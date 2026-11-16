"""Single-node process supervisor; use one Flask process on this VPS."""
import os,subprocess,threading
from models import Bot,db
from config import BASE_DIR
_lock=threading.RLock(); _processes={}
def start_bot(bot):
 with _lock:
  p=_processes.get(bot.id)
  if p and p.poll() is None: return
  import json
  cfg={'id':bot.id,'host':bot.host,'port':bot.port,'version':None if bot.version=='auto' else bot.version,'commandAfk':bool(bot.command_afk),'autoreconnect':bool(bot.autoreconnect)}
  path=BASE_DIR/'data'/f'bot-{bot.id}.json'; path.write_text(json.dumps(cfg),encoding='utf-8')
  if os.name!='nt': os.chmod(path,0o600)
  log=open(BASE_DIR/'data'/f'bot-{bot.id}.log','a',encoding='utf-8')
  p=subprocess.Popen(['node',str(BASE_DIR/'bot.js'),str(path)],cwd=BASE_DIR,stdout=log,stderr=subprocess.STDOUT,start_new_session=(os.name!='nt'))
  _processes[bot.id]=p; bot.pid=p.pid; bot.status='starting'; db.session.commit()
def stop_bot(bot):
 with _lock:
  p=_processes.get(bot.id)
  if p and p.poll() is None:
   p.terminate()
   try: p.wait(timeout=8)
   except subprocess.TimeoutExpired: p.kill()
  _processes.pop(bot.id,None); bot.pid=None; bot.status='stopped'; bot.started_at=None; db.session.commit()
def restart_bot(bot): stop_bot(bot); start_bot(bot)
