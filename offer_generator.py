"""Offer Generator

A small desktop form for turning an advertiser's offer conditions into a
formatted Telegram message. The message is sent to me by a Telegram bot,
because only Telegram's own HTML (<blockquote> etc.) renders the quote block
I need, and plain HTML text copied from a browser does not.

Fill in the fields, press Enter (or "Send") and the formatted offer arrives
in my Telegram chat.
"""
import html
import os
import sys
from pathlib import Path

import customtkinter as ctk
import requests
from dotenv import load_dotenv

# Configuration

# Look for .env next to the script, or next to the .exe when built with PyInstaller.
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
OWNER_ID = os.getenv("OWNER_ID", "")

TRAFFIC_SOURCE = "FB"        # shown in every offer title, e.g. "Name | UK [FB] Slot"
DEFAULT_APPROACH = "Slot"    # used when the Approach field is empty

FIELDS = [
    "Name", "GEO", "CPA", "Mindep", "Cap", "Baseline",
    "Wager", "KPI", "I2R", "R2D", "Platform", "Approach", "Comment",
]


# Message formatting (no GUI, no network) 

def geo_flag(geo: str) -> str:
    """Convert a two-letter country code to a flag emoji ("UK" is treated as GB)."""
    code = geo.strip().upper()
    if code == "UK":
        code = "GB"
    if len(code) != 2 or not code.isascii() or not code.isalpha():
        return "🌍"
    # A flag emoji is two "regional indicator" characters, one per letter.
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in code)


def _conditions(mindep: str, baseline: str, wager: str) -> str:
    """Build the text inside the brackets: mindep, baseline and wager."""
    if baseline and wager:
        if mindep == baseline == wager:
            return f"mindep = <b>baseline = wager {wager}</b>"
        if mindep == baseline:
            return f"mindep = <b>baseline {baseline} + wager {wager}</b>"
        if mindep == wager:
            return f"mindep = <b>wager {wager} + baseline {baseline}</b>"
        return f"mindep {mindep} + <b>baseline {baseline} + wager {wager}</b>"
    if baseline:
        if mindep == baseline:
            return f"mindep = <b>baseline {baseline}</b>"
        return f"mindep {mindep} + <b>baseline {baseline}</b>"
    if wager:
        if mindep == wager:
            return f"mindep = <b>wager {wager}</b>"
        return f"mindep {mindep} + <b>wager {wager}</b>"
    return f"mindep {mindep}"


def build_offer_text(name_input, geo, cpa, mindep, cap, baseline, wager,
                     kpi, i2r, r2d, platform, approach, comment) -> str:
    """Return the Telegram-HTML text. Several names separated by commas give several lines."""
    # Telegram HTML needs <, > and & escaped, otherwise the message is rejected.
    esc = lambda value: html.escape(value, quote=False)

    names = [n.strip() for n in name_input.split(",") if n.strip()]
    flag = geo_flag(geo)
    cap_str = "?ftd" if cap == "" else f"<b>{esc(cap)}ftd</b>"
    conditions = _conditions(esc(mindep), esc(baseline), esc(wager))

    # Quote block: comment first, then KPI, then platform (only the filled ones).
    quote_lines = []
    if comment:
        quote_lines.append(esc(comment))
    if kpi:
        quote_lines.append(f"KPI: {esc(kpi)}")
    if platform:
        quote_lines.append(f"{esc(platform)} platform")

    # Conversion rates line: invite-to-registration and registration-to-deposit.
    rates = []
    if i2r:
        rates.append(f"I2R — <b>{esc(i2r)}%</b>")
    if r2d:
        rates.append(f"R2D — <b>{esc(r2d)}%</b>")

    results = []
    for name in names:
        title = f"{flag} <b>{esc(name)} | {esc(geo)} [{TRAFFIC_SOURCE}] {esc(approach)} — CPA {esc(cpa)}</b>"
        line = f"{title} ({conditions}, {cap_str})"
        if quote_lines:
            line += "\n<blockquote><b>" + "\n".join(quote_lines) + "</b></blockquote>"
        if rates:
            line += "\n" + ", ".join(rates)
        results.append(line)

    return "\n".join(results)


# Telegram

