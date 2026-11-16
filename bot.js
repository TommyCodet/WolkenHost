const mineflayer = require('mineflayer');
const fs = require('fs');
const path = require('path');

const configPath = process.argv[2];
let cfg;
if (configPath) {
  cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
} else {
  if (!process.env.SERVER_HOST) throw new Error('Missing SERVER_HOST');
  cfg = {
    serverHost: process.env.SERVER_HOST,
    serverPort: Number(process.env.SERVER_PORT || 25565),
    mcVersion: process.env.MC_VERSION || 'auto',
    afkEnabled: /^(1|true|yes|on)$/i.test(process.env.AFK_ENABLED || 'true'),
    afkCommand: process.env.AFK_COMMAND || '/afk on',
    autoReconnect: /^(1|true|yes|on)$/i.test(process.env.AUTO_RECONNECT || 'true'),
    reconnectDelay: Number(process.env.RECONNECT_DELAY || 10)
  };
}
const host = String(cfg.serverHost || '');
const port = Number(cfg.serverPort || 25565);
const version = !cfg.mcVersion || cfg.mcVersion === 'auto' ? false : cfg.mcVersion;
const delay = Math.min(300, Math.max(5, Number(cfg.reconnectDelay || 10))) * 1000;
if (!host || !Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid Minecraft server host/port');
if (!['auto', '1.21.1', '1.20.4', '1.19.4'].includes(cfg.mcVersion || 'auto')) throw new Error('Unsupported Minecraft version');

const statusFile = process.env.WOLKEHOST_STATUS_FILE;
function setStatus(status, message) {
  const data = { status, message: String(message || '').slice(0, 300), updatedAt: new Date().toISOString() };
  if (statusFile) {
    const tmp = statusFile + '.tmp';
    try { fs.writeFileSync(tmp, JSON.stringify(data), { mode: 0o600 }); fs.renameSync(tmp, statusFile); } catch (err) { console.error('Could not update status file:', err.message); }
  }
  console.log('[WOLKEHOST_STATUS]', JSON.stringify(data));
}

let bot;
let stopping = false;
let timer;
let startupTimers = [];
function connect() {
  if (stopping) return;
  setStatus('connecting', 'Verbindung zum Minecraft-Server wird hergestellt');
  console.log('Connecting to Minecraft server...');
  bot = mineflayer.createBot({ host, port, username: 'WolkeHost', auth: 'microsoft', version });
  bot.once('login', () => {
    setStatus('running', 'Minecraft-Anmeldung erfolgreich');
    console.log('Minecraft login event received');
    const commands = Array.isArray(cfg.startupCommands) ? cfg.startupCommands :
      (cfg.afkEnabled && cfg.afkCommand ? [cfg.afkCommand] : []);
    commands.slice(0, 10).forEach((command, index) => {
      const message = String(command || '').trim();
      if (!message || message.length > 100 || /[\\x00-\\x1f]/.test(message)) return;
      const timerId = setTimeout(() => {
        if (!stopping && bot && bot.player) {
          try { bot.chat(message); console.log('Sent startup command #' + (index + 1)); }
          catch (error) { console.error('Startup command failed:', error.message); }
        }
      }, 2500 + index * 1500);
      startupTimers.push(timerId);
    });
  });
  bot.on('kicked', reason => {
    const message = String(reason).slice(0, 300);
    setStatus('offline', 'Vom Server getrennt: ' + message);
    console.log('Disconnected by server:', message);
  });
  bot.on('error', error => {
    setStatus('error', error.message);
    console.error('Minecraft connection error:', error.message);
  });
  bot.once('end', () => {
    startupTimers.forEach(clearTimeout);
    startupTimers = [];
    setStatus('offline', 'Verbindung beendet');
    console.log('Connection ended');
    if (!stopping && cfg.autoReconnect) timer = setTimeout(connect, delay);
  });
}
function shutdown() {
  if (stopping) return;
  stopping = true;
  clearTimeout(timer);
  startupTimers.forEach(clearTimeout);
  startupTimers = [];
  setStatus('stopping', 'Bot wird beendet');
  if (bot) { try { bot.quit('WolkeHost stopping'); } catch (_) {} }
  setTimeout(() => process.exit(0), 700).unref();
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
connect();
