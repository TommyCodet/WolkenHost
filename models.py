from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db=SQLAlchemy()
def now(): return datetime.now(timezone.utc)
class User(db.Model):
 id=db.Column(db.Integer,primary_key=True); email=db.Column(db.String(255),unique=True,nullable=False,index=True); password_hash=db.Column(db.String(255)); microsoft_sub=db.Column(db.String(255),unique=True); refresh_token_enc=db.Column(db.Text); is_admin=db.Column(db.Boolean,default=False,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=now)
 def set_password(self,p): self.password_hash=generate_password_hash(p)
 def check_password(self,p): return bool(self.password_hash and check_password_hash(self.password_hash,p))
class Bot(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True); name=db.Column(db.String(80),default='Mein AFK-Bot',nullable=False); host=db.Column(db.String(253),nullable=False); port=db.Column(db.Integer,default=25565,nullable=False); version=db.Column(db.String(20),default='auto',nullable=False); command_afk=db.Column(db.Boolean,default=True,nullable=False); autoreconnect=db.Column(db.Boolean,default=True,nullable=False); status=db.Column(db.String(20),default='stopped',nullable=False); pid=db.Column(db.Integer); started_at=db.Column(db.DateTime(timezone=True)); created_at=db.Column(db.DateTime(timezone=True),default=now)
class Ticket(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True); subject=db.Column(db.String(120),nullable=False); message=db.Column(db.Text,nullable=False); reply=db.Column(db.Text); status=db.Column(db.String(20),default='open',nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=now)
