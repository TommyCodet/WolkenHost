"""Single-node supervisor. For multi-worker/multi-node deployments use a dedicated agent."""
import json,os,subprocess,threading
from models import db
from config import BASE_DIR
from security import resolve_public_host
_lock=threading.RLock();_processes={}
def start_bot(bot):
 with _lock:
  item=_processes.get(bot.id);p=item[0] if item else None
  if p and p.poll() is None:return
  host,addresses=resolve_public_host(bot.host)
  cfg={'serverHost':host,'serverPort':int(bot.port),'mcVersion':bot.version,'afkEnabled':bool(bot.command_afk),'afkCommand':'/afk on' if bot.command_afk else '', 'autoReconnect':bool(bot.autoreconnect),'reconnectDelay':10}
  data_dir=BASE_DIR/'data';data_dir.mkdir(mode=0o700,exist_ok=True)
  auth_home=data_dir/f'auth-{bot.id}';auth_home.mkdir(mode=0o700,parents=True,exist_ok=True);os.chmod(auth_home,0o700)
  path=data_dir/f'bot-{bot.id}.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(cfg),encoding='utf-8');os.chmod(tmp,0o600);os.replace(tmp,path)
  log=open(data_dir/f'bot-{bot.id}.log','a',encoding='utf-8')
  try:p=subprocess.Popen(['node',str(BASE_DIR/'bot.js'),str(path)],cwd=BASE_DIR,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,close_fds=True,start_new_session=(os.name!='nt'),env={**os.environ,'HOME':str(auth_home)})
  except Exception:log.close();raise
  _processes[bot.id]=(p,log);bot.pid=p.pid;bot.status='starting';db.session.commit()
def stop_bot(bot):
 with _lock:
  item=_processes.get(bot.id)
  if item:
   p,log=item
   if p.poll() is None:
    p.terminate()
    try:p.wait(timeout=8)
    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
   log.close();_processes.pop(bot.id,None)
  bot.pid=None;bot.status='stopped';bot.started_at=None;db.session.commit()
def restart_bot(bot):stop_bot(bot);start_bot(bot)
