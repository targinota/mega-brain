# AniLauncher

Um **launcher de janela (desktop)** para o [`ani-cli`](https://github.com/pystardust/ani-cli).
Você digita o anime e escolhe as opções numa janela; o launcher dispara o `ani-cli`
num terminal, onde a seleção e o player (`mpv`/VLC) rodam normalmente.

Feito em **Python + Tkinter** (só a stdlib — sem dependências para instalar).
Pensado para **Windows + WSL (WSLg)**, mas roda em qualquer Linux/macOS com tela.

```
┌─ AniLauncher · ani-cli ───────────────────────┐
│  Buscar anime:  [ frieren                    ] │
│  Qualidade [720 ▾]      Episódios [ 1-12     ] │
│  Áudio  (•)Legendado ( )Dublado                │
│  Player (•)mpv  ( )VLC                         │
│  [ ▶ Assistir ] [ ⏯ Continuar ] [ ⬇ Baixar ]  │
│  Histórico recente:                            │
│   ep 8  ·  Frieren: Beyond Journey's End       │
│   ep 3  ·  Dandadan                            │
└────────────────────────────────────────────────┘
```

## Recursos

- 🔎 Busca por nome
- 🎚️ Qualidade (best / 1080 / 720 / 480 / 360 / worst)
- 💬 Legendado ou **dublado** (`--dub`)
- ▶️ Player **mpv** ou **VLC**
- 🔢 Episódio único ou intervalo (ex: `5` ou `1-12`)
- ⏯️ **Continuar** de onde parou (`ani-cli -c`)
- ⬇️ **Baixar** episódios (`ani-cli -d`)
- 🕘 Lista de **histórico** (duplo-clique para reassistir)
- ⤓ Atualizar o próprio ani-cli (`ani-cli -U`)

## Pré-requisitos (no WSL)

Você precisa de **Windows 11** (WSLg já traz suporte gráfico). Dentro do WSL:

```bash
# 1) Tkinter (a janela) e ferramentas básicas
sudo apt update
sudo apt install -y python3 python3-tk git curl mpv fzf

# 2) ani-cli
sudo curl -sL https://raw.githubusercontent.com/pystardust/ani-cli/master/ani-cli \
  -o /usr/local/bin/ani-cli
sudo chmod +x /usr/local/bin/ani-cli
```

> **Windows 10:** o WSLg não existe nativamente. Use Windows 11, ou instale um
> servidor X (ex: VcXsrv) e exporte `DISPLAY` antes de abrir o launcher.

Para abrir a janela do terminal ao assistir, tenha o **Windows Terminal**
instalado (o launcher chama `wt.exe wsl ...`). Alternativa: um terminal Linux
como `xterm` (`sudo apt install xterm`).

## Como usar

```bash
chmod +x run.sh
./run.sh
```

ou diretamente:

```bash
python3 anilauncher.py
```

1. Digite o anime e tecle **Enter** (ou clique em **Assistir**).
2. Ajuste qualidade / áudio / player se quiser.
3. O `ani-cli` abre num terminal: escolha o resultado e o episódio normalmente.

## Como funciona

O `ani-cli` é interativo e precisa de um **terminal (TTY)** para o `fzf` e o
`mpv`. Uma janela gráfica não tem TTY, então o AniLauncher monta o comando
(`ani-cli -q 720 --dub "frieren"`, por exemplo), grava um pequeno script
temporário e abre um terminal rodando esse script. Assim você ganha a comodidade
da janela sem perder o fluxo nativo do ani-cli.

Ordem de terminais tentada: `wt.exe` (Windows Terminal via WSL) →
`x-terminal-emulator` → `gnome-terminal` → `konsole` → `xfce4-terminal` →
`alacritty` → `kitty` → `xterm` → `Terminal.app` (macOS).

## Solução de problemas

| Sintoma | Causa provável / solução |
|---|---|
| "sem display gráfico" | Use Windows 11 (WSLg) ou configure um servidor X e `DISPLAY`. |
| "ani-cli não encontrado" | Instale o ani-cli (veja acima) e confirme `which ani-cli`. |
| "Nenhum terminal para abrir" | Instale o Windows Terminal ou `sudo apt install xterm`. |
| Vídeo não abre | Instale o `mpv` (`sudo apt install mpv`) ou marque VLC. |
| Sem histórico | Ele aparece depois que você assistir algo (arquivo `ani-hsts`). |

## Licença

Uso livre. O `ani-cli` é um projeto separado, sob sua própria licença.
