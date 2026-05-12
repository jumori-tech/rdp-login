Wallpaper: https://i.ibb.co/XfptybtD/leao.jpg

wget -q https://raw.githubusercontent.com/jumori-tech/rdp-login/refs/heads/main/setup-remmina-fix.py -O ~/setup-remmina-fix.py
sudo python3 ~/setup-remmina-fix.py

wget -q https://raw.githubusercontent.com/jumori-tech/rdp-login/refs/heads/main/ajustar_resolucao.py -O ~/ajustar_resolucao.py
echo n | sudo python ~/ajustar_resolucao.py

wget -q https://raw.githubusercontent.com/jumori-tech/rdp-login/refs/heads/main/setup_config.py -O ~/setup_config.py
sudo python ~/setup_config.py
