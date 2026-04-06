# Telecom AI Agent — MVP
 IN Telecommunications: Agents can autonomously configure and optimize networks, reducing both complexity and the risk of human error.
Agent autonome de diagnostic et configuration réseau basé sur Claude.

## Démarrage rapide (Codespaces)

```bash
# 1. Cloner et ouvrir dans Codespaces
# (bouton "<> Code > Codespaces" sur GitHub)

# 2. Configurer les variables d'environnement
cp .env.example .env
# Renseigner ANTHROPIC_API_KEY dans .env

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'agent
python -m agent.main

# 5. Lancer les tests
pytest tests/ -v
```

## Structure

```
telecom-ai-agent/
├── agent/
│   ├── main.py              # Agent principal (LangChain ReAct)
│   └── tools/
│       ├── network.py       # Ping, stats, topologie
│       ├── analyzer.py      # Détection d'anomalies
│       └── config.py        # Push config + rollback
├── tests/
│   └── test_tools.py        # Tests unitaires
├── .devcontainer/
│   └── devcontainer.json    # Config Codespaces
├── requirements.txt
└── .env.example
```

## Architecture de l'agent

```
Tâche → Agent ReAct (Claude) → Outils réseau → Rapport
              ↑                      ↓
         Raisonnement         Actions concrètes
```

L'agent suit le pattern **ReAct** (Reasoning + Acting) :
1. Analyse la tâche
2. Choisit un outil
3. Interprète le résultat
4. Répète jusqu'à avoir une réponse complète

## Passage en production

Remplacer les simulations dans `tools/network.py` par :

```python
from netmiko import ConnectHandler

conn = ConnectHandler(
    host=host,
    device_type='cisco_ios',
    username=os.getenv('NET_USER'),
    password=os.getenv('NET_PASS'),
)
output = conn.send_command('show interfaces')
```

## Prochaines étapes

- [ ] Dashboard FastAPI (`GET /status`, `POST /diagnose`)
- [ ] Intégration GNS3 API pour simulation
- [ ] Monitoring continu avec scheduler (APScheduler)
- [ ] Alertes (Slack/email) sur anomalies critiques
- [ ] Tests d'intégration avec routeurs virtuels
