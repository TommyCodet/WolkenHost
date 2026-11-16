import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
BASE_DIR=Path(__file__).resolve().parent
DATA_DIR=BASE_DIR/'data'; DATA_DIR.mkdir(exist_ok=True)
SECRET_KEY=os.getenv('FLASK_SECRET_KEY','dev-only-change-me')
DATABASE_URL=os.getenv('DATABASE_URL',f'sqlite:///{DATA_DIR / "wolkenhost.db"}')
FERNET_KEY=os.getenv('FERNET_KEY','')
MICROSOFT_CLIENT_ID=os.getenv('MICROSOFT_CLIENT_ID','')
MICROSOFT_CLIENT_SECRET=os.getenv('MICROSOFT_CLIENT_SECRET','')
MICROSOFT_TENANT=os.getenv('MICROSOFT_TENANT','consumers')
BASE_URL=os.getenv('BASE_URL','http://127.0.0.1:5000')
ADMIN_EMAILS={x.strip().lower() for x in os.getenv('ADMIN_EMAILS','').split(',') if x.strip()}
NODE_ID=os.getenv('NODE_ID','local-1')
