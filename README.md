# WolkeHost
Modernes Minecraft-AFK-Panel (Flask, SQLite, Mineflayer).

## Voraussetzungen
Python 3.11+, Node.js 20+, Minecraft-Java-Konto.
## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
cp .env.example .env
```
Schlüssel generieren:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Beide Werte in `.env` eintragen; `ADMIN_EMAILS` auf die Admin-E-Mail setzen.
## Start
```bash
python app.py
```
Dann http://127.0.0.1:5000 öffnen. Registrierung mit einer Admin-E-Mail aus `ADMIN_EMAILS` weist Adminrechte zu.

## Microsoft/Minecraft-Authentifizierung
Der Microsoft-OAuth-Button authentifiziert beim Panel und verschlüsselt einen gelieferten OAuth-Refresh-Token. **Die Weitergabe dieses Tokens an Xbox Live, XSTS und Minecraft Services ist noch nicht integriert.** Mineflayer nutzt derzeit seinen eigenen Microsoft-Device-Login und Auth-Cache. Das ist ein MVP-Gerüst, kein vollständig fertiges öffentliches Hostingprodukt. Es werden keine Microsoft-Passwörter gespeichert.

## Betriebsgrenzen
CSRF-Schutz, Passwort-Hashing, Session-Cookies, Rate-Limits und Bot-Eigentümerprüfung sind aktiv. Private/reservierte Server-IP-Adressen werden beim Anlegen blockiert; vor Produktivbetrieb DNS-Rebinding-Schutz beim Connect und Egress-Firewall ergänzen. Der Prozess-Supervisor ist für einen Flask-Prozess auf einem VPS gedacht; für mehrere Webworker/externe Nodes ist ein separater authentifizierter Node-Agent erforderlich. Abrechnung, Planablauf, Laufzeit-Automatik, Node-Metriken und externe Nodes sind noch nicht implementiert. Keine Web-Konsole/Dateiverwaltung. Öffentlich nur mit HTTPS und starken Schlüsseln betreiben.
