import json
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from config.api_config import get_anthropic_api_key

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
ALLOWED_SEVERITY = {"low", "medium", "high", "critical"}
ALLOWED_URGENCY = {"low", "medium", "high", "immediate"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_LAYER = {"ingestion", "processing", "network", "storage"}
CLIENT: Optional[Anthropic] = None


def _get_client() -> Anthropic:
    global CLIENT
    if CLIENT is None:
        CLIENT = Anthropic(api_key=get_anthropic_api_key())
    return CLIENT


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _as_list_of_str(value: Any) -> List[str]:
    if isinstance(value, list):
        out = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    return []


def _validated_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    spikes = result.get("spikes", [])
    drops = result.get("drops", [])
    anomalies = result.get("anomalies", [])
    counts = result.get("counts", {}) if isinstance(result.get("counts"), dict) else {}

    return {
        "spikes": _safe_int(counts.get("spikes", len(spikes))),
        "drops": _safe_int(counts.get("drops", len(drops))),
        "anomalies": _safe_int(counts.get("anomalies", len(anomalies))),
        "trend": str(result.get("trend", "stable")).lower(),
        "risk_score": _safe_int(result.get("risk_score", 0)),
        "quality": _safe_int(result.get("quality", 0)),
    }


def _build_prompt(payload: Dict[str, Any]) -> str:
    return (
        "You are a production-grade system intelligence engine embedded inside a data analytics platform.\n"
        "You are NOT a chatbot. Convert system signals into actionable system decisions.\n\n"
        "You must produce technical, data-driven output with no generic statements.\n"
        "STRICT ANALYSIS LOGIC:\n"
        "1) Correlate signals using counts.\n"
        "- If spikes and drops are both high, conclude overload or throttling behavior.\n"
        "- If anomalies are high, conclude instability or unpredictable behavior.\n"
        "- If drops are high, conclude interruption or data loss behavior.\n"
        "2) Root cause must be a SINGLE most likely cause.\n"
        "3) Severity: critical if spikes+drops high, high if anomalies high, medium for moderate instability, low if stable.\n"
        "4) Impact must be technical and definitive (latency, failures, throughput, consistency).\n"
        "5) Recommendations must be specific and implementable.\n"
        "6) Urgency: low | medium | high | immediate.\n"
        "7) Confidence: low | medium | high.\n"
        "8) Choose one primary affected layer: ingestion | processing | network | storage.\n\n"
        "INPUT DATA:\n\n"
        f"Spikes: {payload['spikes']}\n"
        f"Drops: {payload['drops']}\n"
        f"Anomalies: {payload['anomalies']}\n"
        f"Trend: {payload['trend']}\n"
        f"Risk Score: {payload['risk_score']}\n"
        f"Quality: {payload['quality']}\n\n"
        "Return ONLY valid JSON with no markdown and no extra text:\n\n"
        "{\n"
        '  "summary": "technical one-line summary with numbers",\n'
        '  "affected_layer": "ingestion | processing | network | storage",\n'
        '  "root_cause": "single precise cause",\n'
        '  "severity": "low | medium | high | critical",\n'
        '  "impact": "direct system-level impact",\n'
        '  "recommendations": ["specific fix 1", "specific fix 2"],\n'
        '  "urgency": "low | medium | high | immediate",\n'
        '  "confidence": "low | medium | high"\n'
        "}"
    )


def _infer_layer(root_cause: str) -> str:
    text = (root_cause or "").lower()
    if any(token in text for token in ["api", "gateway", "ingest", "input", "throttle", "rate limit"]):
        return "ingestion"
    if any(token in text for token in ["network", "packet", "dns", "latency link"]):
        return "network"
    if any(token in text for token in ["storage", "database", "disk", "io"]):
        return "storage"
    return "processing"


def _system_status_from_severity(severity: str) -> str:
    if severity == "critical":
        return "CRITICAL"
    if severity in {"high", "medium"}:
        return "WARNING"
    return "STABLE"


def _action_type_for_recommendation(text: str) -> str:
    lower = (text or "").lower()
    if any(token in lower for token in ["rate limit", "throttle", "burst cap"]):
        return "throttle"
    if any(token in lower for token in ["autoscale", "scale", "horizontal", "worker"]):
        return "scale"
    if any(token in lower for token in ["investigate", "inspect", "trace", "dependency", "logs"]):
        return "investigate"
    if any(token in lower for token in ["test", "validation", "load", "replay"]):
        return "test"
    return "monitor"


def _action_label(text: str) -> str:
    action_type = _action_type_for_recommendation(text)
    if action_type == "throttle":
        return "Throttle Traffic"
    if action_type == "scale":
        return "Scale Capacity"
    if action_type == "investigate":
        return "Investigate Root Cause"
    if action_type == "test":
        return "Run Validation Test"
    return "Monitor Signals"


def _with_operational_decision_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    severity = str(data.get("severity", "medium")).lower()
    urgency = str(data.get("urgency", "medium")).lower()
    confidence = str(data.get("confidence", "medium")).lower()
    layer = str(data.get("affected_layer", "")).lower()
    if layer not in ALLOWED_LAYER:
        layer = _infer_layer(str(data.get("root_cause", "")))

    status = _system_status_from_severity(severity)
    action_required = severity != "low"

    recs = _as_list_of_str(data.get("recommendations"))
    actions = []
    for rec in recs[:3]:
        actions.append(
            {
                "label": _action_label(rec),
                "type": _action_type_for_recommendation(rec),
                "description": rec,
            }
        )

    if not actions:
        actions.append(
            {
                "label": "Monitor Signals",
                "type": "monitor",
                "description": "Track spikes, drops, anomalies, and queue depth against alert thresholds.",
            }
        )

    diagnosis = str(data.get("impact", "")).strip()
    if not diagnosis:
        diagnosis = str(data.get("summary", "")).strip()

    data["affected_layer"] = layer
    data["system_status"] = status
    data["diagnosis"] = diagnosis
    data["decision"] = {
        "action_required": action_required,
        "priority": urgency if urgency in ALLOWED_URGENCY else "medium",
        "next_step": recs[0] if recs else "Review current telemetry baselines and thresholds.",
    }
    data["actions"] = actions
    data["confidence"] = confidence if confidence in ALLOWED_CONFIDENCE else "medium"
    return data


def _normalize_response(data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    severity = str(data.get("severity", "medium")).strip().lower()
    if severity not in ALLOWED_SEVERITY:
        severity = "medium"

    urgency_default = {
        "critical": "immediate",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }[severity]
    urgency = str(data.get("urgency", urgency_default)).strip().lower()
    if urgency not in ALLOWED_URGENCY:
        urgency = urgency_default

    confidence = str(data.get("confidence", "medium")).strip().lower()
    if confidence not in ALLOWED_CONFIDENCE:
        confidence = "medium"

    recommendations = _as_list_of_str(data.get("recommendations"))
    if len(recommendations) < 2:
        recommendations = [
            "Apply ingress rate limiting and burst control at the gateway.",
            "Scale workers based on queue depth and p95 latency thresholds.",
        ]

    root_cause = str(data.get("root_cause", "")).strip()
    if ";" in root_cause:
        root_cause = root_cause.split(";", 1)[0].strip()
    if not root_cause:
        root_cause = "resource saturation due to burst traffic exceeding capacity"

    summary = str(data.get("summary", "")).strip()
    if not summary:
        summary = (
            f"{payload['spikes']} spikes, {payload['drops']} drops, and {payload['anomalies']} anomalies "
            f"with {payload['trend']} trend indicate {severity} production instability."
        )

    impact = str(data.get("impact", "")).strip()
    if not impact:
        impact = "Latency is elevated, failure rate is increased, throughput is degraded, and processing consistency is reduced."

    affected_layer = str(data.get("affected_layer", "")).strip().lower()
    if affected_layer not in ALLOWED_LAYER:
        affected_layer = _infer_layer(root_cause)

    normalized = {
        "summary": summary,
        "affected_layer": affected_layer,
        "root_cause": root_cause,
        "severity": severity,
        "impact": impact,
        "recommendations": recommendations,
        "urgency": urgency,
        "confidence": confidence,
    }
    return _with_operational_decision_fields(normalized)


def _rule_based_fallback(payload: Dict[str, Any], error: str = "") -> Dict[str, Any]:
    spikes = payload["spikes"]
    drops = payload["drops"]
    anomalies = payload["anomalies"]
    risk_score = payload["risk_score"]
    quality = payload["quality"]
    trend = payload["trend"]

    high_spikes = spikes >= 5
    high_drops = drops >= 2
    high_anomalies = anomalies >= 4

    if high_spikes and high_drops:
        severity = "critical"
        urgency = "immediate"
        layer = "processing"
        root_cause = "resource saturation due to burst traffic exceeding capacity"
        impact = "Latency is elevated, requests are failing under backpressure, throughput is degraded, and retry churn is causing inconsistent processing order."
        recommendations = [
            "Implement API gateway rate limiting with burst caps aligned to worker capacity.",
            "Autoscale processing workers on queue depth and p95 latency with minimum warm capacity.",
        ]
        confidence = "high"
    elif high_anomalies:
        severity = "high"
        urgency = "high"
        layer = "processing"
        root_cause = "unstable input stream causing inconsistent processing behavior"
        impact = "Invalid or volatile input patterns are driving processing variance, increasing retry/failure rates, and reducing deterministic throughput."
        recommendations = [
            "Enforce strict input validation and schema rejection at ingestion boundaries.",
            "Isolate and replay anomalous payload cohorts in a quarantine pipeline for deterministic reprocessing.",
        ]
        confidence = "high"
    elif drops >= 2:
        severity = "high"
        urgency = "high"
        layer = "network"
        root_cause = "service interruption in an upstream dependency causing request loss"
        impact = "Requests are being interrupted before completion, causing visible failure spikes, reduced throughput, and partial data loss windows."
        recommendations = [
            "Add circuit breakers and timeout budgets for upstream dependencies with fast-fail behavior.",
            "Provision dependency redundancy and enable automatic failover for interrupted services.",
        ]
        confidence = "high"
    elif (spikes + drops + anomalies) >= 3 or risk_score >= 12:
        severity = "medium"
        urgency = "medium"
        layer = "processing"
        root_cause = "intermittent workload variance causing periodic resource contention"
        impact = "Latency variance and intermittent request slowdowns are reducing steady-state throughput and introducing occasional processing inconsistencies."
        recommendations = [
            "Increase worker concurrency limits with queue backpressure tuning to smooth transient bursts.",
            "Optimize heavy request paths and cap expensive operations with per-request budget guards.",
        ]
        confidence = "medium"
    else:
        severity = "low"
        urgency = "low"
        layer = "ingestion"
        root_cause = "no dominant production failure signal detected"
        impact = "Current telemetry indicates stable latency and throughput without sustained failure amplification."
        recommendations = [
            "Keep current capacity settings and retain existing request guardrails.",
            "Run weekly load verification against SLO thresholds to confirm stability remains unchanged.",
        ]
        confidence = "low"

    fallback = {
        "summary": (
            f"{spikes} spikes, {drops} drops, and {anomalies} anomalies with {trend} trend "
            f"(risk_score={risk_score}, quality={quality}) indicate {severity} production instability."
        ),
        "affected_layer": layer,
        "root_cause": root_cause,
        "severity": severity,
        "impact": impact,
        "recommendations": recommendations,
        "urgency": urgency,
        "confidence": confidence,
        "source": "rule_based_fallback",
        "fallback_reason": error or "Claude API unavailable",
    }
    return _with_operational_decision_fields(fallback)


def _extract_json(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Empty model response")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(raw[start : end + 1])


def analyze_with_claude(data_summary: Dict[str, Any], model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    payload = _validated_payload(data_summary if isinstance(data_summary, dict) else {})
    prompt = _build_prompt(payload)

    try:
        client = _get_client()
        response = client.messages.create(
            model=model,
            max_tokens=700,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )

        parts = []
        for block in response.content:
            if getattr(block, "type", "") == "text":
                parts.append(block.text)

        parsed = _extract_json("\n".join(parts))
        normalized = _normalize_response(parsed, payload)
        normalized["source"] = "claude"
        return normalized
    except RuntimeError:
        raise
    except Exception as exc:
        return _rule_based_fallback(payload, str(exc) or "Claude API unavailable")
