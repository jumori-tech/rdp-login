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
# EXECUTAR COMANDO (CORRIGIDA E TESTADA)
# ======================
def run(cmd, fatal=True, target_user=None):
    """Executa comandos. Se target_user for definido, usa machinectl para o barramento do usuário."""
    final_cmd = cmd
    if target_user and "systemctl" in cmd:
        # Formato correto para gerenciar serviços de usuário via SUDO
        user_args = ["systemctl", "--user", f"--machine={target_user}@.host"]
        remaining_args = [c for c in cmd if c not in ["systemctl", "--user"]]
        final_cmd = user_args + remaining_args
    
    info(" ".join(final_cmd))
    proc = subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if proc.returncode != 0:
        error_msg = proc.stderr.decode().strip()
        err(error_msg)
        if fatal:
            sys.exit(1)
        return False
    return True

# ======================
# INÍCIO DO SETUP
# ======================
if os.geteuid() != 0:
    err("Execute este script com sudo.")
    sys.exit(1)

# 1. SISTEMA (X11, IDIOMA E AUTO-LOGIN)
# ----------------------
info("Configurando Sistema: X11, PT-BR e Auto-Login")
# Força X11
run(["raspi-config", "nonint", "do_wayland", "W1"])
# Define Idioma
run(["raspi-config", "nonint", "do_change_locale", "pt_BR.UTF-8"])
# Ativa Auto-login no Desktop (ESSENCIAL PARA O REMMINA ABRIR)
run(["raspi-config", "nonint", "do_boot_behaviour", "B4"])
# Define País do Wi-fi
run(["raspi-config", "nonint", "do_wifi_country", "BR"], fatal=False)

# 2. ATUALIZAÇÃO E INSTALAÇÃO
# ----------------------
run(["apt", "update"])
run(["apt", "upgrade", "-y"])
run(["apt", "install", "-y", "remmina", "remmina-plugin-rdp", "remmina-plugin-secret", "freerdp3-x11"])

# 3. CONFIGURAÇÃO DO SERVIÇO
# ----------------------
info(f"Criando serviço de usuário para {USER}")
run(["loginctl", "enable-linger", USER])

os.makedirs(SYSTEMD_USER_DIR, exist_ok=True)

# O segredo do Remmina abrir é o After=graphical-session.target e o Environment DISPLAY
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

# Corrigir permissões da pasta de config
uid = pwd.getpwnam(USER).pw_uid
gid = pwd.getpwnam(USER).pw_gid
for root, dirs, files in os.walk(f"{HOME}/.config"):
    for d in dirs: os.chown(os.path.join(root, d), uid, gid)
    for f in files: os.chown(os.path.join(root, f), uid, gid)

# 4. COMANDOS SYSTEMD (USANDO target_user CORRETAMENTE)
# ----------------------
info("Habilitando serviço de usuário...")
run(["systemctl", "--user", "daemon-reexec"], target_user=USER)
run(["systemctl", "--user", "daemon-reload"], target_user=USER)
run(["systemctl", "--user", "enable", SERVICE_NAME], target_user=USER)
# Restart aqui pode dar erro pois o X11 ainda não reiniciou, então fatal=False
run(["systemctl", "--user", "restart", SERVICE_NAME], target_user=USER, fatal=False)

# 5. EXTRAS
# ----------------------
run(["systemctl", "enable", "ssh"], fatal=False)
run(["systemctl", "enable", "vncserver-x11-serviced"], fatal=False)

print("\n" + "="*40)
ok("SETUP CONCLUÍDO!")
warn("VOCÊ PRECISA REINICIAR AGORA PARA O X11 E O REMMINA FUNCIONAREM.")
print(f"{C.YELLOW}sudo reboot{C.RESET}")
print("="*40)

