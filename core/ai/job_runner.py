"""
Background job runner for AI analysis.
Handles agent execution, retry, heartbeat, watchdog, provider fallback.
Uses ONLY Python stdlib.
"""
import threading
import hashlib
import json
import time
import uuid
import traceback
from datetime import datetime

from core.ai.analysis_store import get_store

# Agent execution order
AGENT_ORDER = [
    {"type": "MarketAnalyst", "depends_on": [], "critical": False},
    {"type": "MacroEconomist", "depends_on": [], "critical": False},
    {"type": "RiskAnalyst", "depends_on": [], "critical": False},
    {"type": "ScenarioPlanner", "depends_on": ["MarketAnalyst", "MacroEconomist"], "critical": False},
    {"type": "StrategyAdvisor", "depends_on": ["MarketAnalyst", "RiskAnalyst", "ScenarioPlanner"], "critical": False},
    {"type": "Synthesizer", "depends_on": ["MarketAnalyst", "MacroEconomist", "RiskAnalyst", "ScenarioPlanner", "StrategyAdvisor"], "critical": True},
]

AGENT_SYSTEM_PROMPTS = {
    "MarketAnalyst": (
        "You are a market analyst. Analyze provided market data (crypto, gold, commodities, "
        "currencies, stocks). Identify key movers, trends, and short-term outlook. "
        "Return JSON with: market_analysis (str), key_movers (list of {name,change,reason}), short_term_outlook (str)."
    ),
    "MacroEconomist": (
        "You are a macro economist. Analyze macroeconomic indicators (BI rate, inflation, GDP, "
        "currency exchange rates, trade balance). Assess monetary policy and economic direction. "
        "Return JSON with: macro_assessment (str), policy_implications (str)."
    ),
    "RiskAnalyst": (
        "You are a risk analyst. Identify risks across all market segments. Create a risk matrix "
        "with severity and likelihood. Suggest mitigations. "
        "Return JSON with: risk_matrix (list of {risk,severity,likelihood}), key_risks (list), mitigation (str)."
    ),
    "ScenarioPlanner": (
        "You are a scenario planner. Based on the provided market and macro analysis, create "
        "three scenarios: best case, base case, worst case. Include probabilities. "
        "Return JSON with: scenarios (object with best, base, worst fields, each a string)."
    ),
    "StrategyAdvisor": (
        "You are a strategy advisor. Based on all prior analysis, provide investment and "
        "business strategy recommendations. Include asset allocation suggestions. "
        "Return JSON with: recommendations (list of {action, rationale, priority}), allocation_suggestion (str)."
    ),
    "Synthesizer": (
        "You are a chief analyst synthesizer. Combine all agent outputs into a coherent final "
        "analysis report in Indonesian. Include executive summary, key findings, risks, and "
        "recommendations. Provide confidence and data quality scores (0-1). "
        "Return JSON with: final_summary (str, the full report), confidence_score (float 0-1), "
        "quality_score (float 0-1). The report should be comprehensive but concise."
    ),
}

AGENT_TASK_PROMPTS = {
    "MarketAnalyst": "Analyze the following market data and provide your assessment:\n\n{formatted_data}",
    "MacroEconomist": "Analyze the following macroeconomic data:\n\n{formatted_data}",
    "RiskAnalyst": "Assess risks based on the following data:\n\n{formatted_data}",
    "ScenarioPlanner": "Create scenarios based on:\n\n{formatted_data}\n\nPrior analysis:\n{prior_outputs}",
    "StrategyAdvisor": "Develop strategy based on:\n\n{formatted_data}\n\nPrior analysis:\n{prior_outputs}",
    "Synthesizer": "Synthesize all agent outputs into a final report:\n\n{formatted_data}\n\nAll agent outputs:\n{prior_outputs}",
}

# Retry config
MAX_ATTEMPTS = 3
RETRY_DELAYS = [2, 4, 8]  # exponential backoff seconds
PROVIDER_TIMEOUT = 60  # seconds per provider call
AGENT_HEARTBEAT_INTERVAL = 10  # seconds
AGENT_STALE_THRESHOLD = 120  # seconds without heartbeat = stuck
JOB_TIMEOUT = 600  # max job duration seconds

_runner = None


def get_runner():
    global _runner
    if _runner is None:
        _runner = JobRunner()
    return _runner


