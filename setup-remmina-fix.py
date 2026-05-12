#!/usr/bin/env python3
import os
import sys
import pwd
import subprocess
import hashlib

USER = "jumori"
HOME = f"/home/{USER}"

SYSTEMD_USER_DIR = f"{HOME}/.config/systemd/user"

REM_MINA_SERVICE_NAME = "remmina.service"
REM_MINA_SERVICE_PATH = f"{SYSTEMD_USER_DIR}/{REM_MINA_SERVICE_NAME}"

GUARD_SERVICE_NAME = "remmina-guard.service"
GUARD_SERVICE_PATH = f"{SYSTEMD_USER_DIR}/{GUARD_SERVICE_NAME}"

GUARD_SCRIPT_PATH = "/usr/local/bin/remmina-guard.py"

GUARD_SERVICE_CONTENT = f"""[Unit]
Description=Remmina Keyboard Guard
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {GUARD_SCRIPT_PATH}
Restart=always
RestartSec=2

[Install]
WantedBy=default.target
"""

GUARD_SCRIPT_CONTENT = f"""#!/usr/bin/env python3
import time
import glob
import os

PROFILE_DIR = "{HOME}/.local/share/remmina"

def enforce_settings():
    files = glob.glob(os.path.join(PROFILE_DIR, "*.remmina"))

    for file in files:
        if not os.path.isfile(file):
            continue

        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Força valores desejados
        if "keyboard_grab=0" in content:
            content = content.replace("keyboard_grab=0", "keyboard_grab=1")
        elif "keyboard_grab=" not in content:
            content += "\\nkeyboard_grab=1\\n"

        if "grab_keyboard=" not in content:
            content += "grab_keyboard=1\\n"

        if "no-suppress=" not in content:
            content += "no-suppress=1\\n"

        if content != original_content:
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)

while True:
    enforce_settings()
    time.sleep(5)
"""

def run(cmd, fatal=True):
    print("[CMD]", " ".join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        if p.stderr.strip():
            print("[ERR]", p.stderr.strip())
        if fatal:
            sys.exit(1)
        return False
    return True

def file_changed(path, content):
    if not os.path.exists(path):
        return True
    with open(path, "r", encoding="utf-8") as f:
        current = f.read()
    return current != content

def write_file(path, content, mode=None):
    changed = file_changed(path, content)
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Arquivo atualizado: {path}")
    else:
        print(f"[OK] Arquivo já estava atualizado: {path}")

    if mode is not None:
        os.chmod(path, mode)

def update_remmina_service():
    if not os.path.exists(REM_MINA_SERVICE_PATH):
        print(f"[WARN] Arquivo não encontrado: {REM_MINA_SERVICE_PATH}")
        print("[WARN] Pulando ajuste do remmina.service.")
        return

    with open(REM_MINA_SERVICE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if any("ExecStartPre=/usr/bin/setxkbmap br" in line for line in lines):
        print("[OK] Correção do teclado já existe no remmina.service.")
        return

    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)
        if line.strip() == "[Service]" and not inserted:
            new_lines.append("ExecStartPre=/usr/bin/setxkbmap br\n")
            inserted = True

    if not inserted:
        print("[WARN] Seção [Service] não encontrada no remmina.service. Nenhuma alteração aplicada.")
        return

    with open(REM_MINA_SERVICE_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("[OK] remmina.service atualizado com ExecStartPre=/usr/bin/setxkbmap br")

def ensure_ownership(path, user_owner=True, root_owner=False):
    if user_owner:
        uid = pwd.getpwnam(USER).pw_uid
        gid = pwd.getpwnam(USER).pw_gid
        os.chown(path, uid, gid)
    elif root_owner:
        os.chown(path, 0, 0)

def main():
    if os.geteuid() != 0:
        print("Execute com sudo.")
        sys.exit(1)

    print("[INFO] Criando diretório systemd user...")
    os.makedirs(SYSTEMD_USER_DIR, exist_ok=True)

    print("[INFO] Ajustando remmina.service...")
    update_remmina_service()

    print("[INFO] Criando/atualizando remmina-guard.service...")
    write_file(GUARD_SERVICE_PATH, GUARD_SERVICE_CONTENT)
    ensure_ownership(GUARD_SERVICE_PATH, user_owner=True)

    print("[INFO] Criando/atualizando script remmina-guard.py...")
    write_file(GUARD_SCRIPT_PATH, GUARD_SCRIPT_CONTENT, mode=0o755)
    ensure_ownership(GUARD_SCRIPT_PATH, user_owner=False, root_owner=True)

    print("[INFO] Recarregando systemd do usuário...")
    run(["systemctl", "--user", "--machine", f"{USER}@.host", "daemon-reload"])

    print("[INFO] Habilitando remmina-guard.service...")
    run(["systemctl", "--user", "--machine", f"{USER}@.host", "enable", GUARD_SERVICE_NAME])

    print("[INFO] Reiniciando remmina-guard.service...")
    run(["systemctl", "--user", "--machine", f"{USER}@.host", "restart", GUARD_SERVICE_NAME])

    if os.path.exists(REM_MINA_SERVICE_PATH):
        print("[INFO] Reiniciando remmina.service...")
        run(["systemctl", "--user", "--machine", f"{USER}@.host", "restart", REM_MINA_SERVICE_NAME], fatal=False)

    print("[INFO] Encerrando Remmina para forçar nova autenticação...")
    subprocess.run(["pkill", "-f", "remmina"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[OK] Atualização concluída com sucesso.")

if __name__ == "__main__":
    main()