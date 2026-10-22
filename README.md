# Secure Multi-Client Chat 

A multi-client, passphrase-authenticated chat system in Python. Messages are
encrypted with Fernet (AES-128-CBC + HMAC-SHA256), key derived from a shared
passphrase via PBKDF2-HMAC-SHA256. Includes basic IDS (rate limiting +
suspicious-content detection), security logging, and an admin CLI for user
role management.

## Features
- Multi-client threaded TCP server
- End-to-end Fernet encryption, PBKDF2-derived key
- Username authentication handshake
- Rate limiting per client (messages per time window)
- Suspicious-content detection (SQLi/XSS/shell-command patterns) — always logged
- Server-side console broadcast (type at the server to message all clients)
- Admin CLI: create/delete/update/search/export users (JSON-backed, CSV export)
- Security event logging to `logs/security.log`

## Requirements
Python 3.10+
```bash
pip install -r requirements.txt
```

## Run

```bash
# Server (auto-generates .env with random passphrase + salt on first run)
python -m app.server

# Client (separate terminal)
python -m app.client
```

Enter a username when prompted — this sends the `AUTH <username>` handshake
the server requires. Type `bye` to disconnect.

Type directly into the server's terminal to broadcast a `[SERVER]:` message
to everyone connected.

## Admin CLI

```bash
python -m app.admin_cli create-user --username alice --role admin
python -m app.admin_cli list-users
python -m app.admin_cli search-user --query admin
python -m app.admin_cli update-user --username alice --role user
python -m app.admin_cli delete-user --username alice
python -m app.admin_cli export-users --file users.csv
```

## Sharing the passphrase between machines
`.env` (containing `FERNET_PASSPHRASE` and `CHAT_SALT_B64`) is generated on
first run and is git-ignored. Copy it to any other machine that needs to
connect — out-of-band, never via git — so client and server derive the
same encryption key.

## Project Structure
```
app/
├── __init__.py
├── config.py      # Loads/generates passphrase & salt from .env
├── crypto.py      # PBKDF2 key derivation + Fernet encrypt/decrypt
├── ids.py         # Rate limiting + suspicious-content detection
├── server.py       # Threaded multi-client server
├── client.py        # CLI chat client
└── admin_cli.py      # User management (create/delete/list/search/export)
requirements.txt
.gitignore
```

## Bugs found and fixed in this final version
1. **4.2GB runaway log file** — `server_input()` caught `EOFError` from
   `input()` in an infinite loop with no delay. If stdin isn't an
   interactive terminal (no console attached, run as a background
   process), `input()` fails instantly and forever, logging a line every
   time. Fixed: backoff delay + the thread shuts itself off after 3
   consecutive EOFErrors instead of spinning.
2. **Hardcoded passphrase & salt in source code** (`"changeme"` passphrase,
   a static `SALT` byte literal) — committed secrets defeat the purpose of
   having them. Fixed: both are generated once and stored in a git-ignored
   `.env`.
3. **Client never sent the AUTH handshake** in an earlier version of this
   project — the server requires the first message to start with
   `"AUTH "`, but the client just went straight to chatting. Fixed: client
   now prompts for a username and sends `AUTH <username>` first.
4. **`if __name__ == "__main_":`** typo (missing underscore) in an earlier
   client — meant `python -m app.client` silently did nothing. Fixed.
5. **Suspicious-content detection was silent** unless `KICK_ON_SUSPICIOUS`
   was `True` (default `False`) — meant the IDS feature logged nothing by
   default. Fixed: every match is now logged regardless of whether the
   client gets kicked.
6. **`UnboundLocalError` risk** — an earlier version's `finally` block
   referenced `username` even when auth failed before it was assigned.
   Fixed: `username` is always initialized before any code path that
   reaches `finally`.
