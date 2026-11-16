# WolkeHost

Minecraft-AFK-Bot-Panel (Flask/SQLite) mit einem separaten Node-0-Agenten (Node.js/Mineflayer). Kein Docker erforderlich.

## Voraussetzungen

- Linux VPS (empfohlen: Ubuntu 24.04), Python 3.11+, Node.js 20+, npm
- Minecraft Java Edition Konto und Server, auf dem Bots erlaubt sind
- Reverse Proxy mit HTTPS für öffentlichen Betrieb

## Installation

```bash
git clone https://github.com/TommyCodet/WolkenHost.git
cd WolkenHost
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
cp .env.example .env
```

Schlüssel erzeugen und in `.env` eintragen:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Setze `BASE_URL` auf deine HTTPS-Domain und `TRUSTED_HOSTS` auf deine Domain plus localhost. Für Microsoft-OIDC trägst du Client-ID und Secret einer korrekt konfigurierten Microsoft-App ein. Niemals Secrets committen.

## Dienste

Panel (hinter Reverse Proxy, nicht direkt öffentlich exponieren):

```bash
.venv/bin/python app.py
```

Node-Agent separat starten:

```bash
sudo cp deploy/wolkehost-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wolkehost-agent
```

Passe in der systemd-Datei Benutzer und Installationspfad an. Lege den Benutzer `wolkehost` an, setze Eigentümerrechte für Projekt und Datenverzeichnis und starte Flask ebenfalls als unprivilegierten Dienst. Beide Prozesse benötigen Zugriff auf dieselbe SQLite-Datenbank; für parallele Nutzung SQLite auf lokalem Datenträger halten.

Admin nach Registrierung vergeben: `python app.py make-admin user@example.com`.

## Minecraft-Authentifizierung – wichtiger Status

Microsoft-OIDC im Panel authentifiziert den Benutzer gegenüber dem Panel und speichert optional dessen Refresh-Token verschlüsselt. Mineflayer verwendet derzeit weiterhin seinen eigenen Microsoft-Device-Login/Auth-Cache. Die OAuth-Refresh-Tokens des Panels werden **noch nicht** in Xbox Live → XSTS → Minecraft Services Tokens umgetauscht und an Mineflayer übergeben. Deshalb ist ein vollständig nahtloser Minecraft-Login im Benutzerpanel noch nicht fertig; der erste Device-Login muss im Agent-/Bot-Auth-Kontext eingerichtet werden. Keine Passwörter speichern und keine Auth-Caches zwischen Benutzern teilen.

## Prozessverwaltung

Der Panel-Prozess schreibt nur den gewünschten Bot-Zustand in die Datenbank. `node_agent.py` überwacht diese Zustände alle fünf Sekunden und startet/stoppt Mineflayer-Prozesse unabhängig von Flask. Ein Agent pro Node; Multi-Node-Registrierung, signierte Agent-Kommunikation und zentrale Node-Zuteilung sind noch nicht implementiert. Der Agent muss mit einem eigenen unprivilegierten Linux-Benutzer laufen.

## Tests

```bash
python -m compileall -q .
python -m unittest discover -s tests
node --check bot.js
python -m json.tool eggs/pterodactyl/egg-wolkehost-afk-bot.json >/dev/null
```

## Vor Produktivbetrieb

Noch erforderlich: Ende-zu-Ende-Test mit echtem Microsoft/Minecraft-Konto, kontrollierte Device-Login-UX, Egress-Firewall gegen DNS-Rebinding/TOCTOU, Prozess-/Ressourcenlimits pro Bot, Laufzeit-/Plan-Abrechnung, Zahlungsanbieter, Node-Registrierung, Backups/Restore, Monitoring und Penetrationstest. Dieses Repository ist ein MVP und keine sicherheitsgeprüfte Hostingplattform.
