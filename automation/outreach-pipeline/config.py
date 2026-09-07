# config.py — Central de configuração do pipeline
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Conta Gmail (já autenticada via gog auth add)
GMAIL_ACCOUNT = "kleber@ziontechgroup.com"

# Caminhos
LEADS_FILE = BASE_DIR / "leads.json"
TRACKING_FILE = BASE_DIR / "tracking.jsonl"
TEMPLATES_DIR = BASE_DIR / "templates"

# Comportamento
DRY_RUN = False
MAX_SENDS_PER_RUN = 50
RATE_LIMIT_SLEEP = 2.0  # segundos entre envios
RETRY_ON_FAILURE = 1     # tentativas extras em falha

# Comando gog para envio (placeholder {account}, {to}, {subject}, {body})
GOG_SEND_CMD = [
    "gog", "gmail", "send",
    "--account", "{account}",
    "--to", "{to}",
    "--subject", "{subject}",
    "--body", "{body}",
]
