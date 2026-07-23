"""
AI Provider System — OpenAI-compatible adapter with 9Router support.

Architecture:
  AI_ROUTER_* env vars → OpenAIAdapter → 9Router (OpenAI-compatible)
  Each of 9 routers has独立 status tracking, circuit breaker, cooldown.

Error codes: AI_CONFIG_MISSING, AI_AUTH_FAILED, AI_CONNECTION_FAILED,
  AI_TIMEOUT, AI_RATE_LIMITED, AI_MODEL_NOT_FOUND, AI_INVALID_RESPONSE,
  AI_ALL_ROUTERS_FAILED, AI_PROVIDER_INTERNAL_ERROR, AI_SERVICE_INTERNAL_ERROR
"""
import os
import time
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    requests = None  # graceful fallback if missing

logger = logging.getLogger("AIProvider")


# ─── Error Codes ─────────────────────────────────────────────────────────────
class AIErrorCode(str, Enum):
    CONFIG_MISSING = "AI_CONFIG_MISSING"
    AUTH_FAILED = "AI_AUTH_FAILED"
    CONNECTION_FAILED = "AI_CONNECTION_FAILED"
    TIMEOUT = "AI_TIMEOUT"
    RATE_LIMITED = "AI_RATE_LIMITED"
    MODEL_NOT_FOUND = "AI_MODEL_NOT_FOUND"
    INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    ALL_ROUTERS_FAILED = "AI_ALL_ROUTERS_FAILED"
    PROVIDER_INTERNAL_ERROR = "AI_PROVIDER_INTERNAL_ERROR"
    SERVICE_INTERNAL_ERROR = "AI_SERVICE_INTERNAL_ERROR"


class RouterStatus(str, Enum):
    CHECKING = "CHECKING"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    AUTH_ERROR = "AUTH_ERROR"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


# ─── Error Normalization ─────────────────────────────────────────────────────
def normalize_error(exc: Exception, context: str = "") -> Dict[str, Any]:
    """Map exceptions to structured error with code + message."""
    msg = str(exc)
    lower = msg.lower()

    if isinstance(exc, (ValueError, KeyError)):
        code = AIErrorCode.CONFIG_MISSING if "not set" in lower or "missing" in lower else AIErrorCode.INVALID_RESPONSE
    elif "401" in lower or "403" in lower or "unauthorized" in lower or "forbidden" in lower:
        code = AIErrorCode.AUTH_FAILED
    elif "429" in lower or "rate" in lower:
        code = AIErrorCode.RATE_LIMITED
    elif "404" in lower or "not found" in lower or "model" in lower:
        code = AIErrorCode.MODEL_NOT_FOUND
    elif isinstance(exc, TimeoutError) or "timeout" in lower:
        code = AIErrorCode.TIMEOUT
    elif isinstance(exc, (ConnectionError, OSError)) or "connection" in lower or "connect" in lower:
        code = AIErrorCode.CONNECTION_FAILED
    elif "500" in lower or "502" in lower or "503" in lower:
        code = AIErrorCode.PROVIDER_INTERNAL_ERROR
    else:
        code = AIErrorCode.SERVICE_INTERNAL_ERROR

    # Sanitize: remove key fragments
    sanitized = msg
    for fragment in ["sk-", "Bearer ", "Authorization"]:
        idx = sanitized.lower().find(fragment.lower())
        if idx >= 0:
            sanitized = sanitized[:idx] + "[REDACTED]"
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."

    return {
        "code": code.value,
        "message": sanitized,
        "context": context,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── Router State ────────────────────────────────────────────────────────────
@dataclass
class RouterState:
    router_id: str
    model_id: str
    status: str = "DISABLED"
    latency_ms: float = 0
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    consecutive_failures: int = 0
    error_code: Optional[str] = None
    sanitized_error_message: Optional[str] = None
    _cooldown_until: float = field(default=0, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "router_id": self.router_id,
            "model_id": self.model_id,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 1),
            "last_checked_at": self.last_checked_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "consecutive_failures": self.consecutive_failures,
            "error_code": self.error_code,
            "sanitized_error_message": self.sanitized_error_message,
        }

    def mark_success(self):
        now = datetime.utcnow().isoformat()
        self.status = RouterStatus.HEALTHY.value
        self.last_success_at = now
        self.last_checked_at = now
        self.consecutive_failures = 0
        self.error_code = None
        self.sanitized_error_message = None
        self._cooldown_until = 0

    def mark_failure(self, error_info: Dict[str, Any], latency_ms: float = 0):
        now = datetime.utcnow().isoformat()
        self.last_failure_at = now
        self.last_checked_at = now
        self.latency_ms = latency_ms
        self.consecutive_failures += 1
        self.error_code = error_info.get("code")
        self.sanitized_error_message = error_info.get("message", "")

        code = error_info.get("code", "")
        if code == AIErrorCode.RATE_LIMITED.value:
            self.status = RouterStatus.RATE_LIMITED.value
        elif code == AIErrorCode.TIMEOUT.value:
            self.status = RouterStatus.TIMEOUT.value
        elif code == AIErrorCode.AUTH_FAILED.value:
            self.status = RouterStatus.AUTH_ERROR.value
        elif code == AIErrorCode.INVALID_RESPONSE.value:
            self.status = RouterStatus.INVALID_RESPONSE.value
        else:
            self.status = RouterStatus.UNAVAILABLE.value

        # Circuit breaker: 3 consecutive failures → cooldown
        if self.consecutive_failures >= 3:
            self._cooldown_until = time.time() + 60  # 60s cooldown

    def is_cooling_down(self) -> bool:
        if self._cooldown_until and time.time() < self._cooldown_until:
            return True
        if self._cooldown_until and time.time() >= self._cooldown_until:
            self._cooldown_until = 0
            self.status = RouterStatus.DEGRADED.value
            self.consecutive_failures = 0
        return False

    def is_usable(self) -> bool:
        return self.status in (
            RouterStatus.HEALTHY.value,
            RouterStatus.DEGRADED.value,
            RouterStatus.CHECKING.value,
        ) and not self.is_cooling_down()