def send_to_bot(text: str) -> None:
    """Send the text to my Telegram chat. Raises an exception if it fails."""
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": OWNER_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
    response.raise_for_status()


# GUI (customtkinter)

def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # The main window. Everything else is placed inside it.
    app = ctk.CTk()
    app.title("Offer Generator")
    app.geometry("600x650")

    # A frame is a container; widgets inside it are arranged with .grid(row, column).
    frame = ctk.CTkFrame(app)
    frame.pack(pady=20, padx=20, fill="both", expand=True)
    frame.grid_columnconfigure(1, weight=1)   # the text boxes (column 1) stretch with the window

    entries = {}   # field name -> text box
    locks = {}     # field name -> checkbox state; a ticked field is NOT cleared after sending,
                   # so values that repeat between offers (e.g. GEO, Platform) stay filled in

    # One row per field: label | text box | "lock" checkbox
    for row, field in enumerate(FIELDS):
        ctk.CTkLabel(frame, text=field).grid(row=row, column=0, sticky="w", pady=5)

        entry = ctk.CTkEntry(frame, placeholder_text=field)
        entry.grid(row=row, column=1, sticky="ew", pady=5, padx=10)
        entries[field] = entry

        lock_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(frame, text="", variable=lock_var, width=20).grid(row=row, column=2, padx=5)
        locks[field] = lock_var

    def show_toast(message: str, duration: int = 600) -> None:
        """Show a small popup in the middle of the window that closes itself."""
        toast = ctk.CTkToplevel(app)
        toast.overrideredirect(True)        # no title bar
        toast.attributes("-topmost", True)  # stay above the main window
        x = app.winfo_x() + app.winfo_width() // 2 - 100
        y = app.winfo_y() + app.winfo_height() // 2 - 30
        toast.geometry(f"200x60+{x}+{y}")
        ctk.CTkLabel(toast, text=message, font=("Arial", 16)).pack(expand=True)

        def close_toast():
            toast.destroy()
            entries["Name"].focus()

        toast.after(duration, close_toast)   # call close_toast after `duration` milliseconds

    def on_submit(event=None) -> None:
        data = {field: entries[field].get().strip() for field in FIELDS}

        if not data["Name"]:
            show_toast("Name is required")
            return

        text = build_offer_text(
            data["Name"], data["GEO"], data["CPA"], data["Mindep"], data["Cap"],
            data["Baseline"], data["Wager"], data["KPI"], data["I2R"],
            data["R2D"], data["Platform"], data["Approach"] or DEFAULT_APPROACH,
            data["Comment"],
        )

        try:
            send_to_bot(text)
        except requests.RequestException:
            show_toast("Send failed")
            return

        show_toast("Sent!")

        # Clear every field except the locked ones.
        for field in FIELDS:
            if not locks[field].get():
                entries[field].delete(0, "end")
        entries["Name"].focus()

    def find_unlocked(index: int, step: int):
        """Index of the nearest unlocked field after (step=1) or before (step=-1) `index`."""
        i = index + step
        while 0 <= i < len(FIELDS):
            if not locks[FIELDS[i]].get():
                return i
            i += step
        return None

    def move_focus(index: int, step: int) -> None:
        target = find_unlocked(index, step)
        if target is not None:
            entries[FIELDS[target]].focus()

    def on_enter(index: int) -> None:
        """Enter jumps to the next unlocked field; if there is none, it sends the form."""
        if find_unlocked(index, 1) is None:
            on_submit()
        else:
            move_focus(index, 1)

    # Keyboard: Up/Down move between fields, Enter moves forward or sends.
    # (idx=index in the lambdas fixes the current index for each field.)
    for index, field in enumerate(FIELDS):
        entry = entries[field]
        entry.bind("<Up>", lambda event, idx=index: move_focus(idx, -1))
        entry.bind("<Down>", lambda event, idx=index: move_focus(idx, 1))
        entry.bind("<Return>", lambda event, idx=index: on_enter(idx))

    ctk.CTkButton(app, text="Send", command=on_submit).pack(pady=10)

    entries["Name"].focus()
    app.mainloop()   # start the event loop: the window stays open and reacts to input


if __name__ == "__main__":
    main()
