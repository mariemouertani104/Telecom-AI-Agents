"""Tests unitaires MVP — Telecom AI Agent"""

import json
import pytest
from agent.tools.network import ping_host, get_interface_stats, scan_topology
from agent.tools.analyzer import analyze_anomaly, suggest_fix
from agent.tools.config import push_config, rollback_config


class TestNetworkTools:
    def test_ping_returns_valid_json(self):
        result = json.loads(ping_host("127.0.0.1"))
        assert "host" in result
        assert "reachable" in result
        assert "latency_ms" in result
        assert "status" in result

    def test_interface_stats_format(self):
        result = json.loads(get_interface_stats("192.168.1.1:GE0/0"))
        assert result["host"] == "192.168.1.1"
        assert result["interface"] == "GE0/0"
        assert 0 <= result["utilization_pct"] <= 100
        assert result["status"] in ("OK", "WARNING", "CRITICAL")

    def test_interface_stats_no_colon(self):
        result = json.loads(get_interface_stats("192.168.1.1"))
        assert result["host"] == "192.168.1.1"

    def test_topology_scan(self):
        result = json.loads(scan_topology("192.168.1.1"))
        assert "neighbors" in result
        assert isinstance(result["neighbors"], list)


class TestAnalyzer:
    def test_detect_critical_latency(self):
        metrics = json.dumps({"latency_ms": 200, "packet_loss_pct": 0})
        result = json.loads(analyze_anomaly(metrics))
        assert result["overall_status"] == "CRITICAL"
        assert any(a["metric"] == "latency_ms" for a in result["anomalies"])

    def test_detect_warning_utilization(self):
        metrics = json.dumps({"utilization_pct": 80})
        result = json.loads(analyze_anomaly(metrics))
        assert result["overall_status"] == "WARNING"

    def test_no_anomaly_ok(self):
        metrics = json.dumps({"latency_ms": 10, "utilization_pct": 30})
        result = json.loads(analyze_anomaly(metrics))
        assert result["overall_status"] == "OK"
        assert result["anomaly_count"] == 0

    def test_invalid_json(self):
        result = json.loads(analyze_anomaly("not-json"))
        assert "error" in result

    def test_suggest_fix_latency(self):
        result = json.loads(suggest_fix("latence élevée sur GE0/0"))
        assert result["fix"]["risk"] == "low"
        assert len(result["fix"]["commands"]) > 0

    def test_suggest_fix_utilization(self):
        result = json.loads(suggest_fix("utilisation bande passante critique"))
        assert result["fix"]["risk"] == "medium"


class TestConfigTools:
    def test_push_config_success(self):
        payload = json.dumps({
            "host": "192.168.1.1",
            "commands": ["interface GE0/0", " no shutdown"]
        })
        result = json.loads(push_config(payload))
        assert result["success"] is True
        assert result["commands_applied"] == 2

    def test_rollback_after_push(self):
        host = "10.0.0.1"
        push_config(json.dumps({"host": host, "commands": ["ip route 0.0.0.0 0.0.0.0 10.0.0.254"]}))
        result = json.loads(rollback_config(host))
        assert result["success"] is True
        assert len(result["rolled_back_commands"]) == 1

    def test_rollback_no_history(self):
        result = json.loads(rollback_config("99.99.99.99"))
        assert result["success"] is False
        assert "error" in result

    def test_push_invalid_json(self):
        result = json.loads(push_config("invalid"))
        assert result["success"] is False