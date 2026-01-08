#!/usr/bin/env python3
import tkinter as tk
import subprocess
import threading
import socket
from PIL import Image, ImageTk

# ======================
# CONFIG
# ======================
BG_IMAGE = "/home/jumori/backgrounds/leao.jpg"
FONT = "Inter"

XFREERDP_BASE = [
    "xfreerdp",
    "/cert:ignore",
    "/sec:nla",
    "/f",
    "/network:auto",
    "-gfx",
    "/gdi:sw",
    "+bitmap-cache",
    "+glyph-cache",
    "/sound:sys:pulse,quality:high"
]

RDS_MAP = {
    "RDS1": "192.168.0.43",
    "RDS2": "192.168.0.44",
    "RDS3": "192.168.0.45",
    "RDS4": "192.168.0.46",
    "RDS5": "192.168.0.47",
    "RDS6": "192.168.0.49",
    "RDS7": "192.168.0.50",
}

# ======================
# STATUS DO SISTEMA
# ======================
def get_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Indisponível"

def get_status_sistema():
    hostname = socket.gethostname()
    ip_local = get_ip_local()

    try:
        subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", "8.8.8.8"],
            stderr=subprocess.DEVNULL
        )
        internet = "Conectado"
        cor = "#66bb6a"
    except:
        internet = "Sem conexão"
        cor = "#ff5252"

    texto = (
        f"Hostname: {hostname}\n"
        f"IP: {ip_local}\n"
        f"Internet: {internet}"
    )

    return texto, cor

# ======================
# ROOT
# ======================
root = tk.Tk()
root.attributes("-fullscreen", True)
root.configure(bg="black")
root.protocol("WM_DELETE_WINDOW", lambda: None)

# ======================
# BACKGROUND
# ======================
bg_img = Image.open(BG_IMAGE)
bg_img = bg_img.resize(
    (root.winfo_screenwidth(), root.winfo_screenheight()),
    Image.LANCZOS
)
bg_photo = ImageTk.PhotoImage(bg_img)
tk.Label(root, image=bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

eye_open_img = ImageTk.PhotoImage(
    Image.open("/home/jumori/backgrounds/eye-open.png").resize((20, 20), Image.LANCZOS)
)

eye_closed_img = ImageTk.PhotoImage(
    Image.open("/home/jumori/backgrounds/eye-closed.png").resize((20, 20), Image.LANCZOS)
)

# ======================
# CARD CENTRAL
# ======================
card = tk.Frame(root, bg="#111111")
card.place(relx=0.5, rely=0.5, anchor="center", width=520, height=600)

tk.Label(
    card,
    text="Login",
    fg="#e53935",
    bg="#111111",
    font=(FONT, 28, "bold")
).pack(pady=(50, 30))

# ======================
# CAMPOS
# ======================
def input_field(label):
    tk.Label(
        card,
        text=label,
        fg="#cccccc",
        bg="#111111",
        font=(FONT, 12)
    ).pack(anchor="w", padx=60)

    e = tk.Entry(
        card,
        font=(FONT, 16),
        bg="#1e1e1e",
        fg="white",
        insertbackground="white",
        relief="flat"
    )
    e.pack(padx=60, pady=10, fill="x")
    return e

entry_server = input_field("Servidor")
entry_user = input_field("Usuário")

# ===== SENHA COM OLHINHO =====
tk.Label(
    card,
    text="Senha",
    fg="#cccccc",
    bg="#111111",
    font=(FONT, 12)
).pack(anchor="w", padx=60)

# Campo senha + botão olho
senha_frame = tk.Frame(card, bg="#111111")
senha_frame.pack(padx=60, pady=10, fill="x")

entry_pass = tk.Entry(
    senha_frame,
    font=(FONT, 16),
    bg="#1e1e1e",
    fg="white",
    insertbackground="white",
    relief="flat",
    show="*"
)
entry_pass.pack(side="left", fill="x", expand=True)

senha_visivel = False

def toggle_senha():
    global senha_visivel
    senha_visivel = not senha_visivel
    entry_pass.config(show="" if senha_visivel else "*")
    btn_eye.config(image=eye_open_img if senha_visivel else eye_closed_img)

btn_eye = tk.Button(
    senha_frame,
    image=eye_closed_img,
    bg="#1e1e1e",
    activebackground="#1e1e1e",
    relief="flat",
    command=toggle_senha
)
btn_eye.pack(side="right", padx=(5, 0))


# ======================
# STATUS LOGIN
# ======================
status = tk.Label(
    card,
    text="",
    fg="#ff5252",
    bg="#111111",
    font=(FONT, 12),
    wraplength=380
)
status.pack(pady=10)

btn = tk.Button(
    card,
    text="Entrar",
    font=(FONT, 16, "bold"),
    bg="#e53935",
    fg="white",
    relief="flat",
    height=2
)
btn.pack(padx=60, pady=15, fill="x")

# ======================
# STATUS DO SISTEMA
# ======================
status_sys = tk.Label(
    card,
    text="",
    fg="#cccccc",
    bg="#111111",
    font=(FONT, 11),
    justify="center",
    anchor="center"
)
status_sys.pack(padx=80, pady=(20, 0), fill="x")

def atualizar_status():
    texto, cor = get_status_sistema()
    status_sys.config(text=texto, fg=cor)
    root.after(10000, atualizar_status)

# ======================
# RDP
# ======================
def conectar():
    server_input = entry_server.get().strip().upper()
    user = entry_user.get().strip()
    password = entry_pass.get().strip()

    if not server_input or not user or not password:
        status.config(text="Servidor, usuário e senha são obrigatórios.")
        return

    if server_input not in RDS_MAP:
        status.config(text=f"Servidor '{server_input}' não existe.")
        return

    server_ip = RDS_MAP[server_input]

    status.config(text=f"Conectando ao {server_input}...")
    btn.config(state="disabled")

    cmd = XFREERDP_BASE + [
        f"/v:{server_ip}",
        f"/u:{user}",
        f"/p:{password}"
    ]

    def run():
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        _, err = proc.communicate()

        msg = ""
        err = err.upper() if err else ""

        if "LOGON_FAILURE" in err:
            msg = "Usuário ou senha inválidos."
        elif (
            "NAME_NOT_RESOLVED" in err
            or "UNABLE TO CONNECT" in err
            or "FAILED TO CONNECT" in err
            or "TRANSPORT CONNECT FAILED" in err
        ):
            msg = f"Não foi possível conectar ao {server_input}."

        root.after(0, lambda: reset(msg))

    threading.Thread(target=run, daemon=True).start()

def reset(msg):
    entry_pass.delete(0, tk.END)
    status.config(text=msg)
    btn.config(state="normal")

btn.config(command=conectar)

# ======================
# ENTER FUNCIONA EM TUDO
# ======================
def enter_pressed(event):
    if btn["state"] == "normal":
        conectar()

for w in (entry_server, entry_user, entry_pass, root):
    w.bind("<Return>", enter_pressed)
    w.bind("<KP_Enter>", enter_pressed)

entry_server.focus_set()

# ======================
# START
# ======================
atualizar_status()
root.mainloop()