#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AniLauncher — um launcher de janela (desktop) para o ani-cli.

Pensado para Windows + WSL (WSLg), mas funciona em qualquer Linux/macOS com
ambiente gráfico. A janela coleta a busca e as opções; o ani-cli em si roda
num terminal (ele precisa de um TTY para o fzf e o mpv).

Sem dependências externas: usa apenas a stdlib (tkinter).
"""

import os
import sys
import shlex
import shutil
import tempfile
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

APP_TITLE = "AniLauncher · ani-cli"
HISTORY_PATH = os.path.join(
    os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")),
    "ani-cli", "ani-hsts",
)

# Terminais que sabemos abrir, em ordem de preferência.
# Cada entrada: (nome_executável, função que recebe o caminho do script e
# devolve a lista de argumentos para abrir o terminal rodando aquele script).
TERMINALS = [
    ("wt.exe",               lambda sh: ["wt.exe", "wsl", "bash", sh]),            # Windows Terminal (WSL)
    ("x-terminal-emulator",  lambda sh: ["x-terminal-emulator", "-e", "bash", sh]),
    ("gnome-terminal",       lambda sh: ["gnome-terminal", "--", "bash", sh]),
    ("konsole",              lambda sh: ["konsole", "-e", "bash", sh]),
    ("xfce4-terminal",       lambda sh: ["xfce4-terminal", "-e", f"bash {shlex.quote(sh)}"]),
    ("alacritty",            lambda sh: ["alacritty", "-e", "bash", sh]),
    ("kitty",                lambda sh: ["kitty", "bash", sh]),
    ("xterm",                lambda sh: ["xterm", "-e", "bash", sh]),
    ("Terminal.app",         lambda sh: ["open", "-a", "Terminal", sh]),          # macOS
]


def which(prog):
    return shutil.which(prog)


def find_terminal():
    """Devolve (nome, builder) do primeiro terminal disponível, ou None."""
    for name, builder in TERMINALS:
        # wt.exe / Terminal.app podem não aparecer no which; tratamos à parte.
        if which(name):
            return name, builder
    # Tentativa especial: Windows Terminal costuma estar no PATH do Windows
    # acessível via WSL mesmo sem which() resolver.
    if which("wt.exe") or os.path.exists("/mnt/c/Windows/System32/cmd.exe"):
        return "wt.exe", dict(TERMINALS)["wt.exe"]
    return None


def build_ani_cmd(query, quality, dub, player_vlc, episodes, download, continue_):
    """Monta a lista de argumentos do ani-cli a partir das opções."""
    cmd = ["ani-cli"]
    if quality and quality != "best":
        cmd += ["-q", quality]
    if dub:
        cmd += ["--dub"]
    if player_vlc:
        cmd += ["-v"]
    if episodes.strip():
        cmd += ["-e", episodes.strip()]
    if download:
        cmd += ["-d"]
    if continue_:
        cmd += ["-c"]
    if query.strip():
        cmd += [query.strip()]
    return cmd


def write_launch_script(ani_cmd):
    """Cria um script temporário que roda o ani-cli e espera o Enter no fim."""
    pretty = " ".join(shlex.quote(a) for a in ani_cmd)
    body = (
        "#!/usr/bin/env bash\n"
        "set +e\n"
        'echo "▶ AniLauncher executando:"\n'
        f'echo "  {pretty}"\n'
        'echo\n'
        f"{pretty}\n"
        "code=$?\n"
        "echo\n"
        'if [ $code -ne 0 ]; then echo "⚠ ani-cli terminou com código $code."; fi\n'
        'read -rp "Pressione Enter para fechar..." _\n'
    )
    fd, path = tempfile.mkstemp(prefix="anilauncher_", suffix=".sh")
    with os.fdopen(fd, "w") as f:
        f.write(body)
    os.chmod(path, 0o755)
    return path


class AniLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("560x560")
        self.minsize(480, 520)
        self.configure(bg="#15171c")
        self._build_style()
        self._build_ui()
        self._check_deps()

    # ---------- estilo ----------
    def _build_style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        bg, fg, acc = "#15171c", "#e8e8e8", "#ffd34e"
        s.configure(".", background=bg, foreground=fg, fieldbackground="#22252d",
                    bordercolor="#2a2f3a", font=("Segoe UI", 10))
        s.configure("TButton", padding=8, background="#22252d", foreground=fg)
        s.map("TButton", background=[("active", "#2e333d")])
        s.configure("Accent.TButton", background=acc, foreground="#15171c",
                    font=("Segoe UI", 11, "bold"))
        s.map("Accent.TButton", background=[("active", "#ffdf7a")])
        s.configure("TLabel", background=bg, foreground=fg)
        s.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=acc)
        s.configure("Sub.TLabel", foreground="#8a93a3")
        s.configure("TEntry", fieldbackground="#22252d", foreground=fg, insertcolor=fg)
        s.configure("TCombobox", fieldbackground="#22252d", foreground=fg)
        s.configure("TCheckbutton", background=bg, foreground=fg)
        s.configure("TRadiobutton", background=bg, foreground=fg)

    # ---------- UI ----------
    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(self, text="AniLauncher", style="Title.TLabel").pack(anchor="w", padx=16, pady=(14, 0))
        ttk.Label(self, text="Frontend de janela para o ani-cli", style="Sub.TLabel").pack(anchor="w", padx=16)

        # Busca
        ttk.Label(self, text="Buscar anime").pack(anchor="w", **pad)
        self.q = tk.StringVar()
        ent = ttk.Entry(self, textvariable=self.q, font=("Segoe UI", 12))
        ent.pack(fill="x", padx=16)
        ent.bind("<Return>", lambda e: self.play())
        ent.focus()

        # Opções em grade
        opts = ttk.Frame(self)
        opts.pack(fill="x", padx=16, pady=10)
        opts.columnconfigure(1, weight=1)
        opts.columnconfigure(3, weight=1)

        ttk.Label(opts, text="Qualidade").grid(row=0, column=0, sticky="w", pady=4)
        self.quality = tk.StringVar(value="best")
        ttk.Combobox(opts, textvariable=self.quality, state="readonly", width=10,
                     values=["best", "1080", "720", "480", "360", "worst"]
                     ).grid(row=0, column=1, sticky="w", padx=8)

        ttk.Label(opts, text="Episódios").grid(row=0, column=2, sticky="e", pady=4)
        self.episodes = tk.StringVar()
        ttk.Entry(opts, textvariable=self.episodes, width=12).grid(row=0, column=3, sticky="w", padx=8)
        ttk.Label(opts, text="(ex: 5  ou  1-12)", style="Sub.TLabel").grid(row=1, column=3, sticky="w", padx=8)

        ttk.Label(opts, text="Áudio").grid(row=2, column=0, sticky="w", pady=8)
        self.dub = tk.BooleanVar(value=False)
        af = ttk.Frame(opts); af.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(af, text="Legendado", variable=self.dub, value=False).pack(side="left")
        ttk.Radiobutton(af, text="Dublado", variable=self.dub, value=True).pack(side="left", padx=8)

        ttk.Label(opts, text="Player").grid(row=2, column=2, sticky="e", pady=8)
        self.vlc = tk.BooleanVar(value=False)
        pf = ttk.Frame(opts); pf.grid(row=2, column=3, sticky="w")
        ttk.Radiobutton(pf, text="mpv", variable=self.vlc, value=False).pack(side="left")
        ttk.Radiobutton(pf, text="VLC", variable=self.vlc, value=True).pack(side="left", padx=8)

        # Botões principais
        bf = ttk.Frame(self); bf.pack(fill="x", padx=16, pady=6)
        ttk.Button(bf, text="▶  Assistir", style="Accent.TButton",
                   command=self.play).pack(side="left", expand=True, fill="x")
        ttk.Button(bf, text="⏯  Continuar",
                   command=self.continue_last).pack(side="left", expand=True, fill="x", padx=6)
        ttk.Button(bf, text="⬇  Baixar",
                   command=self.download).pack(side="left", expand=True, fill="x")

        # Histórico
        ttk.Label(self, text="Histórico recente").pack(anchor="w", padx=16, pady=(10, 0))
        hist_wrap = tk.Frame(self, bg="#15171c")
        hist_wrap.pack(fill="both", expand=True, padx=16, pady=4)
        self.hist = tk.Listbox(hist_wrap, bg="#1b1e24", fg="#cdd3dd",
                               selectbackground="#ffd34e", selectforeground="#15171c",
                               borderwidth=0, highlightthickness=1,
                               highlightbackground="#2a2f3a", activestyle="none",
                               font=("Segoe UI", 10))
        self.hist.pack(side="left", fill="both", expand=True)
        self.hist.bind("<Double-Button-1>", lambda e: self.play_from_history())
        sb = ttk.Scrollbar(hist_wrap, command=self.hist.yview)
        sb.pack(side="right", fill="y")
        self.hist.config(yscrollcommand=sb.set)
        hb = ttk.Frame(self); hb.pack(fill="x", padx=16)
        ttk.Button(hb, text="↻ Atualizar histórico", command=self.load_history).pack(side="left")
        ttk.Button(hb, text="⤓ Atualizar ani-cli", command=self.update_anicli).pack(side="left", padx=6)

        # Status
        self.status = tk.StringVar(value="Pronto.")
        ttk.Label(self, textvariable=self.status, style="Sub.TLabel",
                  anchor="w").pack(fill="x", padx=16, pady=(4, 10))

        self.load_history()

    # ---------- dependências ----------
    def _check_deps(self):
        missing = [p for p in ("ani-cli",) if not which(p)]
        players = [p for p in ("mpv", "vlc") if which(p)]
        msgs = []
        if missing:
            msgs.append("ani-cli não encontrado no PATH do WSL.")
        if not players:
            msgs.append("Nenhum player (mpv/vlc) encontrado.")
        if not find_terminal():
            msgs.append("Nenhum terminal para abrir (instale Windows Terminal ou xterm).")
        if msgs:
            self.status.set("⚠ " + " ".join(msgs))
        else:
            self.status.set("Tudo certo. Digite um anime e clique em Assistir.")

    # ---------- ações ----------
    def _launch(self, ani_cmd):
        term = find_terminal()
        if not term:
            messagebox.showerror(
                APP_TITLE,
                "Não encontrei um terminal para abrir o ani-cli.\n\n"
                "No WSL, instale o Windows Terminal, ou no Linux um terminal\n"
                "como xterm/gnome-terminal/konsole.")
            return
        if not which("ani-cli"):
            messagebox.showerror(
                APP_TITLE,
                "ani-cli não está instalado/visível no PATH.\n\n"
                "Veja o README.md para instalar dentro do WSL.")
            return
        name, builder = term
        script = write_launch_script(ani_cmd)
        argv = builder(script)
        try:
            subprocess.Popen(argv, start_new_session=True)
            self.status.set(f"▶ Aberto no {name}: {' '.join(shlex.quote(a) for a in ani_cmd)}")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"Falha ao abrir o terminal ({name}):\n{e}")

    def play(self):
        if not self.q.get().strip():
            self.status.set("Digite o nome de um anime para buscar.")
            return
        self._launch(self._opts())

    def continue_last(self):
        self._launch(build_ani_cmd("", self.quality.get(), self.dub.get(),
                                    self.vlc.get(), "", False, True))

    def download(self):
        if not self.q.get().strip():
            self.status.set("Digite o nome de um anime para baixar.")
            return
        cmd = build_ani_cmd(self.q.get(), self.quality.get(), self.dub.get(),
                            False, self.episodes.get(), True, False)
        self._launch(cmd)

    def play_from_history(self):
        sel = self.hist.curselection()
        if not sel:
            return
        title = self.hist.get(sel[0]).split("  ·  ", 1)[-1].strip()
        self.q.set(title)
        self.play()

    def _opts(self):
        return build_ani_cmd(self.q.get(), self.quality.get(), self.dub.get(),
                            self.vlc.get(), self.episodes.get(), False, False)

    def update_anicli(self):
        self._launch(["ani-cli", "-U"])

    def load_history(self):
        self.hist.delete(0, tk.END)
        if not os.path.exists(HISTORY_PATH):
            self.hist.insert(tk.END, "  (sem histórico ainda)")
            return
        try:
            with open(HISTORY_PATH, encoding="utf-8") as f:
                lines = [l.rstrip("\n") for l in f if l.strip()]
        except OSError as e:
            self.hist.insert(tk.END, f"  (erro lendo histórico: {e})")
            return
        # Formato do ani-cli: "<ep>\t<allanime_id>\t<título>"
        for line in reversed(lines):
            parts = line.split("\t")
            if len(parts) >= 3:
                ep, title = parts[0], parts[-1]
                self.hist.insert(tk.END, f"  ep {ep}  ·  {title}")
            else:
                self.hist.insert(tk.END, "  " + line)
        if self.hist.size() == 0:
            self.hist.insert(tk.END, "  (sem histórico ainda)")


def main():
    if "tkinter" not in sys.modules:
        pass
    try:
        app = AniLauncher()
    except tk.TclError as e:
        sys.stderr.write(
            "Não foi possível abrir a janela (sem display gráfico).\n"
            "No WSL, use Windows 11 com WSLg, ou configure um servidor X.\n"
            f"Detalhe: {e}\n")
        sys.exit(1)
    app.mainloop()


if __name__ == "__main__":
    main()
