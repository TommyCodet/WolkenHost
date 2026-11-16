"""Single-node process agent. Run as a dedicated systemd service, separate from Flask."""
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from config import BASE_DIR, DATABASE_URL
from models import db, Bot
from flask import Flask
from security import resolve_public_host

POLL_SECONDS = 5
STOP_TIMEOUT = 8

def utcnow():
    return datetime.now(timezone.utc)

def create_agent_app():
    app = Flask('wolkehost-node-agent')
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        migrate_schema()
    return app

def migrate_schema():
    """Small additive SQLite migration for existing MVP installations."""
    engine = db.engine
    if engine.dialect.name != 'sqlite':
        return
    with engine.begin() as conn:
        cols = {row[1] for row in conn.exec_driver_sql('PRAGMA table_info(bot)').fetchall()}
        additions = {
            'desired_state': "VARCHAR(20) NOT NULL DEFAULT 'stopped'",
            'uptime_seconds': 'INTEGER NOT NULL DEFAULT 0',
            'last_heartbeat': 'DATETIME',
            'last_error': 'VARCHAR(500)',
            'startup_commands': "TEXT NOT NULL DEFAULT ''",
        }
        for name, ddl in additions.items():
            if name not in cols:
                conn.exec_driver_sql(f'ALTER TABLE bot ADD COLUMN {name} {ddl}')

class Supervisor:
    def __init__(self):
        self.children = {}
        self.data_dir = BASE_DIR / 'data'
        self.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    def _status_path(self, bot_id):
        return self.data_dir / f'bot-{bot_id}.status.json'

    def _config(self, bot):
        host, _addresses = resolve_public_host(bot.host)
        return {
            'serverHost': host, 'serverPort': int(bot.port),
            'mcVersion': bot.version, 'afkEnabled': bool(bot.command_afk),
            'startupCommands': (['/afk on'] if bot.command_afk else []) +
                [line.strip() for line in (bot.startup_commands or '').splitlines() if line.strip()],
            'autoReconnect': bool(bot.autoreconnect), 'reconnectDelay': 10,
        }

    def _stop(self, bot_id):
        item = self.children.pop(bot_id, None)
        if not item:
            return
        proc, log = item
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=STOP_TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        log.close()
        try:
            self._status_path(bot_id).unlink(missing_ok=True)
        except OSError:
            pass

    def _start(self, bot):
        cfg = self._config(bot)
        path = self.data_dir / f'bot-{bot.id}.json'
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(cfg), encoding='utf-8')
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        auth_home = self.data_dir / f'auth-{bot.id}'
        auth_home.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(auth_home, 0o700)
        status_path = self._status_path(bot.id)
        status_path.unlink(missing_ok=True)
        log = open(self.data_dir / f'bot-{bot.id}.log', 'a', encoding='utf-8')
        env = {**os.environ, 'HOME': str(auth_home), 'WOLKEHOST_BOT_ID': str(bot.id),
               'WOLKEHOST_STATUS_FILE': str(status_path)}
        try:
            proc = subprocess.Popen(
                ['node', str(BASE_DIR / 'bot.js'), str(path)],
                cwd=BASE_DIR, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, close_fds=True,
                start_new_session=(os.name != 'nt'), env=env,
            )
        except Exception:
            log.close()
            raise
        self.children[bot.id] = (proc, log)
        bot.pid = proc.pid
        bot.status = 'starting'
        bot.started_at = utcnow()
        bot.last_error = None

    def reconcile(self):
        bots = Bot.query.all()
        active_ids = {b.id for b in bots if b.desired_state in ('running', 'restart')}
        for bot_id in list(self.children):
            if bot_id not in active_ids:
                self._stop(bot_id)
        for bot in bots:
            bot.last_heartbeat = utcnow()
            item = self.children.get(bot.id)
            proc = item[0] if item else None
            if proc and proc.poll() is not None:
                item[1].close()
                self.children.pop(bot.id, None)
                bot.pid = None
                bot.status = 'crashed'
                bot.last_error = f'Bot-Prozess beendet (Exit-Code {proc.returncode})'
                proc = None
            if bot.desired_state == 'stopped':
                if proc:
                    self._stop(bot.id)
                bot.pid = None
                bot.status = 'stopped'
                bot.started_at = None
                continue
            if bot.desired_state == 'restart':
                if proc:
                    self._stop(bot.id)
                bot.pid = None
                bot.desired_state = 'running'
                bot.status = 'queued'
                proc = None
            if bot.desired_state == 'running' and not proc:
                try:
                    self._start(bot)
                except Exception as exc:
                    bot.status = 'error'
                    bot.last_error = str(exc)[:500]
                    bot.pid = None
            elif proc:
                status_path = self._status_path(bot.id)
                try:
                    state = json.loads(status_path.read_text(encoding='utf-8'))
                    if state.get('status') in {'connecting', 'running', 'offline', 'error', 'stopping'}:
                        bot.status = state['status']
                        bot.last_error = state.get('message') if state['status'] == 'error' else None
                except (OSError, ValueError, TypeError):
                    pass
            if bot.started_at:
                started = bot.started_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                bot.uptime_seconds = max(0, int((utcnow() - started).total_seconds()))
        db.session.commit()

    def shutdown(self):
        for bot_id in list(self.children):
            self._stop(bot_id)

def main():
    app = create_agent_app()
    supervisor = Supervisor()
    stopping = False
    def stop_signal(_sig, _frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGINT, stop_signal)
    with app.app_context():
        while not stopping:
            try:
                supervisor.reconcile()
            except Exception as exc:
                print(f'Agent reconciliation error: {exc}', file=sys.stderr, flush=True)
                db.session.rollback()
            time.sleep(POLL_SECONDS)
        supervisor.shutdown()
        for bot in Bot.query.filter(Bot.desired_state == 'running').all():
            bot.status = 'queued'
            bot.pid = None
        db.session.commit()

if __name__ == '__main__':
    main()