# ─── OpenAI-Compatible Adapter ───────────────────────────────────────────────
class OpenAIAdapter:
    """HTTP adapter for OpenAI-compatible endpoints."""

    def __init__(self, base_url: str, api_key: str, timeout_ms: int = 60000,
                 health_timeout_ms: int = 10000):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_ms / 1000
        self.health_timeout_s = health_timeout_ms / 1000
        if not requests:
            raise RuntimeError("requests library not installed")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def list_models(self, timeout: float = None) -> List[str]:
        """Try to list models. Not all providers support this."""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers=self._headers(),
                timeout=timeout or self.health_timeout_s,
            )
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("id", "") for m in data.get("data", [])]
            return []
        except Exception:
            return []

    def health_check(self, model_id: str) -> Dict[str, Any]:
        """
        Completion-based health check. Does NOT depend on /models.
        Sends a minimal completion request with max_tokens=1.
        """
        t0 = time.time()
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                    "temperature": 0,
                    "stream": False,  # 9Router requires non-streaming
                },
                timeout=self.health_timeout_s,
            )
            latency = (time.time() - t0) * 1000

            if resp.status_code in (401, 403):
                return {"ok": False, "error_code": AIErrorCode.AUTH_FAILED.value,
                        "message": f"HTTP {resp.status_code}", "latency_ms": latency}
            if resp.status_code == 429:
                return {"ok": False, "error_code": AIErrorCode.RATE_LIMITED.value,
                        "message": "Rate limited", "latency_ms": latency}
            if resp.status_code == 404:
                return {"ok": False, "error_code": AIErrorCode.MODEL_NOT_FOUND.value,
                        "message": f"Model {model_id} not found", "latency_ms": latency}
            if resp.status_code >= 500:
                return {"ok": False, "error_code": AIErrorCode.PROVIDER_INTERNAL_ERROR.value,
                        "message": f"HTTP {resp.status_code}", "latency_ms": latency}

            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return {"ok": True, "latency_ms": latency, "model": model_id}
                return {"ok": False, "error_code": AIErrorCode.INVALID_RESPONSE.value,
                        "message": "Response missing choices", "latency_ms": latency}

            return {"ok": False, "error_code": AIErrorCode.SERVICE_INTERNAL_ERROR.value,
                    "message": f"HTTP {resp.status_code}", "latency_ms": latency}

        except requests.exceptions.Timeout:
            return {"ok": False, "error_code": AIErrorCode.TIMEOUT.value,
                    "message": f"Health check timeout ({self.health_timeout_s}s)"}
        except requests.exceptions.ConnectionError as e:
            return {"ok": False, "error_code": AIErrorCode.CONNECTION_FAILED.value,
                    "message": normalize_error(e)["message"]}
        except Exception as e:
            return {"ok": False, "error_code": AIErrorCode.SERVICE_INTERNAL_ERROR.value,
                    "message": normalize_error(e)["message"]}

    def chat_completion(self, messages: List[Dict[str, str]], model_id: str,
                        temperature: float = 0.3, max_tokens: int = 4096,
                        timeout: float = None) -> Dict[str, Any]:
        """Send chat completion. Returns structured result."""
        t0 = time.time()
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,  # 9Router requires non-streaming
                },
                timeout=timeout or self.timeout_s,
            )
            latency = (time.time() - t0) * 1000

            if resp.status_code in (401, 403):
                raise ConnectionError(f"Auth failed: HTTP {resp.status_code}")
            if resp.status_code == 429:
                raise ConnectionError("Rate limited")
            if resp.status_code == 404:
                raise ValueError(f"Model not found: {model_id}")

            resp.raise_for_status()
            data = resp.json()

            if "choices" not in data or not data["choices"]:
                raise ValueError("Invalid response: no choices")

            content = data["choices"][0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            return {
                "content": content,
                "model": model_id,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                },
                "latency_ms": latency,
            }

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timeout ({timeout or self.timeout_s}s)")
        except (ConnectionError, ValueError, TimeoutError):
            raise
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Connection failed: {normalize_error(e)['message']}")
        except Exception as e:
            raise RuntimeError(normalize_error(e)["message"])


