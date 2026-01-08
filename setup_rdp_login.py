#!/usr/bin/env python3
import subprocess
import os
import sys
import time
import pwd
import textwrap

USER = "jumori"
HOME = f"/home/{USER}"
APP_PATH = f"{HOME}/rdp_login.py"
BG_DIR = f"{HOME}/backgrounds"
SERVICE_PATH = "/etc/systemd/system/rdp-login.service"

# ======================
# CORES (SEM ÍCONES)
# ======================
class C:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"

def info(msg):
    print(f"{C.BLUE}[INFO]{C.RESET} {msg}")

def ok(msg):
    print(f"{C.GREEN}[OK]{C.RESET} {msg}")

def warn(msg):
    print(f"{C.YELLOW}[WARN]{C.RESET} {msg}")

def err(msg):
    print(f"{C.RED}[ERRO]{C.RESET} {msg}")

# ======================
# BARRA DE PROGRESSO
# ======================
def progress(title, percent):
    bar_len = 40
    filled = int(bar_len * percent / 100)
    bar = "█" * filled + "-" * (bar_len - filled)
    print(f"\r{C.CYAN}{title:<30} [{bar}] {percent:3d}%{C.RESET}", end="", flush=True)
    if percent == 100:
        print()

# ======================
# EXECUTAR COMANDO
# ======================
def run(cmd, title="", fatal=True):
    info(" ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for i in range(0, 101, 10):
        progress(title, i)
        time.sleep(0.1)
    out, errp = proc.communicate()
    if proc.returncode != 0:
        err(errp.decode().strip())
        if fatal:
            sys.exit(1)
        return False
    progress(title, 100)
    return True

# ======================
# CHECK ROOT
# ======================
if os.geteuid() != 0:
    err("Execute este script com sudo.")
    sys.exit(1)

# ======================
# ATUALIZA SISTEMA
# ======================
info("Atualizando sistema")
run(["apt", "update"], "Atualizando repositórios")
run(["apt", "upgrade", "-y"], "Atualizando pacotes")
ok("Sistema atualizado")

# ======================
# INSTALA PACOTES
# ======================
packages = [
    "python3",
    "python3-tk",
    "python3-pil",
    "python3-pil.imagetk",
    "freerdp2-x11",
    "xorg",
    "x11-xserver-utils",
    "pulseaudio",
    "pulseaudio-utils",
    "fonts-inter"
]

run(["apt", "install", "-y"] + packages, "Instalando dependências")
ok("Dependências instaladas")

# ======================
# BACKGROUNDS
# ======================
info("Configurando backgrounds")
os.makedirs(BG_DIR, exist_ok=True)

uid = pwd.getpwnam(USER).pw_uid
gid = pwd.getpwnam(USER).pw_gid
os.chown(BG_DIR, uid, gid)

files = {
    "leao.jpg": "https://i.ibb.co/XfptybtD/leao.jpg",
    "eye-open.png": "https://i.ibb.co/Dfn03pKc/eye-open.png",
    "eye-closed.png": "https://i.ibb.co/Y7yR0r9f/eye-closed.png",
}

total = len(files)
count = 0

for name, url in files.items():
    count += 1
    progress("Baixando arquivos", int((count - 1) / total * 100))
    subprocess.run(["wget", "-q", "-O", f"{BG_DIR}/{name}", url], check=True)
    os.chown(f"{BG_DIR}/{name}", uid, gid)

progress("Baixando arquivos", 100)
ok("Arquivos baixados")

# ======================
# SYSTEMD SERVICE
# ======================
info("Criando serviço systemd")

service_content = f"""
[Unit]
Description=RDP Login Screen
After=systemd-user-sessions.service network-online.target

[Service]
User={USER}
Environment=DISPLAY=:0
Environment=XAUTHORITY={HOME}/.Xauthority
ExecStart=/usr/bin/startx /usr/bin/python3 {APP_PATH} --
Restart=always
RestartSec=2

[Install]
WantedBy=graphical.target
"""

with open(SERVICE_PATH, "w") as f:
    f.write(textwrap.dedent(service_content))

run(["chmod", "644", SERVICE_PATH], "Permissões do serviço")
run(["systemctl", "daemon-reload"], "Recarregando systemd")
run(["systemctl", "enable", "rdp-login.service"], "Habilitando serviço")

ok("Serviço configurado")

# ======================
# AUTOSTART LXSESSION
# ======================
info("Configurando autostart gráfico")

autostart_dir = f"{HOME}/.config/lxsession/LXDE-pi"
autostart_file = f"{autostart_dir}/autostart"

os.makedirs(autostart_dir, exist_ok=True)

with open(autostart_file, "w") as f:
    f.write(f"@python3 {APP_PATH}\n")

os.chown(autostart_dir, uid, gid)
os.chown(autostart_file, uid, gid)

ok("Autostart configurado")

# ======================
# ATIVAR SSH
# ======================
info("Ativando SSH")
run(["systemctl", "enable", "ssh"], "Habilitando SSH")
run(["systemctl", "start", "ssh"], "Iniciando SSH")
ok("SSH ativo")

# ======================
# ATIVAR VNC
# ======================
info("Ativando VNC")
run(["systemctl", "enable", "vncserver-x11-serviced"], "Habilitando VNC", fatal=False)
run(["systemctl", "start", "vncserver-x11-serviced"], "Iniciando VNC", fatal=False)
ok("VNC ativo")

# ======================
# CONFIGURAR ÁUDIO
# ======================
info("Configurando áudio")

run(["amixer", "set", "Master", "100%"], "Volume em 100%", fatal=False)

# AV JACK = 2 (se existir)
result = subprocess.run(
    ["amixer", "cset", "numid=3", "2"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

if result.returncode == 0:
    ok("Saída de áudio definida para AV JACK")
else:
    warn("AV JACK não disponível, mantendo saída padrão")

# ======================
# CONFIGURAR TECLADO
# ======================
info("Configurando teclado pt-BR")

run(["localectl", "set-keymap", "br"], "Keymap console")
run(["localectl", "set-x11-keymap", "br"], "Keymap X11")

ok("Teclado configurado para pt-BR")

# ======================
# FINAL
# ======================
print()
ok("Setup concluído com sucesso")
info("Reinicie o sistema para aplicar tudo:")
print(f"{C.YELLOW}sudo reboot{C.RESET}")
