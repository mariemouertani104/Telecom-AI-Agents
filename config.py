"""
Outil de configuration réseau via SSH.
En prod: remplacer par Netmiko ConnectHandler.
"""

import json
from datetime import datetime


# Historique des configs pour rollback
_config_history: dict[str, list[dict]] = {}


def push_config(input_json: str) -> str:
    """
    Pousse une configuration sur un équipement.
    En prod: utiliser Netmiko.
    Input JSON: {"host": "...", "commands": [...]}
    """
    try:
        payload = json.loads(input_json)
        host = payload["host"]
        commands = payload["commands"]
    except (json.JSONDecodeError, KeyError) as e:
        return json.dumps({"success": False, "error": str(e)})

    # Simulation du push SSH
    entry = {
        "timestamp": datetime.now().isoformat(),
        "commands": commands,
        "applied": True,
    }
    _config_history.setdefault(host, []).append(entry)

    # En prod:
    # from netmiko import ConnectHandler
    # with ConnectHandler(host=host, device_type='cisco_ios',
    #                     username=os.getenv('NET_USER'),
    #                     password=os.getenv('NET_PASS')) as conn:
    #     output = conn.send_config_set(commands)

    return json.dumps({
        "success": True,
        "host": host,
        "commands_applied": len(commands),
        "timestamp": entry["timestamp"],
        "output": f"[SIMULATED] {len(commands)} commandes appliquées sur {host}",
    }, ensure_ascii=False)


def rollback_config(host: str) -> str:
    """Annule la dernière configuration poussée."""
    host = host.strip()
    history = _config_history.get(host, [])

    if not history:
        return json.dumps({
            "success": False,
            "error": f"Aucun historique de configuration pour {host}",
        })

    last = history.pop()
    return json.dumps({
        "success": True,
        "host": host,
        "rolled_back_commands": last["commands"],
        "original_timestamp": last["timestamp"],
        "message": f"Rollback effectué — {len(last['commands'])} commandes annulées.",
    }, ensure_ascii=False)