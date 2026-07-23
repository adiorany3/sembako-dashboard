"""
Multi-agent market analysis system.
8 specialized agents + orchestrator + output validator.
"""
import json, time, uuid, re
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


# ─── Result dataclasses ───────────────────────────────────────────────────────

@dataclass
class AgentResult:
    agent_name: str
    status: str          # 'ok' | 'error' | 'skipped'
    output: dict
    confidence: int       # 0-100
    data_used: list
    provider_used: str
    model_used: str
    latency_ms: int
    errors: list


@dataclass
class AnalysisResult:
    analysis_id: str
    created_at: str
    data_snapshot_id: str
    mode: str
    agent_results: dict
    final_result: dict
    data_quality_score: float
    confidence_score: int
    duration_ms: int
    status: str          # 'complete' | 'partial' | 'error'
    errors: list
    providers_used: list


# ─── Output Validator ────────────────────────────────────────────────────────

class OutputValidator:
    def validate(self, agent_name: str, output: dict) -> tuple:
        issues = []
        if agent_name == 'ScenarioPlanner':
            if 'scenarios' in output:
                total = sum(s.get('probability_pct', 0) for s in output['scenarios'])
                if abs(total - 100) > 1:
                    issues.append(f"Probabilitas skenario={total}%, dinormalisasi ke 100%")
                    factor = 100 / total if total > 0 else 1
                    for s in output['scenarios']:
                        s['probability_pct'] = round(s.get('probability_pct', 0) * factor)
        if agent_name == 'Synthesizer':
            if 'overall_confidence' in output:
                c = output['overall_confidence']
                if not (0 <= c <= 100):
                    issues.append(f"Confidence={c} di luar 0-100")
                    output['overall_confidence'] = max(0, min(100, c))
        if agent_name == 'RiskAnalyst':
            if 'risk_level' in output:
                if output['risk_level'] not in ('low', 'medium', 'high', 'critical'):
                    issues.append(f"risk_level tidak valid: {output['risk_level']}")
        if agent_name == 'StrategyAdvisor':
            for s in output.get('strategies', []):
                if s.get('recommendation') and not s.get('reasoning'):
                    issues.append(f"Saran tanpa reasoning: {s.get('recommendation', '')[:50]}")
        return len(issues) == 0, issues


# ─── Base Agent ──────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    def __init__(self, name: str, provider_manager, model: str = None):
        self.name = name
        self.pm = provider_manager
        self.model = model
        self.validator = OutputValidator()

    def run(self, context: dict, timeout: int = 60) -> AgentResult:
        t0 = time.time()
        try:
            prompt = self._build_prompt(context)
            resp = self._call_llm(prompt, timeout=timeout)
            output = self._parse_response(resp)
            ok, issues = self.validator.validate(self.name, output)
            if issues:
                output['_warnings'] = issues
            data_used = context.get('datasets_used', [])
            return AgentResult(
                agent_name=self.name, status='ok', output=output,
                confidence=output.get('_confidence', 75),
                data_used=data_used,
                provider_used=resp.get('provider', 'unknown'),
                model_used=resp.get('model', self.model),
                latency_ms=int((time.time() - t0) * 1000),
                errors=issues
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name, status='error', output={},
                confidence=0, data_used=[], provider_used='none',
                model_used=self.model,
                latency_ms=int((time.time() - t0) * 1000),
                errors=[str(e)]
            )

    def _call_llm(self, prompt: str, timeout: int = 60) -> dict:
        messages = [{'role': 'user', 'content': prompt}]
        return self.pm.complete_with_fallback(messages, timeout=timeout)

    def _parse_response(self, resp: dict) -> dict:
        content = resp.get('content', '')
        if not content:
            return {'text': 'Respons kosong dari provider', '_confidence': 0}
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return {'text': content, '_confidence': 40}

    @abstractmethod
    def _build_prompt(self, context: dict) -> str:
        pass


# ─── Data Quality Agent (no LLM) ─────────────────────────────────────────────

