# keftrol

Tray app to control KEF speakers - switch inputs and adjust volume.

Uses [pykefcontrol](https://github.com/N0ciple/pykefcontrol) for speaker communication.

## Setup (Arch Linux)

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```
.venv/bin/python keftrol.py &
```

## Autostart (Hyprland)

Add to `~/.config/hypr/hyprland.conf`:

```
exec-once = /home/ehs/dev/keftrol/.venv/bin/python /home/ehs/dev/keftrol/keftrol.py
```

## Configuration

Edit `SPEAKER_IP` in `keftrol.py` if your speaker IP changes.
