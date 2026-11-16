import ipaddress,socket,re
from cryptography.fernet import Fernet,InvalidToken
from config import FERNET_KEY
def _fernet():
 if not FERNET_KEY: raise RuntimeError("FERNET_KEY fehlt. Siehe .env.example.")
 try:return Fernet(FERNET_KEY.encode())
 except Exception as exc:raise RuntimeError("FERNET_KEY ist ungültig.") from exc
def encrypt_secret(value): return _fernet().encrypt(value.encode()).decode()
def decrypt_secret(value):
 try:return _fernet().decrypt(value.encode()).decode()
 except InvalidToken as exc:raise ValueError("Token konnte nicht entschlüsselt werden") from exc
def resolve_public_host(host):
 host=(host or '').strip().rstrip('.')
 if not host or len(host)>253 or any(c.isspace() for c in host) or '/' in host or '\\\\' in host:raise ValueError("Ungültiger Server-Host.")
 try:
  ip=ipaddress.ip_address(host)
  addresses={ip}
 except ValueError:
  try:
   ascii_host=host.encode('idna').decode('ascii')
   if not re.fullmatch(r'(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)(?:\\.(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?))*',ascii_host):raise ValueError("Ungültiger DNS-Name.")
   addresses={ipaddress.ip_address(x[4][0]) for x in socket.getaddrinfo(ascii_host,None,type=socket.SOCK_STREAM)}
   host=ascii_host
  except (socket.gaierror,UnicodeError) as exc:raise ValueError("Server-Host kann nicht sicher aufgelöst werden.") from exc
 if not addresses or any(not ip.is_global for ip in addresses):raise ValueError("Private oder reservierte Server-Adressen sind nicht erlaubt.")
 return host,sorted(str(x) for x in addresses)
def validate_host(host):return resolve_public_host(host)[0]
