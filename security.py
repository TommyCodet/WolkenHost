import ipaddress,socket
from cryptography.fernet import Fernet,InvalidToken
from config import FERNET_KEY
def _fernet():
 if not FERNET_KEY: raise RuntimeError("FERNET_KEY fehlt. Siehe .env.example.")
 return Fernet(FERNET_KEY.encode())
def encrypt_secret(value): return _fernet().encrypt(value.encode()).decode()
def decrypt_secret(value):
 try: return _fernet().decrypt(value.encode()).decode()
 except InvalidToken as exc: raise ValueError("Token konnte nicht entschlüsselt werden") from exc
def validate_host(host):
 host=(host or '').strip().rstrip('.')
 if not host or len(host)>253 or any(c.isspace() for c in host): raise ValueError("Ungültiger Server-Host.")
 try: addresses={ipaddress.ip_address(host)}
 except ValueError:
  try: addresses={ipaddress.ip_address(x[4][0]) for x in socket.getaddrinfo(host,None)}
  except socket.gaierror as exc: raise ValueError("Server-Host kann nicht aufgelöst werden.") from exc
 if not addresses or any(not ip.is_global for ip in addresses): raise ValueError("Private oder reservierte Server-Adressen sind nicht erlaubt.")
 return host
