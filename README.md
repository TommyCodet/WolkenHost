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
npm ci
cp .env.example .env
```
Schlüssel generieren und in `.env` einsetzen:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Für lokale Entwicklung `BASE_URL=http://127.0.0.1:5000` setzen. Für öffentlichen Betrieb zwingend HTTPS, korrekte `TRUSTED_HOSTS`, Firewall und Reverse Proxy konfigurieren.
```bash
python app.py
```
Admin nach Registrierung explizit über CLI vergeben: `python app.py make-admin user@example.com`. Niemals Adminrechte allein anhand einer frei registrierbaren E-Mail-Adresse vergeben.

## Microsoft/Minecraft
Microsoft OAuth fürs Panel ist optional über Entra-App-Client-ID/Secret einzurichten. Die Microsoft-Identität wird nicht automatisch mit einem bestehenden Passwortkonto anhand der E-Mail verknüpft. Mineflayer verwendet separat seinen Microsoft-Device-Login/Auth-Cache. Die OAuth-Refresh-Tokens des Panel-Logins sind verschlüsselt; die Xbox Live/XSTS/Minecraft-Tokenbroker-Kette zur Wiederverwendung dieses Tokens ist nicht implementiert. Daher nicht behaupten, dass Panel-OAuth die Bot-Anmeldung bereits erledigt.

## Pterodactyl Egg
`eggs/pterodactyl/egg-wolkehost-afk-bot.json` ist das Egg für einen Pterodactyl-Node mit Node.js 20. Die Environment-Variablen sind mit dem Bot-Startcode abgestimmt. Das Flask-Panel ist davon getrennt und nutzt aktuell seinen lokalen VPS-Prozess-Supervisor. Das Egg installiert/started den Mineflayer-Worker; es stellt nicht automatisch eine Pterodactyl-API-Verbindung zum Panel her.

## Sicherheitsgrenzen
CSRF, Session-Cookies, Login-/Registrierungs-Limits, Security-Header, Admin-CLI, Passwort-Hashing, verschlüsselte Refresh-Tokens und Bot-Eigentümerprüfung sind implementiert. Hostnamen werden auf öffentliche IP-Adressen geprüft. DNS-Rebinding/TOCTOU lässt sich mit einer reinen Vorabprüfung nicht vollständig verhindern; für Produktion Netzwerk-Egress-Firewall oder einen kontrollierten Proxy einsetzen. Der lokale Prozess-Supervisor ist Single-Process-MVP, kein Multi-Node-Orchestrator. Vor produktivem Einsatz zusätzlich Reverse-Proxy-Limits, Backups, OS-Isolation pro Bot, Prozess-Reconciliation und echte Microsoft-Xbox-Tokenintegration ergänzen. Kein Filemanager, keine Shell und keine öffentliche Bot-Konsole.
