# app/client.py
import socket
import threading
from app.config import CONFIG
from app.crypto import fernet, encrypt, decrypt

FERNET_OBJ = fernet(CONFIG.PASSPHRASE)


def receive(sock):
    while True:
        data = sock.recv(8192)
        if not data:
            print("[-] Server closed the connection.")
            break
        msg = decrypt(FERNET_OBJ, data)
        if msg:
            print(msg)


def send(sock):
    while True:
        try:
            text = input()
        except EOFError:
            break
        sock.sendall(encrypt(FERNET_OBJ, text))
        if text.strip().lower() == "bye":
            break


def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_host = "127.0.0.1" if CONFIG.HOST == "0.0.0.0" else CONFIG.HOST
    sock.connect((connect_host, CONFIG.PORT))
    print(f"[+] Connected to {connect_host}:{CONFIG.PORT}")

    username = input("Choose a username: ").strip() or "anon"
    sock.sendall(encrypt(FERNET_OBJ, f"AUTH {username}"))

    welcome = sock.recv(4096)
    print(decrypt(FERNET_OBJ, welcome))

    threading.Thread(target=receive, args=(sock,), daemon=True).start()
    send(sock)
    sock.close()


if __name__ == "__main__":
    start_client()