class DataQualityAgent(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('DataQuality', provider_manager)

    def _build_prompt(self, context: dict) -> str:  # noqa: D401
        return ''  # rule-based, no LLM needed

    def run(self, context: dict, timeout: int = 10) -> AgentResult:
        t0 = time.time()
        datasets = context.get('datasets', {})
        per_dataset = {}
        total_score = 0
        count = 0
        for name, ds in datasets.items():
            info = ds.get('info', {})
            status = info.get('status', 'UNAVAILABLE')
            rows = info.get('row_count', 0)
            null_pct = info.get('null_pct', 100)
            freshness = info.get('freshness_hours', 999)
            issues = []
            if status == 'UNAVAILABLE':
                issues.append('File/sheet tidak ditemukan')
            if status == 'INVALID':
                issues.append('Data tidak valid atau kosong')
            if status == 'STALE':
                issues.append(f'Data staleness {freshness:.0f}h')
            if null_pct > 50:
                issues.append(f'Null fields {null_pct:.0f}%')
            score_map = {'VALID': 100, 'PARTIAL': 70, 'STALE': 40, 'INVALID': 10, 'UNAVAILABLE': 0}
            score = score_map.get(status, 0)
            per_dataset[name] = {
                'status': status, 'issues': issues, 'score': score,
                'rows': rows, 'null_pct': null_pct, 'freshness_h': freshness
            }
            total_score += score
            count += 1
        overall = total_score / count if count else 0
        health = 'good' if overall >= 70 else 'fair' if overall >= 40 else 'poor'
        return AgentResult(
            agent_name=self.name, status='ok', output={
                'quality_score': round(overall, 1),
                'datasets': per_dataset,
                'overall_health': health,
                'recommendations': ['Perbarui data staleness > 48h'] if any(
                    d.get('freshness_h', 0) > 48 for d in per_dataset.values()
                ) else ['Semua dataset dalam kondisi baik']
            }, confidence=int(overall), data_used=list(datasets.keys()),
            provider_used='local', model_used='rule-based',
            latency_ms=int((time.time() - t0) * 1000), errors=[]
        )


# ─── Market Analyst ───────────────────────────────────────────────────────────

class MarketAnalyst(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('MarketAnalyst', provider_manager, 'groq/llama-3.1-8b-instant')

    def _build_prompt(self, context: dict) -> str:
        data = context.get('formatted_data', 'Tidak ada data.')
        return f"""# Analisis Pasar — Market Analyst Agent

## Data Pasar Saat Ini
{data}

## Tugas
Analisis kondisi pasar berdasarkan data di atas. Output dalam JSON:
{{
  "market_condition": "bullish| bearish| neutral| mixed",
  "indicators": [
    {{"name": "Nama Indikator", "value": "nilai", "change": "perubahan %", "signal": "buy| sell| hold"}}
  ],
  "short_term_outlook": "ringkasan outlook 1-4 minggu",
  "momentum_score": 0-100
}}

- Referensi data yang sebenarnya ada di dataset
- Jangan buat angka yang tidak ada di data"""


# ─── Macro Economist ──────────────────────────────────────────────────────────

class MacroEconomist(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('MacroEconomist', provider_manager, 'groq/llama-3.1-70b-versatile')

    def _build_prompt(self, context: dict) -> str:
        data = context.get('formatted_data', 'Tidak ada data.')
        return f"""# Analisis Ekonomi Makro — Macro Economist Agent

## Data Ekonomi
{data}

## Tugas
Analisis kondisi ekonomi makro Indonesia. Output JSON:
{{
  "economic_condition": "kuat| moderat| lemah",
  "indicators": [
    {{"name": "Nama", "value": "nilai", "assessment": "positif| negatif| netral"}}
  ],
  "inflation_outlook": "ringkasan inflasi",
  "monetary_policy_signal": "hawkish| dovish| neutral"
}}

- Gunakan hanya data yang tersedia di dataset
- Jangan asumsikan data yang tidak ada"""


# ─── Correlation Analyst ──────────────────────────────────────────────────────

class CorrelationAnalyst(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('CorrelationAnalyst', provider_manager, 'groq/llama-3.1-8b-instant')

    def _build_prompt(self, context: dict) -> str:
        data = context.get('formatted_data', 'Tidak ada data.')
        return f"""# Analisis Korelasi — Correlation Analyst Agent

## Data
{data}

## PERINGATAN KRUSIAL
JANGAN menyatakan korelasi = sebab-akibat.
Jika A dan B bergerak bersamaan, itu KORELASI, bukan bukti sebab-akibat.

## Tugas
Analisis pola korelasi antar-indikator pasar. Output JSON:
{{
  "correlations": [
    {{"pair": "A vs B", "correlation": "positif| negatif| netral", "strength": "kuat| sedang| lemah", "note": "keterangan"}}
  ],
  "patterns": ["penjelasan pola"],
  "disclaimer": "KORELASI BUKAN SEBAB-AKIBAT"
}}"""


# ─── Risk Analyst ─────────────────────────────────────────────────────────────

class RiskAnalyst(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('RiskAnalyst', provider_manager, 'groq/llama-3.1-8b-instant')

    def _build_prompt(self, context: dict) -> str:
        data = context.get('formatted_data', 'Tidak ada data.')
        return f"""# Analisis Risiko — Risk Analyst Agent

## Data
{data}

## Tugas
Identifikasi risiko pasar. Output JSON:
{{
  "risk_level": "low| medium| high| critical",
  "risks": [
    {{"name": "Nama Risiko", "severity": "rendah| sedang| tinggi", "description": "deskripsi", "mitigation": "cara mitigasi"}}
  ],
  "warning_signs": ["tanda peringatan"],
  "volatility_index": 0-100
}}"""


# ─── Scenario Planner ─────────────────────────────────────────────────────────

class ScenarioPlanner(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('ScenarioPlanner', provider_manager, 'groq/llama-3.1-70b-versatile')

    def _build_prompt(self, context: dict) -> str:
        data = context.get('formatted_data', 'Tidak ada data.')
        agents = context.get('agent_results', {})
        market = agents.get('MarketAnalyst', {}).get('output', {})
        risk = agents.get('RiskAnalyst', {}).get('output', {})
        return f"""# Perencana Skenario — Scenario Planner Agent

## Data & Analisis Agent Lain
{data}

Market condition: {market.get('market_condition', '-')}
Risk level: {risk.get('risk_level', '-')}

## Tugas
Buat 3 skenario. PROBABILITAS WAJIB JUMLAH = 100%.

Output JSON:
{{
  "scenarios": [
    {{"name": "positif", "description": "deskripsi", "probability_pct": 30, "triggers": ["trigger1"], "impact": "dampak"}},
    {{"name": "dasar", "description": "deskripsi", "probability_pct": 50, "triggers": ["trigger1"], "impact": "dampak"}},
    {{"name": "negatif", "description": "deskripsi", "probability_pct": 20, "triggers": ["trigger1"], "impact": "dampak"}}
  ]
}}

- Jika jumlah ≠ 100%, akan dinormalisasi otomatis
- Gunakan data aktual untuk mendukung setiap skenario"""


# ─── Strategy Advisor ─────────────────────────────────────────────────────────

class StrategyAdvisor(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('StrategyAdvisor', provider_manager, 'groq/llama-3.1-70b-versatile')

    def _build_prompt(self, context: dict) -> str:
        agents = context.get('agent_results', {})
        scenarios = agents.get('ScenarioPlanner', {}).get('output', {}).get('scenarios', [])
        risk = agents.get('RiskAnalyst', {}).get('output', {})
        data = context.get('formatted_data', 'Tidak ada data.')
        return f"""# Penasihat Strategi — Strategy Advisor Agent

## Data & Analisis
{data}

Risk Level: {risk.get('risk_level', '-')}
Skenario: {[s.get('name') for s in scenarios]}

## Tugas
Berikan strategi investasi untuk 3 horizon waktu.
SETIAP SARAN WAJIB MEMILIKI REASONING DAN RISIKO.

Output JSON:
{{
  "strategies": [
    {{"horizon": "pendek (1-4 minggu)", "recommendation": "saran", "reasoning": "alasan", "risk": "risiko", "target_assets": ["aset1"]}},
    {{"horizon": "menengah (1-6 bulan)", "recommendation": "saran", "reasoning": "alasan", "risk": "risiko", "target_assets": []}},
    {{"horizon": "panjang (6-12 bulan)", "recommendation": "saran", "reasoning": "alasan", "risk": "risiko", "target_assets": []}}
  ]
}}"""


# ─── Synthesizer ──────────────────────────────────────────────────────────────

class Synthesizer(BaseAgent):
    def __init__(self, provider_manager):
        super().__init__('Synthesizer', provider_manager, 'groq/llama-3.1-70b-versatile')

    def _build_prompt(self, context: dict) -> str:
        agents = context.get('agent_results', {})
        quality = agents.get('DataQuality', {}).get('output', {})
        market = agents.get('MarketAnalyst', {}).get('output', {})
        macro = agents.get('MacroEconomist', {}).get('output', {})
        corr = agents.get('CorrelationAnalyst', {}).get('output', {})
        risk = agents.get('RiskAnalyst', {}).get('output', {})
        scenarios = agents.get('ScenarioPlanner', {}).get('output', {})
        strategy = agents.get('StrategyAdvisor', {}).get('output', {})
        data = context.get('formatted_data', '')
        return f"""# Synthesizer — Ringkasan Analisis Multi-Agent

## Data Sources
{data}

## Hasil Agent
- Quality Score: {quality.get('quality_score', '-')}/100
- Market Condition: {market.get('market_condition', '-')}
- Momentum: {market.get('momentum_score', '-')}
- Economic Condition: {macro.get('economic_condition', '-')}
- Monetary Policy: {macro.get('monetary_policy_signal', '-')}
- Risk Level: {risk.get('risk_level', '-')}
- Skenario: {', '.join(s.get('name', '?') + ':' + str(s.get('probability_pct', '?')) + '%' for s in scenarios.get('scenarios', []))}
- Strategi pendek: {strategy.get('strategies', [{}])[0].get('recommendation', '-') if strategy.get('strategies') else '-'}

## Tugas
Gabungkan semua hasil agent menjadi analisis terpadu. TIDAK BOLEH membuat fakta baru.
Jika ada konflik antar-agent, catat.

Output JSON:
{{
  "executive_summary": "ringkasan 2-3 kalimat",
  "key_insights": [
    {{
      "title": "Insight 1",
      "conclusion": "kesimpulan",
      "supporting_data": "data pendukung",
      "period": "periode data",
      "impact": "dampak",
      "confidence": 0-100,
      "cancellation_factors": ["faktor pembatal"]
    }}
  ],
  "risks_summary": "ringkasan risiko",
  "opportunities_summary": "ringkasan peluang",
  "scenarios_summary": "ringkasan skenario",
  "recommendations_summary": "ringkasan rekomendasi",
  "conflicts": [
    {{"agents": ["AgentA", "AgentB"], "description": "konflik"}}
  ],
  "overall_confidence": 0-100
}}"""


# ─── Agent Orchestrator ───────────────────────────────────────────────────────

class AgentOrchestrator:
    from datetime import datetime

    MODES = {
        'quick': ['DataQuality', 'MarketAnalyst', 'RiskAnalyst', 'Synthesizer'],
        'full':  ['DataQuality', 'MarketAnalyst', 'MacroEconomist',
                  'CorrelationAnalyst', 'RiskAnalyst', 'ScenarioPlanner',
                  'StrategyAdvisor', 'Synthesizer'],
        'macro': ['DataQuality', 'MacroEconomist', 'CorrelationAnalyst',
                  'RiskAnalyst', 'ScenarioPlanner', 'Synthesizer'],
        'risk':  ['DataQuality', 'CorrelationAnalyst', 'RiskAnalyst',
                   'ScenarioPlanner', 'Synthesizer'],
    }

    def __init__(self, provider_manager):
        self.pm = provider_manager
        self.agents = {
            'DataQuality': DataQualityAgent(provider_manager),
            'MarketAnalyst': MarketAnalyst(provider_manager),
            'MacroEconomist': MacroEconomist(provider_manager),
            'CorrelationAnalyst': CorrelationAnalyst(provider_manager),
            'RiskAnalyst': RiskAnalyst(provider_manager),
            'ScenarioPlanner': ScenarioPlanner(provider_manager),
            'StrategyAdvisor': StrategyAdvisor(provider_manager),
            'Synthesizer': Synthesizer(provider_manager),
        }

    def run_analysis(self, snapshot: dict, mode: str = 'full',
                     formatted_data: str = '', timeout: int = 60) -> dict:
        from datetime import datetime
        t0 = time.time()
        analysis_id = str(uuid.uuid4())[:8]
        agent_names = self.MODES.get(mode, self.MODES['full'])
        agent_results = {}
        errors = []
        providers_used = set()
        quality_score = 0.0

        for name in agent_names:
            agent = self.agents[name]
            ctx = {
                'datasets': snapshot.get('datasets', {}),
                'formatted_data': formatted_data,
                'agent_results': agent_results,
            }
            result = agent.run(ctx, timeout=timeout)
            agent_results[name] = asdict(result)
            if result.provider_used and result.provider_used != 'local':
                providers_used.add(result.provider_used)
            if result.errors:
                errors.append(f'{name}: {"; ".join(result.errors)}')
            if name == 'DataQuality':
                quality_score = result.output.get('quality_score', 0)
            print(f'[AGENT] {name} status={result.status} provider={result.provider_used} latency={result.latency_ms}ms')

        final = agent_results.get('Synthesizer', {}).get('output', {})
        confidence = final.get('overall_confidence',
                               sum(a.get('confidence', 0) for a in agent_results.values()) // max(len(agent_results), 1))

        status = 'complete' if not errors else 'partial' if agent_results else 'error'
        return {
            'analysis_id': analysis_id,
            'created_at': datetime.now().isoformat(),
            'data_snapshot_id': snapshot.get('snapshot_id', ''),
            'mode': mode,
            'agent_results': agent_results,
            'final_result': final,
            'data_quality_score': quality_score,
            'confidence_score': confidence,
            'duration_ms': int((time.time() - t0) * 1000),
            'status': status,
            'errors': errors,
            'providers_used': list(providers_used)
        }
