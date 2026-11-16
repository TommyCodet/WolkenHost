"""Panel-side desired-state API. The independent node_agent.py owns processes."""
from datetime import datetime, timezone
from models import db

def start_bot(bot):
    bot.desired_state = 'running'
    bot.status = 'queued'
    bot.last_error = None
    db.session.commit()

def stop_bot(bot):
    bot.desired_state = 'stopped'
    bot.status = 'stopping'
    db.session.commit()

def restart_bot(bot):
    bot.desired_state = 'restart'
    bot.status = 'restarting'
    bot.last_error = None
    db.session.commit()