class JobRunner:
    def __init__(self):
        self._active_jobs = {}  # job_id -> threading.Event (for cancellation)
        self._watchdog_thread = None
        self._start_watchdog()

    def _start_watchdog(self):
        def watchdog_loop():
            while True:
                time.sleep(30)
                try:
                    self._watchdog_tick()
                except Exception:
                    pass
        self._watchdog_thread = threading.Thread(target=watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def start_job(self, job_id):
        event = threading.Event()
        self._active_jobs[job_id] = event
        t = threading.Thread(target=self._run_job, args=(job_id, event), daemon=True)
        t.start()

    def cancel_job(self, job_id):
        event = self._active_jobs.get(job_id)
        if event:
            event.set()
        store = get_store()
        store.update_job(job_id, status="CANCELLED", finished_at=datetime.utcnow().isoformat())

    def retry_failed(self, job_id):
        store = get_store()
        agents = store.get_agent_tasks(job_id)
        retried = False
        for a in agents:
            if a["status"] in ("FAILED", "SKIPPED"):
                store.update_agent_task(a["id"], status="PENDING", attempt_count=0,
                                       error_message=None, error_code=None, output=None)
                retried = True
        if retried:
            store.update_job(job_id, status="QUEUED", started_at=None, finished_at=None, duration_ms=0)
            self.start_job(job_id)

    def _run_job(self, job_id, cancel_event):
        store = get_store()
        start_time = time.time()
        try:
            # Phase 1: Collect data
            store.update_job(job_id, status="PREPARING_DATA", started_at=datetime.utcnow().isoformat())
            try:
                from core.ai.data_pipeline import collect_all_data, format_for_agents
                snap = collect_all_data()
                fmt = format_for_agents(snap, "full")
                data_hash = hashlib.sha256(fmt.encode()).hexdigest()[:16]
                store.update_job(job_id, status="VALIDATING_DATA", data_snapshot_hash=data_hash)
            except Exception as e:
                store.update_job(job_id, status="FAILED", error_message=f"Data collection failed: {e}",
                                 finished_at=datetime.utcnow().isoformat())
                return

            if cancel_event.is_set():
                return

            # Phase 2: Create agent tasks
            job = store.get_job(job_id)
            mode = job.get("mode", "full")
            agent_configs = [{"type": a["type"], "depends_on": a["depends_on"], "critical": a["critical"]} for a in AGENT_ORDER]
            store.create_agent_tasks(job_id, agent_configs)

            # Phase 3: Run agents
            store.update_job(job_id, status="RUNNING")
            prior_outputs = {}
            completed_agents = set()
            router_counts = {}  # Track router usage: {router_id: count}

            has_critical_failure = False

            for agent_def in AGENT_ORDER:
                if cancel_event.is_set():
                    return

                agent_type = agent_def["type"]

                # Check timeout
                if time.time() - start_time > JOB_TIMEOUT:
                    store.update_job(job_id, status="FAILED",
                                     error_message=f"Job timeout ({JOB_TIMEOUT}s exceeded)")
                    return

                # Check dependencies
                deps_met = all(d in completed_agents for d in agent_def["depends_on"])
                if not deps_met:
                    # Check if dependency failed
                    deps_failed = any(d not in completed_agents for d in agent_def["depends_on"])
                    if deps_failed and not agent_def["critical"]:
                        # Find the agent task and skip it
                        agents = store.get_agent_tasks(job_id)
                        for a in agents:
                            if a["agent_type"] == agent_type:
                                store.update_agent_task(a["id"], status="SKIPPED",
                                                        current_step="Dependency not met")
                        continue
                    elif deps_failed and agent_def["critical"]:
                        agents = store.get_agent_tasks(job_id)
                        for a in agents:
                            if a["agent_type"] == agent_type:
                                store.update_agent_task(a["id"], status="SKIPPED",
                                                        current_step="Critical dependency failed")
                        has_critical_failure = True
                        continue

                # Find agent task
                agents = store.get_agent_tasks(job_id)
                agent_task = None
                for a in agents:
                    if a["agent_type"] == agent_type:
                        agent_task = a
                        break

                if not agent_task or agent_task["status"] in ("COMPLETED",):
                    if agent_task and agent_task["status"] == "COMPLETED":
                        completed_agents.add(agent_type)
                    continue

                # Run agent
                store.update_job(job_id, progress=self._calc_progress(completed_agents, len(AGENT_ORDER)))
                result, rid = self._run_agent(store, job_id, agent_task, fmt, prior_outputs, cancel_event, mode, router_counts)

                if result is not None:
                    prior_outputs[agent_type] = result
                    completed_agents.add(agent_type)
                    if agent_type == "Synthesizer" and result is None:
                        has_critical_failure = True
                else:
                    if agent_def["critical"]:
                        has_critical_failure = True

                store.update_job(job_id, progress=self._calc_progress(completed_agents, len(AGENT_ORDER)))

            # Phase 4: Finalize
            elapsed_ms = int((time.time() - start_time) * 1000)
            agents_final = store.get_agent_tasks(job_id)
            completed_count = sum(1 for a in agents_final if a["status"] == "COMPLETED")
            total = len(agents_final)

            # Extract scores from synthesizer output
            conf_score = None
            qual_score = None
            summary = ""
            for a in agents_final:
                if a["agent_type"] == "Synthesizer" and a["output"]:
                    try:
                        out = json.loads(a["output"]) if isinstance(a["output"], str) else a["output"]
                        conf_score = out.get("confidence_score")
                        qual_score = out.get("quality_score")
                        summary = out.get("final_summary", "")
                    except (json.JSONDecodeError, TypeError):
                        pass

            if has_critical_failure and completed_count < total:
                final_status = "PARTIAL"
            elif has_critical_failure:
                final_status = "FAILED"
            else:
                final_status = "COMPLETED"

            # Determine most-used router for this job
            router_used = max(router_counts, key=router_counts.get) if router_counts else None
            providers_used = ",".join(router_counts.keys()) if router_counts else None

            store.update_job(job_id,
                             status=final_status,
                             progress=100,
                             duration_ms=elapsed_ms,
                             confidence_score=conf_score,
                             data_quality_score=qual_score,
                             summary=summary[:2000] if summary else None,
                             result=json.dumps(prior_outputs, default=str) if prior_outputs else None,
                             router_used=router_used,
                             providers_used=providers_used,
                             finished_at=datetime.utcnow().isoformat())

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            store.update_job(job_id, status="FAILED",
                             error_message=f"Job error: {e}",
                             duration_ms=elapsed_ms,
                             finished_at=datetime.utcnow().isoformat())
            traceback.print_exc()
        finally:
            self._active_jobs.pop(job_id, None)

    def _run_agent(self, store, job_id, agent_task, formatted_data, prior_outputs, cancel_event, mode="full", router_counts=None):
        task_id = agent_task["id"]
        agent_type = agent_task["agent_type"]
        max_attempts = agent_task.get("max_attempts", MAX_ATTEMPTS)

        system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type, "You are an analyst.")
        task_template = AGENT_TASK_PROMPTS.get(agent_type, "{formatted_data}")

        prior_str = "\n\n".join(f"=== {k} ===\n{v}" for k, v in prior_outputs.items()) if prior_outputs else "No prior analysis available."

        prompt = task_template.replace("{formatted_data}", formatted_data).replace("{prior_outputs}", prior_str)
        input_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        # Check checkpoint cache
        checkpoint = store.get_checkpoint(job_id, task_id, "agent_output")
        if checkpoint and checkpoint.get("input_hash") == input_hash:
            store.update_agent_task(task_id, status="COMPLETED", output=checkpoint["output"],
                                    progress=100, last_heartbeat_at=datetime.utcnow().isoformat())
            try:
                parsed = json.loads(checkpoint["output"]) if isinstance(checkpoint["output"], str) else checkpoint["output"]
            except (json.JSONDecodeError, TypeError):
                parsed = checkpoint["output"]
            return parsed, None  # Cached, no router info

        store.update_agent_task(task_id, status="RUNNING", started_at=datetime.utcnow().isoformat(),
                                current_step="Starting", input_hash=input_hash)

        # Start heartbeat
        heartbeat_stop = threading.Event()

        def heartbeat_loop():
            while not heartbeat_stop.is_set():
                try:
                    store.update_agent_task(task_id, last_heartbeat_at=datetime.utcnow().isoformat())
                except Exception:
                    pass
                heartbeat_stop.wait(AGENT_HEARTBEAT_INTERVAL)

        hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        hb_thread.start()

        last_error = None
        for attempt in range(1, max_attempts + 1):
            if cancel_event.is_set():
                heartbeat_stop.set()
                store.update_agent_task(task_id, status="CANCELLED")
                return None

            delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
            store.update_agent_task(task_id, attempt_count=attempt,
                                    current_step=f"Attempt {attempt}/{max_attempts}")

            # Try provider
            try:
                result_text, rid = self._call_provider(prompt, system_prompt, timeout=PROVIDER_TIMEOUT, mode=mode)
                if result_text:
                    # Track router usage
                    if rid and router_counts is not None:
                        router_counts[rid] = router_counts.get(rid, 0) + 1
                    # Parse JSON output
                    try:
                        # Try to extract JSON from response
                        parsed = self._extract_json(result_text)
                    except Exception:
                        parsed = {"raw_output": result_text}

                    store.update_agent_task(task_id, status="COMPLETED", output=json.dumps(parsed, default=str),
                                            progress=100, current_step="Done",
                                            finished_at=datetime.utcnow().isoformat())

                    # Save checkpoint
                    store.save_checkpoint(job_id, task_id, "agent_output", json.dumps(parsed, default=str), input_hash)

                    heartbeat_stop.set()
                    return parsed, rid
                else:
                    last_error = "Provider returned empty response"
            except Exception as e:
                last_error = str(e)

            store.update_agent_task(task_id, status="RETRYING",
                                    current_step=f"Retry in {delay}s",
                                    error_message=last_error)

            # Wait with cancel check
            for _ in range(int(delay)):
                if cancel_event.is_set():
                    heartbeat_stop.set()
                    store.update_agent_task(task_id, status="CANCELLED")
                    return None, None
                time.sleep(1)

        # All attempts failed
        heartbeat_stop.set()
        store.update_agent_task(task_id, status="FAILED", error_message=last_error,
                                current_step="All attempts failed",
                                finished_at=datetime.utcnow().isoformat())
        return None, None

    def _call_provider(self, prompt, system_prompt, timeout=60, mode="full"):
        """Call AI provider with timeout via 9Router. Returns (text, router_id) or (None, None)."""
        result = [None]
        error = [None]
        router_id_used = [None]

        def do_call():
            try:
                from core.ai.providers import get_provider_manager
                mgr = get_provider_manager()
                if not mgr or not mgr.is_available():
                    error[0] = "AI provider not configured"
                    return
                resp = mgr.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    mode=mode,
                    temperature=0.3,
                    max_tokens=4096,
                    timeout=min(timeout, PROVIDER_TIMEOUT),
                )
                router_id_used[0] = resp.get("router_id") if isinstance(resp, dict) else None
                result[0] = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            except Exception as e:
                error[0] = str(e)

        t = threading.Thread(target=do_call, daemon=True)
        t.start()
        t.join(timeout)

        if t.is_alive():
            return None, None
        if error[0]:
            return None, None
        return result[0], router_id_used[0]

    def _extract_json(self, text):
        """Try to extract JSON from LLM response."""
        # Try direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        # Try to find JSON block in markdown
        import re
        match = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except (json.JSONDecodeError, TypeError):
                pass
        # Try to find { ... } block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except (json.JSONDecodeError, TypeError):
                pass
        return {"raw_output": text}

    def _calc_progress(self, completed, total):
        return round((len(completed) / total) * 100) if total > 0 else 0

    def _watchdog_tick(self):
        """Check for stuck agents and timed-out jobs."""
        store = get_store()
        # Find active jobs
        jobs = store.get_history(limit=10)
        for job in jobs:
            if job["status"] not in ("RUNNING", "QUEUED", "PREPARING_DATA", "VALIDATING_DATA", "RETRYING"):
                continue

            # Check job timeout
            if job.get("started_at"):
                try:
                    started = datetime.fromisoformat(job["started_at"])
                    elapsed = (datetime.utcnow() - started).total_seconds()
                    if elapsed > JOB_TIMEOUT:
                        store.update_job(job["id"], status="FAILED",
                                         error_message=f"Watchdog: job timeout ({elapsed:.0f}s)")
                        self._active_jobs.pop(job["id"], None)
                        continue
                except (ValueError, TypeError):
                    pass

            # Check stuck agents
            agents = store.get_agent_tasks(job["id"])
            for a in agents:
                if a["status"] != "RUNNING":
                    continue
                if a.get("last_heartbeat_at"):
                    try:
                        hb = datetime.fromisoformat(a["last_heartbeat_at"])
                        stale = (datetime.utcnow() - hb).total_seconds()
                        if stale > AGENT_STALE_THRESHOLD:
                            if a["attempt_count"] < a.get("max_attempts", MAX_ATTEMPTS):
                                store.update_agent_task(a["id"], status="RETRYING",
                                                        current_step=f"Watchdog: no heartbeat for {stale:.0f}s")
                            else:
                                store.update_agent_task(a["id"], status="FAILED",
                                                        error_message=f"Watchdog: no heartbeat for {stale:.0f}s",
                                                        finished_at=datetime.utcnow().isoformat())
                    except (ValueError, TypeError):
                        pass