# ─── 9Router System ──────────────────────────────────────────────────────────
# Default router configurations — VERIFIED models working at 9Router endpoint
# Verified 2026-07-21: sum/MiniMax-M2.7-highspeed, groq/llama-3.1-8b-instant,
# groq/llama-3.3-70b-versatile, groq/openai/gpt-oss-120b, Indo/gemma4-26b
DEFAULT_ROUTER_CONFIGS = [
    {"router_id": "r1", "model_id": "sum/MiniMax-M2.7-highspeed", "label": "MiniMax M2.7 HS"},
    {"router_id": "r2", "model_id": "groq/llama-3.3-70b-versatile", "label": "Llama 3.3 70B"},
    {"router_id": "r3", "model_id": "groq/openai/gpt-oss-120b", "label": "GPT-OSS 120B"},
    {"router_id": "r4", "model_id": "Indo/gemma4-26b", "label": "Gemma4 26B"},
    {"router_id": "r5", "model_id": "groq/llama-3.1-8b-instant", "label": "Llama 3.1 8B"},
]

# Mode → preferred router order
MODE_ROUTER_PREFERENCE = {
    "quick": ["r1", "r2", "r3", "r4", "r5"],
    "full": ["r1", "r2", "r3", "r4", "r5"],
    "macro": ["r1", "r2", "r3", "r4", "r5"],
    "risk": ["r1", "r2", "r3", "r4", "r5"],
}

MAX_RETRIES = 2  # per-router retries before fallback
BASE_BACKOFF = 2  # seconds


