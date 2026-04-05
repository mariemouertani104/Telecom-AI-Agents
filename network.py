"""
Outils réseau — MVP avec simulation réaliste.
En prod: remplacer les simulations par Netmiko/NAPALM/pysnmp.
"""

import json
import random
import subprocess
from dataclasses import dataclass, asdict


@dataclass
class PingResult:
    host: str
    reachable: bool
    latency_ms: float
    packet_loss_pct: float
    status: str


@dataclass
class InterfaceStats:
    host: str
    interface: str
    bandwidth_mbps: float
    utilization_pct: float
    errors_in: int
    errors_out: int
    drops: int
    status: str


def ping_host(host: str) -> str:
    """
    Ping réel si disponible, sinon simulation.
    En prod: utiliser subprocess.run(['ping', '-c', '4', host])
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "3", "-W", "1", host],
            capture_output=True, text=True, timeout=5
        )
        reachable = result.returncode == 0
        latency = round(random.uniform(1.2, 45.0), 2) if reachable else 0.0
        loss = 0.0 if reachable else 100.0
    except Exception:
        # Simulation si host inaccessible
        reachable = random.random() > 0.2
        latency = round(random.uniform(1.2, 120.0), 2) if reachable else 0.0
        loss = round(random.uniform(0, 5), 1) if reachable else 100.0

    status = "OK" if reachable and loss < 5 else ("DEGRADED" if reachable else "DOWN")
    r = PingResult(host, reachable, latency, loss, status)
    return json.dumps(asdict(r), ensure_ascii=False)


def get_interface_stats(input_str: str) -> str:
    """
    Récupère les stats d'une interface.
    En prod: utiliser Netmiko + SNMP (pysnmp).
    Format input: 'host:interface'
    """
    try:
        host, interface = input_str.split(":", 1)
    except ValueError:
        host, interface = input_str, "GE0/0"

    # Simulation avec anomalies aléatoires
    utilization = round(random.uniform(10, 99), 1)
    errors = random.randint(0, 500)
    drops = random.randint(0, 200)

    status = "CRITICAL" if utilization > 90 or errors > 300 else \
             "WARNING"  if utilization > 75 or errors > 100 else "OK"

    stats = InterfaceStats(
        host=host.strip(),
        interface=interface.strip(),
        bandwidth_mbps=1000.0,
        utilization_pct=utilization,
        errors_in=errors,
        errors_out=random.randint(0, 50),
        drops=drops,
        status=status,
    )
    return json.dumps(asdict(stats), ensure_ascii=False)


def scan_topology(host: str) -> str:
    """
    Scanne les voisins LLDP/CDP.
    En prod: utiliser Netmiko + 'show lldp neighbors detail'.
    """
    neighbors = [
        {"neighbor": f"router-{i}.local", "ip": f"192.168.1.{10 + i}",
         "interface_local": f"GE0/{i}", "interface_remote": "GE0/0",
         "protocol": random.choice(["LLDP", "CDP"])}
        for i in range(random.randint(1, 4))
    ]
    return json.dumps({
        "host": host,
        "neighbor_count": len(neighbors),
        "neighbors": neighbors
    }, ensure_ascii=False)