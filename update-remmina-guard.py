#!/usr/bin/env python3
import subprocess
import os
import pwd
import sys
import time

USER = "jumori"
HOME = f"/home/{USER}"
SYSTEMD_USER_DIR = f"{HOME}/.config/systemd/user"
SERVICE_NAME = "remmina-guard.service"
SERVICE_PATH = f"{SYSTEMD_USER_DIR}/{SERVICE_NAME}"
SCRIPT_PATH = "/usr/local/bin/remmina-guard.py"

SERVICE_CONTENT = f"""[Unit]
Description=Remmina Keyboard Guard
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {SCRIPT_PATH}
Restart=always
RestartSec=2

[Install]
WantedBy=default.target
"""

PYTHON_GUARD_SCRIPT = f"""#!/usr/bin/env python3
import time
import glob
import os

PROFILE_DIR = "{HOME}/.local/share/remmina"

def enforce_settings():
    files = glob.glob(os.path.join(PROFILE_DIR, "*.remmina"))

    for file in files:
        if not os.path.isfile(file):
            continue

        with open(file, "r") as f:
            content = f.read()

        original_content = content

        # Força valores
        if "keyboard_grab=" in content:
            content = content.replace(
                "keyboard_grab=0", "keyboard_grab=1"
            )
        else:
            content += "\\nkeyboard_grab=1\\n"

        if "grab_keyboard=" not in content:
            content += "grab_keyboard=1\\n"

        if "no-suppress=" not in content:
            content += "no-suppress=1\\n"

        # Só grava se houve mudança
        if content != original_content:
            with open(file, "w") as f:
                f.write(content)

while True:
    enforce_settings()
    time.sleep(5)
"""

def run(cmd, fatal=True):
    print("[CMD]", " ".join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        print("[ERR]", p.stderr.decode().strip())
        if fatal:
            sys.exit(1)
        return False
    return True

if os.geteuid() != 0:
    print("Execute com sudo.")
    sys.exit(1)

print("Criando diretório systemd user...")
os.makedirs(SYSTEMD_USER_DIR, exist_ok=True)

print("Criando serviço remmina-guard...")
with open(SERVICE_PATH, "w") as f:
    f.write(SERVICE_CONTENT)

print("Criando script Python guard...")
with open(SCRIPT_PATH, "w") as f:
    f.write(PYTHON_GUARD_SCRIPT)

os.chmod(SCRIPT_PATH, 0o755)

uid = pwd.getpwnam(USER).pw_uid
gid = pwd.getpwnam(USER).pw_gid

os.chown(SERVICE_PATH, uid, gid)
os.chown(SCRIPT_PATH, 0, 0)

print("Recarregando systemd do usuário...")
run(["systemctl", "--user", "--machine", f"{USER}@.host", "daemon-reload"])

print("Habilitando serviço...")
run(["systemctl", "--user", "--machine", f"{USER}@.host", "enable", SERVICE_NAME])

print("Reiniciando serviço...")
run(["systemctl", "--user", "--machine", f"{USER}@.host", "restart", SERVICE_NAME])

print("Encerrando Remmina para forçar nova autenticação...")
subprocess.run(["pkill", "-f", "remmina"])

print("Atualização concluída com sucesso.")

#01) nano update-remmina-guard.py

#02) sudo python3 update-remmina-guard.py