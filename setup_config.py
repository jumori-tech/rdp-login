#!/usr/bin/env python3
import subprocess
import os
import sys
import pwd

# ======================
# CONFIGURAÇÕES
# ======================
USER = "jumori"
HOME = f"/home/{USER}"
SERVICE_NAME = "remmina.service"
SYSTEMD_USER_DIR = f"{HOME}/.config/systemd/user"
WALLPAPER_URL = "https://i.ibb.co/XfptybtD/leao.jpg"
WALLPAPER_PATH = f"{HOME}/leao.jpg"

# ======================
# CORES
# ======================
class C:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"

def info(msg): print(f"{C.BLUE}[INFO]{C.RESET} {msg}")
def ok(msg): print(f"{C.GREEN}[OK]{C.RESET} {msg}")
def warn(msg): print(f"{C.YELLOW}[WARN]{C.RESET} {msg}")
def err(msg): print(f"{C.RED}[ERRO]{C.RESET} {msg}")

# ======================
# EXECUTAR COMANDO
# ======================
def run(cmd, fatal=True, target_user=None):
    final_cmd = cmd

    if target_user and "systemctl" in cmd:
        user_args = ["systemctl", "--user", f"--machine={target_user}@.host"]
        remaining_args = [c for c in cmd if c not in ["systemctl", "--user"]]
        final_cmd = user_args + remaining_args

    info(" ".join(final_cmd))

    proc = subprocess.Popen(final_cmd)

    proc.wait()

    if proc.returncode != 0:
        err(f"Comando falhou com código {proc.returncode}")
        if fatal:
            sys.exit(1)
        return False
    return True

# ======================
# DETECTAR RASPBERRY PI 4
# ======================
def is_rpi4():
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read()
            return "Raspberry Pi 4" in model
    except:
        return False

# ======================
# INÍCIO DO SETUP
# ======================
if os.geteuid() != 0:
    err("Execute este script com sudo.")
    sys.exit(1)

# 1. SISTEMA
info("Configurando Sistema: X11, PT-BR e Auto-Login")
run(["raspi-config", "nonint", "do_wayland", "W1"])
run(["raspi-config", "nonint", "do_change_locale", "pt_BR.UTF-8"])
run(["raspi-config", "nonint", "do_boot_behaviour", "B4"])
run(["raspi-config", "nonint", "do_wifi_country", "BR"], fatal=False)

# 2. ATUALIZAÇÃO
run(["apt", "update"])
run(["apt", "upgrade", "-y"])
run(["apt", "install", "-y", "remmina", "remmina-plugin-rdp", "remmina-plugin-secret", "freerdp3-x11", "wget"])

# 3. SE FOR RPI 4 → AJUSTAR RESOLUÇÃO
if is_rpi4():
    info("Raspberry Pi 4 detectada. Ajustando resolução...")
    run(["wget", "-q",
         "https://raw.githubusercontent.com/JumoriAutoPecas/rdp-login/refs/heads/main/ajustar_resolucao.py",
         "-O", f"{HOME}/ajustar_resolucao.py"])
    run(["bash", "-c", f"echo n | sudo python3 {HOME}/ajustar_resolucao.py"], fatal=False)
    ok("Resolução ajustada para Raspberry Pi 4")
else:
    warn("Não é uma Raspberry Pi 4. Pulando ajuste de resolução.")

# 4. WALLPAPER
info("Baixando wallpaper...")
run(["wget", "-q", WALLPAPER_URL, "-O", WALLPAPER_PATH])

ok("EXECUTE: ===>   pcmanfm --set-wallpaper /home/jumori/leao.jpg")

# 5. CONFIGURAÇÃO DO SERVIÇO
# Corrigir permissões
uid = pwd.getpwnam(USER).pw_uid
gid = pwd.getpwnam(USER).pw_gid

for root, dirs, files in os.walk(f"{HOME}/.config"):
    for d in dirs:
        os.chown(os.path.join(root, d), uid, gid)
    for f_name in files:
        os.chown(os.path.join(root, f_name), uid, gid)

info(f"Criando serviço de usuário para {USER}")
run(["loginctl", "enable-linger", USER])

os.makedirs(SYSTEMD_USER_DIR, exist_ok=True)

SERVICE_CONTENT = f"""[Unit]
Description=Remmina Kiosk
After=graphical-session.target
Wants=graphical-session.target

[Service]
ExecStartPre=/usr/bin/setxkbmap br
Type=simple
ExecStart=/usr/bin/remmina
Restart=always
RestartSec=1
Environment=DISPLAY=:0
Environment=XAUTHORITY={HOME}/.Xauthority

[Install]
WantedBy=default.target
"""

service_path = os.path.join(SYSTEMD_USER_DIR, SERVICE_NAME)
with open(service_path, "w") as f:
    f.write(SERVICE_CONTENT)

# Corrigir permissões
for root, dirs, files in os.walk(f"{HOME}/.config"):
    for d in dirs:
        os.chown(os.path.join(root, d), uid, gid)
    for f_name in files:
        os.chown(os.path.join(root, f_name), uid, gid)

# 6. SYSTEMD USER
info("Habilitando serviço de usuário...")
run(["systemctl", "--user", "daemon-reexec"], target_user=USER)
run(["systemctl", "--user", "daemon-reload"], target_user=USER)
run(["systemctl", "--user", "enable", SERVICE_NAME], target_user=USER)
run(["systemctl", "--user", "restart", SERVICE_NAME], target_user=USER, fatal=False)

# 7. EXTRAS
run(["systemctl", "enable", "ssh"], fatal=False)
run(["systemctl", "enable", "vncserver-x11-serviced"], fatal=False)

print("\n" + "="*40)
ok("SETUP CONCLUÍDO!")
warn("VOCÊ PRECISA REINICIAR AGORA PARA O X11 E O REMMINA FUNCIONAREM.")
print(f"{C.YELLOW}sudo reboot{C.RESET}")
print("="*40)
