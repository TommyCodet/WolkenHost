import os,sys,secrets
from functools import wraps
from authlib.integrations.flask_client import OAuth
from flask import Flask,abort,flash,redirect,render_template,request,session,url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from config import *
from models import db,User,Bot,Ticket
from security import encrypt_secret,validate_host
from worker import start_bot,stop_bot,restart_bot
from node_agent import migrate_schema
def create_app():
 validate_settings()
 app=Flask(__name__)
 app.config.update(SECRET_KEY=SECRET_KEY,SQLALCHEMY_DATABASE_URI=DATABASE_URL,SQLALCHEMY_TRACK_MODIFICATIONS=False,
  SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=BASE_URL.startswith('https://'),
  PERMANENT_SESSION_LIFETIME=__import__('datetime').timedelta(hours=8),WTF_CSRF_TIME_LIMIT=3600,
  MAX_CONTENT_LENGTH=1024*1024,TRUSTED_HOSTS=TRUSTED_HOSTS)
 db.init_app(app);csrf=CSRFProtect(app);limiter=Limiter(get_remote_address,app=app,default_limits=['300 per day','80 per hour'])
 oauth=OAuth(app)
 if MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET:
  oauth.register(name='microsoft',client_id=MICROSOFT_CLIENT_ID,client_secret=MICROSOFT_CLIENT_SECRET,
   server_metadata_url=f'https://login.microsoftonline.com/{MICROSOFT_TENANT}/v2.0/.well-known/openid-configuration',
   client_kwargs={'scope':'openid email profile offline_access'})
 with app.app_context():
  db.create_all()
  migrate_schema()
 def me():
  uid=session.get('uid');return db.session.get(User,uid) if uid else None
 def login_required(fn):
  @wraps(fn)
  def w(*a,**k):
   if not me():return redirect(url_for('login',next=request.path))
   return fn(*a,**k)
  return w
 def admin_required(fn):
  @wraps(fn)
  def w(*a,**k):
   if not me() or not me().is_admin:abort(403)
   return fn(*a,**k)
  return w
 @app.after_request
 def security_headers(response):
  response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY'
  response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
  response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
  response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
  if BASE_URL.startswith('https://'):response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
  return response
 @app.context_processor
 def inject():return {'me':me()}
 @app.get('/')
 def index():return render_template('home.html') if not me() else redirect(url_for('dashboard'))
 @app.route('/register',methods=['GET','POST'])
 @limiter.limit('3 per hour',methods=['POST'])
 def register():
  if request.method=='POST':
   email=request.form.get('email','').strip().lower();pw=request.form.get('password','')
   if len(email)>254 or '@' not in email or len(pw)<12 or len(pw)>256:flash('Bitte gültige E-Mail und ein Passwort mit mindestens 12 Zeichen verwenden.','error')
   elif User.query.filter_by(email=email).first():flash('Registrierung nicht möglich.','error')
   else:
    u=User(email=email);u.set_password(pw);db.session.add(u);db.session.commit();session.clear();session['uid']=u.id;session.permanent=True;return redirect(url_for('dashboard'))
  return render_template('login.html',register=True)
 @app.route('/login',methods=['GET','POST'])
 @limiter.limit('5 per minute',methods=['POST'])
 def login():
  if request.method=='POST':
   u=User.query.filter_by(email=request.form.get('email','').strip().lower()).first()
   if u and u.check_password(request.form.get('password','')):session.clear();session['uid']=u.id;session.permanent=True;return redirect(url_for('dashboard'))
   flash('E-Mail oder Passwort falsch.','error')
  return render_template('login.html',register=False)
 @app.get('/login/microsoft')
 @limiter.limit('10 per minute')
 def microsoft_login():
  if 'microsoft' not in oauth._clients:flash('Microsoft-Login ist noch nicht konfiguriert.','error');return redirect(url_for('login'))
  session['oauth_nonce']=secrets.token_urlsafe(24)
  return oauth.microsoft.authorize_redirect(url_for('microsoft_callback',_external=True),nonce=session['oauth_nonce'])
 @app.get('/login/microsoft/callback')
 def microsoft_callback():
  if 'microsoft' not in oauth._clients:abort(503)
  nonce=session.pop('oauth_nonce',None)
  if not nonce:abort(400)
  token=oauth.microsoft.authorize_access_token();info=oauth.microsoft.parse_id_token(token,nonce=nonce)
  sub=info.get('sub');email=(info.get('email') or info.get('preferred_username') or '').strip().lower()
  if not sub or not email:abort(400)
  u=User.query.filter_by(microsoft_sub=sub).first()
  if not u:
   # Never silently link a Microsoft identity to a password account by matching email.
   if User.query.filter_by(email=email).first():
    flash('Zu dieser E-Mail existiert bereits ein Passwort-Konto. Bitte dort anmelden; automatisches Verknüpfen ist aus Sicherheitsgründen deaktiviert.','error')
    return redirect(url_for('login'))
   u=User(email=email,microsoft_sub=sub);db.session.add(u)
  if token.get('refresh_token'):u.refresh_token_enc=encrypt_secret(token['refresh_token'])
  db.session.commit();session.clear();session['uid']=u.id;session.permanent=True;return redirect(url_for('dashboard'))
 @app.post('/logout')
 @login_required
 def logout():session.clear();return redirect(url_for('login'))
 @app.get('/dashboard')
 @login_required
 def dashboard():return render_template('dashboard.html',bots=Bot.query.filter_by(user_id=me().id).all())
 @app.route('/bots/new',methods=['GET','POST'])
 @login_required
 def bot_new():
  if request.method=='POST':
   try:host=validate_host(request.form.get('host'))
   except ValueError as e:flash(str(e),'error');return render_template('bot_new.html')
   try:port=int(request.form.get('port','25565'))
   except ValueError:port=0
   version=request.form.get('version','auto')
   startup_commands=request.form.get('startup_commands','')
   commands=[line.strip() for line in startup_commands.splitlines() if line.strip()]
   invalid_commands=(len(commands)>10 or any(len(line)>100 or any(ord(ch)<32 for ch in line) for line in commands))
   if invalid_commands:flash('Maximal 10 Startbefehle mit jeweils höchstens 100 Zeichen erlaubt.','error')
   elif not 1<=port<=65535:flash('Port muss zwischen 1 und 65535 liegen.','error')
   elif version not in {'auto','1.21.1','1.20.4','1.19.4'}:flash('Ungültige Version.','error')
   else:
    b=Bot(user_id=me().id,host=host,port=port,version=version,command_afk=request.form.get('command_afk')=='on',startup_commands='\n'.join(commands),autoreconnect=request.form.get('autoreconnect')=='on');db.session.add(b);db.session.commit();return redirect(url_for('dashboard'))
  return render_template('bot_new.html')
 def owned(bot_id):
  b=db.session.get(Bot,bot_id)
  if not b or b.user_id!=me().id:abort(404)
  return b
 @app.post('/bots/<int:bot_id>/<action>')
 @login_required
 def bot_action(bot_id,action):
  b=owned(bot_id)
  if action=='start':start_bot(b)
  elif action=='stop':stop_bot(b)
  elif action=='restart':restart_bot(b)
  else:abort(404)
  return redirect(url_for('dashboard'))
 @app.route('/tickets',methods=['GET','POST'])
 @login_required
 def tickets():
  if request.method=='POST':
   s=request.form.get('subject','').strip();m=request.form.get('message','').strip()
   if s and m and len(s)<=120 and len(m)<=5000:db.session.add(Ticket(user_id=me().id,subject=s,message=m));db.session.commit();flash('Ticket erstellt.','success')
   else:flash('Bitte Betreff und Nachricht prüfen.','error')
  return render_template('tickets.html',tickets=Ticket.query.filter_by(user_id=me().id).order_by(Ticket.created_at.desc()).all())
 @app.route('/admin',methods=['GET','POST'])
 @login_required
 @admin_required
 def admin():
  if request.method=='POST':
   try:t=db.session.get(Ticket,int(request.form.get('ticket_id',0)))
   except (ValueError,TypeError):t=None
   if t:t.reply=request.form.get('reply','')[:5000];t.status='answered';db.session.commit()
  return render_template('admin.html',users=User.query.order_by(User.id.desc()).all(),bots=Bot.query.order_by(Bot.id.desc()).all(),tickets=Ticket.query.order_by(Ticket.created_at.desc()).all())
 @app.post('/admin/bots/<int:bot_id>/<action>')
 @login_required
 @admin_required
 def admin_bot_action(bot_id,action):
  b=db.session.get(Bot,bot_id)
  if not b:abort(404)
  if action=='start':start_bot(b)
  elif action=='stop':stop_bot(b)
  elif action=='restart':restart_bot(b)
  else:abort(404)
  return redirect(url_for('admin'))
 @app.get('/health')
 def health():return {'status':'ok','node':NODE_ID}
 return app
def make_admin(email):
 app=create_app()
 with app.app_context():
  u=User.query.filter_by(email=email.strip().lower()).first()
  if not u:raise SystemExit('User existiert nicht. Erst registrieren.')
  u.is_admin=True;db.session.commit();print(f'Adminrechte gesetzt: {u.email}')
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='make-admin':make_admin(sys.argv[2])
 else:create_app().run(host='127.0.0.1' if BASE_URL.startswith('http://127.0.0.1') else '0.0.0.0',port=int(os.getenv('PORT','5000')),debug=False)
