# app/server.py
import socket
import threading
import logging
import os
import time

from app.config import CONFIG
from app.crypto import fernet, decrypt, encrypt
from app.ids import check_rate, is_suspicious, clear_rate_bucket

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "security.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

clients = {}  # sock -> (username, addr)
FERNET = fernet(CONFIG.PASSPHRASE)


def broadcast(sender_sock, message: str):
    for sock in list(clients.keys()):
        if sock is sender_sock:
            continue
        try:
            sock.sendall(encrypt(FERNET, message))
        except Exception:
            logging.exception("Failed to send to a client; removing socket")
            try:
                sock.close()
            except Exception:
                pass
            clients.pop(sock, None)


def handle_client(sock, addr):
    username = None
    try:
        first = sock.recv(4096)
        if not first:
            sock.close()
            return
        plaintext = decrypt(FERNET, first)
        if not plaintext or not plaintext.startswith("AUTH "):
            sock.close()
            return

        username = plaintext[5:].strip() or f"user_{addr[1]}"
        clients[sock] = (username, addr)
        logging.info(f"{username}@{addr} joined")
        broadcast(sock, f"🔐 {username} joined the chat")
        try:
            sock.sendall(encrypt(FERNET, f"Welcome, {username}!"))
        except Exception:
            logging.exception("Failed to send welcome message")

        while True:
            data = sock.recv(8192)
            if not data:
                break
            msg = decrypt(FERNET, data)
            if msg is None:
                break
            if msg.strip().lower() == "bye":
                break
            if not check_rate(addr):
                try:
                    sock.sendall(encrypt(FERNET, "[SERVER] Rate limit exceeded. Disconnecting."))
                except Exception:
                    logging.exception("Failed sending rate-limit message")
                break
            if is_suspicious(msg) and CONFIG.KICK_ON_SUSPICIOUS:
                try:
                    sock.sendall(encrypt(FERNET, "[SERVER] Suspicious content detected. Disconnecting."))
                except Exception:
                    logging.exception("Failed sending suspicious-content message")
                break

            logging.info(f"{username}@{addr}: {msg}")
            broadcast(sock, f"{username}: {msg}")

    except Exception:
        logging.exception("Unhandled exception in client handler")
    finally:
        clients.pop(sock, None)
        clear_rate_bucket(addr)
        try:
            sock.close()
        except Exception:
            pass
        if username:
            logging.info(f"{username}@{addr} disconnected")
            broadcast(None, f"🔒 {username} left the chat")


def server_input():
    """Lets the operator type messages at the server console to broadcast
    to everyone, prefixed [SERVER].

    FIX: the previous version wrapped `input()` in `while True: try/except
    Exception: logging.exception(...)` with NOTHING to stop it from
    spinning. If stdin isn't an interactive terminal (no console attached,
    started as a background/service process, IDE run without a terminal),
    `input()` raises EOFError on every single call — forever, with zero
    delay — which is exactly what produced the 4.2GB security.log. Now:
    a short backoff on error, and the thread exits cleanly after repeated
    EOFErrors instead of looping forever.
    """
    consecutive_errors = 0
    while True:
        try:
            msg = input("")
            consecutive_errors = 0
            if msg.strip():
                broadcast(None, f"[SERVER]: {msg}")
                logging.info(f"Server broadcast: {msg}")
        except EOFError:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                logging.info("No interactive stdin available; server console input disabled.")
                return
            time.sleep(1)
        except Exception:
            logging.exception("Error in server input")
            time.sleep(1)


def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((CONFIG.HOST, CONFIG.PORT))
    server_sock.listen(10)
    print(f"Server listening on {CONFIG.HOST}:{CONFIG.PORT}")
    print("Type messages and press Enter to broadcast from the server.")

    threading.Thread(target=server_input, daemon=True).start()

    try:
        while True:
            client_sock, addr = server_sock.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_server()
