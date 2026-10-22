# app/config.py
import os
import base64
import secrets
from dataclasses import dataclass, field
from dotenv import load_dotenv

ENV_PATH = ".env"


def _ensure_env_file():
    """Auto-generate a .env with a random passphrase + salt on first run,
    so no secret ever has to live in source code (fixes the hardcoded
    SALT / 'changeme' passphrase from the earlier version)."""
    if os.path.exists(ENV_PATH):
        return
    passphrase = secrets.token_urlsafe(24)
    salt_b64 = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode()
    with open(ENV_PATH, "w") as f:
        f.write(f"FERNET_PASSPHRASE={passphrase}\n")
        f.write(f"CHAT_SALT_B64={salt_b64}\n")
    print(f"[+] Generated new .env with a random passphrase + salt at {ENV_PATH}")
    print("[+] Share this .env file out-of-band (never via git) with anyone who needs to connect.")


_ensure_env_file()
load_dotenv(ENV_PATH)


@dataclass
class Config:
    HOST: str = "0.0.0.0"
    PORT: int = 12345

    PASSPHRASE: str = os.environ.get("FERNET_PASSPHRASE", "")
    SALT: bytes = base64.urlsafe_b64decode(os.environ["CHAT_SALT_B64"])
    KDF_ITERATIONS: int = 390_000

    WINDOW_SECONDS: int = 10
    MAX_MSG_PER_WINDOW: int = 15

    SUSPICIOUS_TERMS: list = field(default_factory=lambda: [
        "<script>", "</script>", "union select", " or 1=1", "drop table",
        "xp_cmdshell", ";--", "-- ", " rm -rf ", "wget http://",
        "curl http://", "powershell -enc",
    ])

    KICK_ON_SUSPICIOUS: bool = False
    USER_FILE: str = "users.json"


CONFIG = Config()
