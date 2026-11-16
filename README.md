# WolkeHost
Minecraft AFK Bot Panel mit Flask/SQLite und Node.js/Mineflayer.

## Lokaler VPS-Betrieb
Voraussetzungen: Python 3.11+, Node.js 20+, npm, Minecraft Java Konto.
```bash
git clone https://github.com/TommyCodet/WolkenHost.git
cd WolkenHost
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
cp .env.example .env
```
Schlüssel generieren und in `.env` einsetzen:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Für lokale Entwicklung `BASE_URL=http://127.0.0.1:5000` setzen. Für öffentlichen Betrieb HTTPS, korrekte `TRUSTED_HOSTS`, Firewall und Reverse Proxy konfigurieren.
```bash
python app.py
```
Admin nach Registrierung explizit vergeben: `python app.py make-admin user@example.com`.

## Pterodactyl Egg
Importiere `eggs/pterodactyl/egg-wolkehost-afk-bot.json` unter Admin → Nests → Eggs → Import Egg. Das Egg liest exakt `SERVER_HOST`, `SERVER_PORT`, `MC_VERSION`, `AFK_ENABLED`, `AFK_COMMAND`, `AUTO_RECONNECT` und `RECONNECT_DELAY`. Dieselben Einstellungen werden vom lokalen Worker an `bot.js` übergeben. Tests: `python -m unittest discover -s tests`.

## Microsoft/Minecraft
Microsoft OAuth fürs Panel ist optional über Entra-App-Client-ID/Secret einzurichten. Ein Microsoft-Login wird nicht automatisch anhand einer E-Mail mit einem bestehenden Passwortkonto verknüpft. Mineflayer verwendet separat seinen Microsoft-Device-Login/Auth-Cache. Panel-OAuth-Refresh-Tokens sind verschlüsselt; die Xbox Live/XSTS/Minecraft-Tokenbroker-Kette zur Wiederverwendung dieses Tokens ist nicht implementiert.

## Sicherheitsgrenzen
CSRF, Session-Cookies, Login-/Registrierungs-Limits, Security-Header, Admin-CLI, Passwort-Hashing, verschlüsselte Refresh-Tokens und Bot-Eigentümerprüfung sind implementiert. Hostnamen werden auf öffentliche IP-Adressen geprüft. DNS-Rebinding/TOCTOU kann eine Vorabprüfung nicht vollständig verhindern; für Produktion Netzwerk-Egress-Firewall oder kontrollierten Proxy einsetzen. Der lokale Prozess-Supervisor ist ein Single-Process-MVP, kein Multi-Node-Orchestrator. Vor öffentlichem Produktivbetrieb zusätzlich Reverse-Proxy-Limits, Backups, OS-Isolation pro Bot, Prozess-Reconciliation und echte Microsoft-Xbox-Tokenintegration ergänzen.
