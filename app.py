import os
from functools import wraps
from authlib.integrations.flask_client import OAuth
from flask import Flask,abort,flash,redirect,render_template,request,session,url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import *
from models import db,User,Bot,Ticket
from security import encrypt_secret,validate_host
from worker import start_bot,stop_bot,restart_bot
def create_app():
 app=Flask(__name__);app.config.update(SECRET_KEY=SECRET_KEY,SQLALCHEMY_DATABASE_URI=DATABASE_URL,SQLALCHEMY_TRACK_MODIFICATIONS=False,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=BASE_URL.startswith('https://'))
 db.init_app(app);CSRFProtect(app);Limiter(get_remote_address,app=app,default_limits=['200 per day','50 per hour']);oauth=OAuth(app)
 if MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET:oauth.register(name='microsoft',client_id=MICROSOFT_CLIENT_ID,client_secret=MICROSOFT_CLIENT_SECRET,server_metadata_url=f'https://login.microsoftonline.com/{MICROSOFT_TENANT}/v2.0/.well-known/openid-configuration',client_kwargs={'scope':'openid email profile offline_access'})
 with app.app_context():db.create_all()
 def me():
  uid=session.get('uid');return db.session.get(User,uid) if uid else None
 def login_required(fn):
  @wraps(fn)
  def w(*a,**k):
   if not me():return redirect(url_for('login'))
   return fn(*a,**k)
  return w
 def admin_required(fn):
  @wraps(fn)
  def w(*a,**k):
   if not me() or not me().is_admin:abort(403)
   return fn(*a,**k)
  return w
 @app.context_processor
 def inject():return {'me':me()}
 @app.get('/')
 def index():return redirect(url_for('dashboard') if me() else url_for('login'))
 @app.route('/register',methods=['GET','POST'])
 def register():
  if request.method=='POST':
   email=request.form.get('email','').strip().lower();pw=request.form.get('password','')
   if '@' not in email or len(pw)<10:flash('Bitte gültige E-Mail und mindestens 10 Zeichen Passwort verwenden.','error')
   elif User.query.filter_by(email=email).first():flash('Dieses Konto existiert bereits.','error')
   else:
    u=User(email=email);u.set_password(pw);u.is_admin=email in ADMIN_EMAILS;db.session.add(u);db.session.commit();session['uid']=u.id;return redirect(url_for('dashboard'))
  return render_template('login.html',register=True)
 @app.route('/login',methods=['GET','POST'])
 def login():
  if request.method=='POST':
   u=User.query.filter_by(email=request.form.get('email','').strip().lower()).first()
   if u and u.check_password(request.form.get('password','')):session.clear();session['uid']=u.id;return redirect(url_for('dashboard'))
   flash('Login fehlgeschlagen.','error')
  return render_template('login.html',register=False)
 @app.get('/login/microsoft')
 def microsoft_login():
  if 'microsoft' not in oauth._clients:abort(503)
  return oauth.microsoft.authorize_redirect(url_for('microsoft_callback',_external=True))
 @app.get('/login/microsoft/callback')
 def microsoft_callback():
  if 'microsoft' not in oauth._clients:abort(503)
  token=oauth.microsoft.authorize_access_token();info=token.get('userinfo') or oauth.microsoft.userinfo();email=(info.get('email') or info.get('preferred_username') or '').lower();sub=info.get('sub')
  if not email or not sub:abort(400)
  u=User.query.filter_by(microsoft_sub=sub).first() or User.query.filter_by(email=email).first() or User(email=email);u.microsoft_sub=sub
  if token.get('refresh_token'):u.refresh_token_enc=encrypt_secret(token['refresh_token'])
  u.is_admin=u.is_admin or email in ADMIN_EMAILS;db.session.add(u);db.session.commit();session.clear();session['uid']=u.id;return redirect(url_for('dashboard'))
 @app.get('/logout')
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
   if not 1<=port<=65535:flash('Port muss zwischen 1 und 65535 liegen.','error')
   elif version not in {'auto','1.21.1','1.20.4','1.19.4'}:flash('Ungültige Version.','error')
   else:
    b=Bot(user_id=me().id,host=host,port=port,version=version,command_afk=request.form.get('command_afk')=='on',autoreconnect=request.form.get('autoreconnect')=='on');db.session.add(b);db.session.commit();return redirect(url_for('dashboard'))
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
  flash('Aktion ausgeführt.','success');return redirect(url_for('dashboard'))
 @app.route('/tickets',methods=['GET','POST'])
 @login_required
 def tickets():
  if request.method=='POST':
   s=request.form.get('subject','').strip();m=request.form.get('message','').strip()
   if s and m:db.session.add(Ticket(user_id=me().id,subject=s[:120],message=m[:5000]));db.session.commit();flash('Ticket erstellt.','success')
  return render_template('tickets.html',tickets=Ticket.query.filter_by(user_id=me().id).order_by(Ticket.created_at.desc()).all())
 @app.route('/admin',methods=['GET','POST'])
 @login_required
 @admin_required
 def admin():
  if request.method=='POST':
   t=db.session.get(Ticket,int(request.form.get('ticket_id',0)))
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
app=create_app()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')),debug=False)
