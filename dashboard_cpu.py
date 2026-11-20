import csv
import tkinter as tk

FILE = "telemetry.csv"
N_POINTS = 60          # nombre de points affichés
REFRESH_MS = 500
SEUIL = 80             # seuil d'alerte visuel (%)
W, H = 820, 420
MARGIN = 50


def read_data():
    """Lit les N derniers points: liste de (cpu, alert)."""
    try:
        with open(FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))[1:]  # saute l'en-tête
    except (FileNotFoundError, OSError):
        return []
    data = []
    for r in rows[-N_POINTS:]:
        try:
            data.append((int(r[1]), int(r[2])))
        except (IndexError, ValueError):
            continue
    return data


def to_xy(i, cpu, n):
    x = MARGIN + (W - 2 * MARGIN) * (i / max(n - 1, 1))
    y = H - MARGIN - (H - 2 * MARGIN) * (cpu / 100)
    return x, y


def refresh():
    data = read_data()
    canvas.delete("all")

    # Grille + axe Y
    for v in (0, 25, 50, 75, 100):
        _, y = to_xy(0, v, 2)
        canvas.create_line(MARGIN, y, W - MARGIN, y, fill="#333")
        canvas.create_text(MARGIN - 8, y, text=f"{v}%", fill="#aaa", anchor="e")

    # Ligne de seuil
    _, ys = to_xy(0, SEUIL, 2)
    canvas.create_line(MARGIN, ys, W - MARGIN, ys, fill="#c9a227", dash=(4, 4))
    canvas.create_text(W - MARGIN, ys - 8, text=f"seuil {SEUIL}%",
                       fill="#c9a227", anchor="e")

    if not data:
        canvas.create_text(W / 2, H / 2, fill="#aaa",
                           text="En attente de données (lance serial_alert_bridge.py)")
        status.config(text="Aucune donnée", fg="#aaa")
        root.after(REFRESH_MS, refresh)
        return

    pts = [to_xy(i, c, len(data)) for i, (c, _) in enumerate(data)]
    if len(pts) > 1:
        flat = [v for p in pts for v in p]
        canvas.create_line(*flat, fill="#4da3ff", width=2, smooth=False)

    for (x, y), (cpu, alert) in zip(pts, data):
        if alert:
            canvas.create_oval(x - 5, y - 5, x + 5, y + 5,
                               fill="#ff3b30", outline="")

    cpu, alert = data[-1]
    last_alert = any(a for _, a in data[-5:])
    if last_alert or cpu >= SEUIL:
        status.config(text=f"CPU = {cpu}%   ⚠ ALERTE / CHARGE ÉLEVÉE", fg="#ff3b30")
    else:
        status.config(text=f"CPU = {cpu}%   normal", fg="#34c759")

    root.after(REFRESH_MS, refresh)


root = tk.Tk()
root.title("Supervision CPU - STM32")
root.configure(bg="#111")

status = tk.Label(root, text="...", font=("Segoe UI", 16, "bold"),
                  bg="#111", fg="#aaa")
status.pack(pady=(10, 0))

canvas = tk.Canvas(root, width=W, height=H, bg="#1c1c1e", highlightthickness=0)
canvas.pack(padx=10, pady=10)

refresh()
root.mainloop()