class NineRouterManager:
    """
    Manages 9 routers through a single OpenAI-compatible endpoint.
    Handles health checks, selection, fallback, circuit breaker.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._adapter: Optional[OpenAIAdapter] = None
        self._routers: Dict[str, RouterState] = {}
        self._initialized = False
        self._init_error: Optional[str] = None

    def initialize(self) -> bool:
        """Initialize from environment variables. Returns True if configured."""
        base_url = os.environ.get("AI_ROUTER_BASE_URL", "http://127.0.0.1:20128/v1").strip()
        api_key = os.environ.get("AI_ROUTER_API_KEY", "").strip()
        timeout_ms = int(os.environ.get("AI_ROUTER_TIMEOUT_MS", "60000"))
        health_timeout_ms = int(os.environ.get("AI_ROUTER_HEALTH_TIMEOUT_MS", "10000"))

        # Fallback: try to read 9Router key from its SQLite DB
        if not api_key:
            try:
                import sqlite3
                db_path = "/root/.9router/db/data.sqlite"
                if os.path.exists(db_path):
                    db = sqlite3.connect(db_path)
                    cur = db.cursor()
                    cur.execute("SELECT key FROM apiKeys WHERE name = 'hermes' AND isActive = 1")
                    row = cur.fetchone()
                    if row:
                        api_key = row[0]
                        logger.info("Read 9Router API key from SQLite DB")
                    db.close()
            except Exception as e:
                logger.warning(f"Could not read 9Router key from DB: {e}")

        if not api_key:
            self._init_error = "AI_ROUTER_API_KEY not configured"
            logger.error(self._init_error)
            return False

        try:
            self._adapter = OpenAIAdapter(
                base_url=base_url,
                api_key=api_key,
                timeout_ms=timeout_ms,
                health_timeout_ms=health_timeout_ms,
            )
        except Exception as e:
            self._init_error = f"Adapter init failed: {e}"
            logger.error(self._init_error)
            return False

        # Initialize router states
        self._routers = {}
        for cfg in DEFAULT_ROUTER_CONFIGS:
            state = RouterState(
                router_id=cfg["router_id"],
                model_id=cfg["model_id"],
                status=RouterStatus.CHECKING.value,
            )
            self._routers[cfg["router_id"]] = state

        self._initialized = True
        logger.info(f"9Router initialized: {base_url} with {len(self._routers)} routers")
        return True

    @property
    def is_configured(self) -> bool:
        return self._initialized and self._adapter is not None

    def get_status_summary(self) -> Dict[str, Any]:
        """Return status for provider-status endpoint."""
        if not self.is_configured:
            return {
                "available": False,
                "error": self._init_error or "Not configured",
                "routers": {},
                "healthy_count": 0,
                "total_count": len(DEFAULT_ROUTER_CONFIGS),
                "config": {
                    "base_url": os.environ.get("AI_ROUTER_BASE_URL", "(default groq)"),
                    "provider": os.environ.get("AI_ROUTER_PROVIDER", "9router"),
                    "has_api_key": bool(os.environ.get("AI_ROUTER_API_KEY") or os.environ.get("GROQ_API_KEY")),
                },
            }

        routers = {r.router_id: r.to_dict() for r in self._routers.values()}
        healthy = [r for r in self._routers.values() if r.status == RouterStatus.HEALTHY.value]
        active = [r for r in self._routers.values() if r.is_usable()]

        active_router = None
        if healthy:
            active_router = min(healthy, key=lambda r: r.latency_ms or 999999)

        return {
            "available": len(healthy) > 0,
            "healthy_count": len(healthy),
            "usable_count": len(active),
            "total_count": len(self._routers),
            "active_router": active_router.router_id if active_router else None,
            "active_model": active_router.model_id if active_router else None,
            "routers": routers,
            "error": None if len(healthy) > 0 else "Tidak ada router sehat",
        }

    def health_check_all(self) -> Dict[str, Any]:
        """Check health of all routers (threaded for speed)."""
        if not self.is_configured:
            return self.get_status_summary()

        def check_router(router_state: RouterState):
            with self._lock:
                router_state.status = RouterStatus.CHECKING.value

            result = self._adapter.health_check(router_state.model_id)

            with self._lock:
                if result["ok"]:
                    router_state.mark_success()
                    router_state.latency_ms = result.get("latency_ms", 0)
                else:
                    error_info = {"code": result.get("error_code", "UNKNOWN"),
                                  "message": result.get("message", "Unknown")}
                    router_state.mark_failure(error_info, result.get("latency_ms", 0))

        threads = []
        for router_state in self._routers.values():
            t = threading.Thread(target=check_router, args=(router_state,), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=15)
            if t.is_alive():
                logger.warning("Health check thread still running after timeout")

        with self._lock:
            for r in self._routers.values():
                if r.status == RouterStatus.CHECKING.value:
                    r.status = RouterStatus.TIMEOUT.value
                    r.sanitized_error_message = "Health check timeout"

        return self.get_status_summary()

    def select_router(self, mode: str = "quick") -> Optional[RouterState]:
        """Select best available router for given mode."""
        with self._lock:
            preference = MODE_ROUTER_PREFERENCE.get(mode, MODE_ROUTER_PREFERENCE["quick"])

            for router_id in preference:
                state = self._routers.get(router_id)
                if state and state.is_usable():
                    return state

            for state in self._routers.values():
                if not state.is_cooling_down():
                    return state

        return None

    def chat(self, messages: List[Dict[str, str]], mode: str = "quick",
             temperature: float = 0.3, max_tokens: int = 4096,
             timeout: float = None) -> Dict[str, Any]:
        """
        Chat with automatic router selection and fallback.
        Tries preferred router first, then falls back to others.
        """
        if not self.is_configured:
            raise ConnectionError(f"AI not configured: {self._init_error}")

        tried_routers = set()
        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            router = self.select_router(mode)
            if not router:
                break

            if router.router_id in tried_routers and attempt > 0:
                with self._lock:
                    for state in self._routers.values():
                        if state.router_id not in tried_routers and state.is_usable():
                            router = state
                            break
                    else:
                        break

            tried_routers.add(router.router_id)

            try:
                result = self._adapter.chat_completion(
                    messages=messages,
                    model_id=router.model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
                with self._lock:
                    router.mark_success()
                    router.latency_ms = result.get("latency_ms", 0)

                result["router_id"] = router.router_id
                result["provider"] = "9router"
                return result

            except Exception as e:
                last_error = e
                error_info = normalize_error(e, f"router={router.router_id}")
                with self._lock:
                    router.mark_failure(error_info, getattr(e, "latency_ms", 0))

                logger.warning(
                    f"Router {router.router_id} ({router.model_id}) failed: "
                    f"{error_info['code']} — attempt {attempt + 1}/{MAX_RETRIES + 1}"
                )

                if attempt < MAX_RETRIES:
                    time.sleep(BASE_BACKOFF * (2 ** attempt))

        error_info = normalize_error(
            last_error or RuntimeError("No routers available"),
            context=f"tried={list(tried_routers)}"
        )
        raise ConnectionError(
            f"{AIErrorCode.ALL_ROUTERS_FAILED.value}: "
            f"{error_info['message']} (tried: {', '.join(tried_routers)})"
        )

    def get_adapter(self) -> Optional[OpenAIAdapter]:
        return self._adapter


# ─── ProviderManager — Unified Interface ─────────────────────────────────────
class ProviderUsage:
    def __init__(self, **kw):
        self.timestamp = time.time()
        self.provider = kw.get("provider", "")
        self.model = kw.get("model", "")
        self.tokens_in = kw.get("tokens_in", 0)
        self.tokens_out = kw.get("tokens_out", 0)
        self.latency_ms = kw.get("latency_ms", 0)
        self.mode = kw.get("mode", "auto")
        self.success = kw.get("success", True)


class ProviderManager:
    """
    Unified provider interface. Wraps NineRouterManager for backward compat.
    Code that used AI_MANAGER.chat(...) or AI_MANAGER.health_check_all()
    continues to work.
    """

    def __init__(self):
        self._router_manager = NineRouterManager()
        self.provider_stats: Dict[str, Any] = {}
        self._call_timestamps: Dict[str, list] = {}
        self.providers: Dict[str, Any] = {}  # legacy compat

    def initialize(self) -> bool:
        ok = self._router_manager.initialize()
        if ok:
            self.providers["9router"] = self
        else:
            groq_key = os.environ.get("GROQ_API_KEY", "")
            if groq_key:
                self.providers["groq"] = self
                logger.info("Falling back to legacy Groq provider")
                return True
        return ok

    def get_status(self) -> Dict[str, Any]:
        return self._router_manager.get_status_summary()

    def health_check_all(self) -> Dict[str, Any]:
        return self._router_manager.health_check_all()

    def chat(self, messages, mode="quick", temperature=0.3, max_tokens=4096,
             timeout=60, **kw) -> Dict[str, Any]:
        return self._router_manager.chat(
            messages=messages, mode=mode, temperature=temperature,
            max_tokens=max_tokens, timeout=timeout,
        )

    def complete_with_fallback(self, messages, timeout=60, **kw) -> Dict[str, Any]:
        """Alias used by agents.py BaseAgent."""
        return self.chat(messages=messages, timeout=timeout, **kw)

    def is_available(self) -> bool:
        return self._router_manager.is_configured


# ─── Global Instance ─────────────────────────────────────────────────────────
_manager = None


def get_provider_manager() -> ProviderManager:
    global _manager
    if _manager is None:
        _manager = ProviderManager()
        _manager.initialize()
    return _manager


# Legacy alias
AI_MANAGER = None


def _init_global():
    global AI_MANAGER
    mgr = get_provider_manager()
    AI_MANAGER = mgr


try:
    _init_global()
except Exception as e:
    logger.critical(f"FATAL: Failed to init AI system: {e}")
    AI_MANAGER = None


# ─── Self-test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mgr = get_provider_manager()
    print(f"Configured: {mgr._router_manager.is_configured}")
    if mgr._router_manager.is_configured:
        print("Running health checks...")
        status = mgr.health_check_all()
        healthy = status.get("healthy_count", 0)
        total = status.get("total_count", 0)
        print(f"Healthy: {healthy}/{total}")
        for rid, info in status.get("routers", {}).items():
            print(f"  {rid}: {info['status']} ({info['model']}) {info.get('latency_ms', 0):.0f}ms")
    else:
        print(f"Error: {mgr._router_manager._init_error}")
