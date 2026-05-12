import subprocess
import os
import sys
import re

# Cores para o terminal
VERDE = '\033[92m'
AMARELO = '\033[93m'
VERMELHO = '\033[91m'
RESET = '\033[0m'
NEGRITO = '\033[1m'

CONFIG_PATH = "/boot/firmware/config.txt"

def get_current_res():
    try:
        # Pega a linha inteira que tem o asterisco
        cmd = "xrandr | grep '*'"
        output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        
        # Usa Regex para encontrar o padrao de numeros (ex: 1360x768 ou 1366x768)
        match = re.search(r'\d{3,4}x\d{3,4}', output)
        if match:
            return match.group(0)
        
        # Se nao achou no grep '*', tenta pegar da segunda linha do xrandr (current)
        cmd_alt = "xrandr | grep 'current' | awk -F'current' '{print $2}' | awk -F',' '{print $1}'"
        res_alt = subprocess.check_output(cmd_alt, shell=True).decode('utf-8').strip()
        return res_alt
    except:
        return "Nao detectada"

def update_config_file():
    print(f"{AMARELO}Iniciando modificacao do {CONFIG_PATH}...{RESET}")
    
    if os.geteuid() != 0:
        print(f"{VERMELHO}Erro: Este script precisa de privilegios de ROOT (sudo).{RESET}")
        return False

    with open(CONFIG_PATH, 'r') as f:
        linhas = f.readlines()

    novas_linhas = []
    modificado = False

    settings = [
        "hdmi_force_hotplug=1\n",
        "hdmi_group=2\n",
        "hdmi_mode=87\n",
        "hdmi_cvt=1366 768 60 6 0 0 0\n",
        "hdmi_drive=2\n"
    ]

    for linha in linhas:
        if "dtoverlay=vc4-kms-v3d" in linha and not linha.startswith("#"):
            novas_linhas.append("dtoverlay=vc4-fkms-v3d\n")
            print(f"{VERDE}Driver alterado de KMS para FKMS.{RESET}")
            modificado = True
        else:
            novas_linhas.append(linha)

    for setting in settings:
        if setting not in novas_linhas:
            novas_linhas.append(setting)
            modificado = True

    if modificado:
        with open(CONFIG_PATH, 'w') as f:
            f.writelines(novas_linhas)
        print(f"{VERDE}{NEGRITO}Arquivo config.txt atualizado com sucesso!{RESET}")
        return True
    else:
        print(f"{AMARELO}As configuracoes ja estavam aplicadas no arquivo.{RESET}")
        return False

def main():
    print(f"\n{NEGRITO}--- Verificador de Resolucao Raspberry Pi 4 ---{RESET}\n")
    
    res_atual = get_current_res()
    print(f"Resolucao detectada pelo sistema: {NEGRITO}{res_atual}{RESET}")

    # Verifica se a resolucao contem 1360 ou 1366
    if "1366" in res_atual or "1360" in res_atual:
        print(f"{VERDE}Sucesso! A resolucao {res_atual} ja esta ativa.{RESET}\n")
    else:
        print(f"{AMARELO}Resolucao atual ({res_atual}) diferente do objetivo (1366x768).{RESET}")
        if update_config_file():
            print(f"\n{VERMELHO}{NEGRITO}Reinicie para aplicar as mudancas.{RESET}")
            if input("Reiniciar agora? (s/n): ").lower() == 's':
                os.system("sudo reboot")
        else:
            print(f"{AMARELO}Arquivo ja configurado, mas a resolucao ainda nao mudou.{RESET}")
            print(f"Dica: Tente rodar 'xrandr --output HDMI-1 --mode 1366x768_60.00' se disponivel.")

if __name__ == "__main__":
    main()

#nano ~/ajustar_resolucao.py
#chmod +x ~/ajustar_resolucao.py;sudo python ~/ajustar_resolucao.py
"""
sudo nano /boot/firmware/config.txt

DE dtoverlay=vc4-kms-v3d PARA dtoverlay=vc4-fkms-v3d

hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1366 768 60 6 0 0 0
hdmi_drive=2
"""