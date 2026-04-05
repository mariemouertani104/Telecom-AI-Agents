"""
Analyseur d'anomalies réseau + suggestion de corrections.
"""

import json
from typing import Any


THRESHOLDS = {
    "latency_ms":        {"warning": 50,  "critical": 150},
    "packet_loss_pct":   {"warning": 2,   "critical": 10},
    "utilization_pct":   {"warning": 75,  "critical": 90},
    "errors_in":         {"warning": 100, "critical": 300},
    "drops":             {"warning": 50,  "critical": 150},
}

FIX_TEMPLATES = {
    "high_latency": {
        "description": "Latence élevée détectée",
        "commands": [
            "interface GigabitEthernet0/0",
            " ip ospf cost 10",
            " no shutdown",
        ],
        "risk": "low",
    },
    "high_utilization": {
        "description": "Surcharge de bande passante",
        "commands": [
            "policy-map QOS-POLICY",
            " class VOIP",
            "  priority 512",
            " class DATA",
            "  bandwidth 256",
            "interface GigabitEthernet0/0",
            " service-policy output QOS-POLICY",
        ],
        "risk": "medium",
    },
    "high_errors": {
        "description": "Erreurs d'interface excessives",
        "commands": [
            "interface GigabitEthernet0/0",
            " shutdown",
            " no shutdown",
            " carrier-delay msec 500",
        ],
        "risk": "medium",
    },
    "packet_loss": {
        "description": "Perte de paquets significative",
        "commands": [
            "ip route 0.0.0.0 0.0.0.0 192.168.1.254 track 1",
            "ip sla 1",
            " icmp-echo 8.8.8.8",
            " frequency 10",
            "ip sla schedule 1 life forever start-time now",
        ],
        "risk": "low",
    },
}


def analyze_anomaly(metrics_json: str) -> str:
    """Analyse des métriques et retourne les anomalies détectées."""
    try:
        metrics: dict[str, Any] = json.loads(metrics_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "JSON invalide", "anomalies": []})

    anomalies = []
    for metric, value in metrics.items():
        if metric not in THRESHOLDS or not isinstance(value, (int, float)):
            continue
        t = THRESHOLDS[metric]
        if value >= t["critical"]:
            anomalies.append({
                "metric": metric,
                "value": value,
                "severity": "CRITICAL",
                "threshold": t["critical"],
            })
        elif value >= t["warning"]:
            anomalies.append({
                "metric": metric,
                "value": value,
                "severity": "WARNING",
                "threshold": t["warning"],
            })

    return json.dumps({
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "overall_status": (
            "CRITICAL" if any(a["severity"] == "CRITICAL" for a in anomalies)
            else "WARNING" if anomalies else "OK"
        ),
    }, ensure_ascii=False)


def suggest_fix(problem_description: str) -> str:
    """Suggère une correction selon le problème détecté."""
    desc = problem_description.lower()

    if "latence" in desc or "latency" in desc:
        fix = FIX_TEMPLATES["high_latency"]
    elif "utilisation" in desc or "utilization" in desc or "bande passante" in desc:
        fix = FIX_TEMPLATES["high_utilization"]
    elif "erreur" in desc or "error" in desc:
        fix = FIX_TEMPLATES["high_errors"]
    elif "perte" in desc or "loss" in desc:
        fix = FIX_TEMPLATES["packet_loss"]
    else:
        fix = {
            "description": "Problème non identifié — intervention manuelle recommandée",
            "commands": [],
            "risk": "unknown",
        }

    return json.dumps({
        "fix": fix,
        "warning": "Valider avec un ingénieur réseau avant déploiement en production.",
        "auto_apply": fix["risk"] == "low",
    }, ensure_ascii=False)