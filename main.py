"""
Telecom AI Agent — MVP
Compatible LangChain 1.x + Gemini
"""

import json
import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, ToolMessage
from network import ping_host, get_interface_stats, scan_topology
from config import push_config, rollback_config
from analyzer import analyze_anomaly, suggest_fix


TOOLS_LIST = [
    Tool(name="ping_host", func=ping_host,
         description="Ping un hôte et retourne latence/perte. Input: adresse IP."),
    Tool(name="get_interface_stats", func=get_interface_stats,
         description="Stats d'une interface. Input: 'host:interface' ex: '192.168.1.1:GE0/0'"),
    Tool(name="scan_topology", func=scan_topology,
         description="Scanne les voisins LLDP/CDP. Input: adresse IP du routeur."),
    Tool(name="analyze_anomaly", func=analyze_anomaly,
         description="Détecte les anomalies réseau. Input: JSON avec métriques."),
    Tool(name="suggest_fix", func=suggest_fix,
         description="Propose une correction. Input: description du problème."),
    Tool(name="push_config", func=push_config,
         description="Pousse une config SSH. Input: JSON avec 'host' et 'commands'."),
    Tool(name="rollback_config", func=rollback_config,
         description="Rollback de la dernière config. Input: adresse IP."),
]


def run_agent(task: str) -> dict:
    print(f"\n{'='*60}")
    print(f"[{datetime.now().isoformat()}] Tâche : {task}")
    print('='*60)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )

    tools_map = {t.name: t for t in TOOLS_LIST}
    llm_with_tools = llm.bind_tools(TOOLS_LIST)

    messages = [HumanMessage(content=task)]
    steps = 0

    while steps < 10:
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        steps += 1

        if not response.tool_calls:
            break

        for call in response.tool_calls:
            name = call["name"]
            args = call["args"]
            inp = args.get("__arg1") or args.get("input") or (list(args.values())[0] if args else "")
            print(f"\n>> Outil : {name}({inp})")
            result = tools_map[name].func(inp) if name in tools_map else "Outil inconnu"
            print(f"<< {result[:200]}")
            messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    answer = response.content if hasattr(response, "content") else str(response)
    report = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "answer": answer,
        "steps": steps,
    }
    print(f"\n{'='*60}\nRAPPORT FINAL :\n{answer}\n{'='*60}")
    return report


if __name__ == "__main__":
    task = (
        "Diagnostique l'hôte 192.168.1.1 : vérifie sa connectivité, "
        "analyse ses interfaces, détecte toute anomalie et propose une correction."
    )
    run_agent(task)