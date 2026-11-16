import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
BASE_DIR=Path(__file__).resolve().parent
DATA_DIR=BASE_DIR/'data'
DATA_DIR.mkdir(mode=0o700,exist_ok=True)
SECRET_KEY=os.getenv('FLASK_SECRET_KEY','')
DATABASE_URL=os.getenv('DATABASE_URL',f'sqlite:///{DATA_DIR / "wolkenhost.db"}')
FERNET_KEY=os.getenv('FERNET_KEY','')
MICROSOFT_CLIENT_ID=os.getenv('MICROSOFT_CLIENT_ID','')
MICROSOFT_CLIENT_SECRET=os.getenv('MICROSOFT_CLIENT_SECRET','')
MICROSOFT_TENANT=os.getenv('MICROSOFT_TENANT','consumers')
BASE_URL=os.getenv('BASE_URL','http://127.0.0.1:5000').rstrip('/')
NODE_ID=os.getenv('NODE_ID','local-1')
TRUSTED_HOSTS=[x.strip() for x in os.getenv('TRUSTED_HOSTS','localhost,127.0.0.1').split(',') if x.strip()]
def validate_settings():
 if len(SECRET_KEY)<32 or SECRET_KEY.lower() in {'change-me','dev-only-change-me','replace-with-long-random-secret'}:
  raise RuntimeError('FLASK_SECRET_KEY fehlt/ist unsicher. Bitte in .env einen zufälligen Schlüssel mit mindestens 32 Zeichen setzen.')
 if BASE_URL.startswith('https://') is False and os.getenv('WOLKEHOST_ALLOW_INSECURE_HTTP')!='1' and BASE_URL not in {'http://127.0.0.1:5000','http://localhost:5000'}:
  raise RuntimeError('Für externe Nutzung HTTPS in BASE_URL konfigurieren.')
