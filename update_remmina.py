import os

# Caminho para o serviço do usuário
service_path = os.path.expanduser("~/.config/systemd/user/remmina.service")

def update_remmina_service():
    if not os.path.exists(service_path):
        print(f"Erro: O arquivo {service_path} não foi encontrado.")
        return

    with open(service_path, 'r') as f:
        lines = f.readlines()

    # Verifica se a correção já existe para evitar duplicidade
    if any("setxkbmap br" in line for line in lines):
        print("A correção já está aplicada no arquivo de serviço.")
        return

    new_lines = []
    found_service_section = False
    applied = False

    for line in lines:
        new_lines.append(line)
        # Procura o início da seção [Service]
        if "[Service]" in line:
            found_service_section = True
        
        # Insere a linha logo após o cabeçalho [Service]
        if found_service_section and not applied:
            new_lines.append("ExecStartPre=/usr/bin/setxkbmap br\n")
            applied = True

    with open(service_path, 'w') as f:
        f.writelines(new_lines)
    
    print("Serviço atualizado com sucesso!")
    
    # Recarrega o systemd e reinicia o serviço
    print("Recarregando configurações do systemd...")
    os.system("systemctl --user daemon-reload")
    os.system("systemctl --user restart remmina.service")
    print("Serviço reiniciado. Teste o teclado agora.")

if __name__ == "__main__":
    update_remmina_service()