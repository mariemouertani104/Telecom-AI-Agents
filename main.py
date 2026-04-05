"""
Telecom AI Agent — MVP
Agent autonome de diagnostic et configuration réseau.
"""

import asyncio
import json
from datetime import datetime
from langchain.agents import AgentExecutor, create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from agent.tools.network import ping_host, get_interface_stats, scan_topology
from agent.tools.config import push_config, rollback_config
from agent.tools.analyzer import analyze_anomaly, suggest_fix


SYSTEM_PROMPT = PromptTemplate.from_template("""
Tu es un agent réseau télécom autonome. Tu diagnostiques, analyses et corriges
les problèmes réseau sans intervention humaine.

Tu as accès aux outils suivants :
{tools}

Noms des outils : {tool_names}

Règles :
- Toujours diagnostiquer AVANT de corriger
- Logger chaque action avec timestamp
- Ne jamais pousser une config sans vérification préalable
- En cas de doute, analyser et recommander sans agir

Format de réponse :
Question: la tâche à accomplir
Thought: ton raisonnement
Action: l'outil à utiliser
Action Input: les paramètres
Observation: résultat de l'outil
... (répète si nécessaire)
Thought: j'ai assez d'information
Final Answer: rapport final structuré

Question: {input}
{agent_scratchpad}
""")


def build_tools() -> list[Tool]:
    return [
        Tool(
            name="ping_host",
            func=ping_host,
            description="Ping un hôte et retourne latence/perte. Input: adresse IP ou hostname."
        ),
        Tool(
            name="get_interface_stats",
            func=get_interface_stats,
            description="Récupère les stats d'une interface (bande passante, erreurs, drops). Input: 'host:interface' ex: '192.168.1.1:GE0/0'"
        ),
        Tool(
            name="scan_topology",
            func=scan_topology,
            description="Scanne la topologie réseau et retourne les voisins LLDP/CDP. Input: adresse IP du routeur."
        ),
        Tool(
            name="analyze_anomaly",
            func=analyze_anomaly,
            description="Analyse des métriques réseau et détecte les anomalies. Input: JSON avec métriques."
        ),
        Tool(
            name="suggest_fix",
            func=suggest_fix,
            description="Propose une correction pour une anomalie détectée. Input: description du problème."
        ),
        Tool(
            name="push_config",
            func=push_config,
            description="Pousse une configuration sur un équipement via SSH. Input: JSON avec 'host', 'commands'."
        ),
        Tool(
            name="rollback_config",
            func=rollback_config,
            description="Annule la dernière configuration poussée. Input: adresse IP du routeur."
        ),
    ]


def build_agent() -> AgentExecutor:
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0,
        max_tokens=4096,
    )
    tools = build_tools()
    agent = create_react_agent(llm, tools, SYSTEM_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


async def run_agent(task: str) -> dict:
    print(f"\n{'='*60}")
    print(f"[{datetime.now().isoformat()}] Nouvelle tâche : {task}")
    print('='*60)

    executor = build_agent()
    result = await asyncio.to_thread(executor.invoke, {"input": task})

    report = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "answer": result["output"],
        "steps": len(result.get("intermediate_steps", [])),
    }
    print(f"\n[RAPPORT FINAL]\n{json.dumps(report, indent=2, ensure_ascii=False)}")
    return report


if __name__ == "__main__":
    task = (
        "Diagnostique l'hôte 192.168.1.1 : vérifie sa connectivité, "
        "analyse ses interfaces, détecte toute anomalie et propose une correction."
    )
    asyncio.run(run_agent(task))