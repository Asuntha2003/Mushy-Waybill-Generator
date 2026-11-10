import os
import sys
import sqlite3
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

APP_NAME = "Mushy Cute Corner - Waybill Generator"
PAGE_W, PAGE_H = 4 * inch, 6 * inch

def app_dir():
    # Store writable data beside the EXE; for source mode, beside this script.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

ROOT = app_dir()
DATA_DIR = ROOT / "database"
PDF_DIR = ROOT / "generated_waybills"
DATA_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "waybills.db"

def db_connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    with db_connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS waybills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sender_name TEXT, sender_phone TEXT, sender_address TEXT,
            customer_name TEXT NOT NULL, customer_phone TEXT,
            customer_address TEXT NOT NULL, amount TEXT,
            instructions TEXT, pdf_path TEXT)""")
        defaults = {
            "sender_name": "Mushy Cute Corner",
            "sender_phone": "",
            "sender_address": ""
        }
        for key, value in defaults.items():
            con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))

def get_setting(key):
    with db_connect() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else ""

def set_setting(key, value):
    with db_connect() as con:
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

def safe_filename(value):
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value.strip())
    return cleaned or "waybill"

def draw_wrapped(c, text, x, y, max_width, font="Helvetica", size=8, leading=10, max_lines=5):
    c.setFont(font, size)
    words = str(text or "").split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if stringWidth(candidate, font, size) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if not lines:
        lines = ["-"]
    for line in lines[:max_lines]:
        c.drawString(x, y, line)
        y -= leading
    return y

def create_pdf(data, path):
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
    margin = 0.22 * inch
    x = margin
    right = PAGE_W - margin
    width = right - x
    y = PAGE_H - margin

    # Header
    c.setFillColor(colors.HexColor("#172554"))
    c.roundRect(x, y - 0.62*inch, width, 0.62*inch, 7, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(PAGE_W/2, y - 0.25*inch, data["sender_name"][:34])
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PAGE_W/2, y - 0.43*inch, "DELIVERY WAYBILL")
    y -= 0.78*inch

    # Order and date
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, f"ORDER ID: {data['order_id']}")
    c.setFont("Helvetica", 7)
    c.drawRightString(right, y, data["date"])
    y -= 0.13*inch
    c.setStrokeColor(colors.HexColor("#64748b"))
    c.setLineWidth(0.7)
    c.line(x, y, right, y)
    y -= 0.18*inch

    # Sender block
    c.setFillColor(colors.HexColor("#dbeafe"))
    c.roundRect(x, y - 0.18*inch, width, 0.18*inch, 3, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 5, y - 0.13*inch, "FROM / SENDER")
    y -= 0.31*inch
    c.setFillColor(colors.black)
    y = draw_wrapped(c, data["sender_name"], x+3, y, width-6, "Helvetica-Bold", 8, 10, 1)
    y = draw_wrapped(c, "Tel: " + (data["sender_phone"] or "-"), x+3, y, width-6, size=7, leading=9, max_lines=1)
    y = draw_wrapped(c, data["sender_address"] or "-", x+3, y, width-6, size=7, leading=9, max_lines=2)
    y -= 0.08*inch

    # Receiver block
    c.setFillColor(colors.HexColor("#dcfce7"))
    c.roundRect(x, y - 0.18*inch, width, 0.18*inch, 3, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#166534"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 5, y - 0.13*inch, "TO / CUSTOMER")
    y -= 0.31*inch
    c.setFillColor(colors.black)
    y = draw_wrapped(c, data["customer_name"], x+3, y, width-6, "Helvetica-Bold", 10, 12, 2)
    y = draw_wrapped(c, "Tel: " + (data["customer_phone"] or "-"), x+3, y, width-6, size=8, leading=10, max_lines=1)
    y = draw_wrapped(c, data["customer_address"], x+3, y, width-6, size=8, leading=10, max_lines=4)
    y -= 0.08*inch

    # Amount panel
    panel_h = 0.52*inch
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.roundRect(x, y-panel_h, width, panel_h, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#334155"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x+8, y-0.19*inch, "TOTAL AMOUNT")
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 14)
    amount = data["amount"].strip()
    c.drawRightString(right-8, y-0.30*inch, ("LKR " + amount) if amount else "LKR 0.00")
    y -= panel_h + 0.12*inch

    if data["instructions"].strip():
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor("#475569"))
        c.drawString(x+2, y, "DELIVERY INSTRUCTIONS")
        y -= 10
        y = draw_wrapped(c, data["instructions"], x+2, y, width-4, size=7, leading=9, max_lines=3)
        y -= 3

    # Footer
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.line(x, 0.48*inch, right, 0.48*inch)
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(PAGE_W/2, 0.32*inch, "THANK YOU FOR YOUR ORDER!")
    c.setFont("Helvetica", 6)
    c.drawCentredString(PAGE_W/2, 0.20*inch, "Please contact the sender for order enquiries.")
    c.save()

class WaybillApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("900x720")
        self.minsize(760, 650)
        self.configure(bg="#f1f5f9")
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("TFrame", background="#f1f5f9")
        self.style.configure("Card.TFrame", background="white")
        self.style.configure("TLabel", background="white", foreground="#172554", font=("Segoe UI", 9))
        self.style.configure("Title.TLabel", background="#172554", foreground="white", font=("Segoe UI", 17, "bold"))
        self.style.configure("Section.TLabel", background="white", foreground="#1d4ed8", font=("Segoe UI", 10, "bold"))
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=8)
        self.style.configure("Primary.TButton", background="#1d4ed8", foreground="white")
        self.style.map("Primary.TButton", background=[("active", "#1e40af")])
        self.vars = {}
        self.build_ui()
        self.load_sender_settings()

    def build_ui(self):
        header = tk.Frame(self, bg="#172554", height=76)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="MUSHY CUTE CORNER", bg="#172554", fg="white",
                 font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=22, pady=(12, 0))
        tk.Label(header, text="WAYBILL GENERATOR  •  4 × 6 INCH COURIER LABEL",
                 bg="#172554", fg="#bfdbfe", font=("Segoe UI", 9)).pack(anchor="w", padx=23)

        body = ttk.Frame(self, padding=16)
        body.pack(fill="both", expand=True)
        canvas = tk.Canvas(body, bg="#f1f5f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        self.form = ttk.Frame(canvas)
        self.form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.form, anchor="nw", width=820)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.add_section("SENDER / BUSINESS DETAILS")
        self.add_entry("Business name", "sender_name")
        self.add_entry("Contact number", "sender_phone")
        self.add_entry("Business address", "sender_address")

        self.add_section("CUSTOMER / RECEIVER DETAILS")
        self.add_entry("Customer name *", "customer_name")
        self.add_entry("Customer contact number", "customer_phone")
        self.add_entry("Full delivery address *", "customer_address", multiline=True)

        self.add_section("ORDER DETAILS")
        self.add_entry("Order ID *", "order_id")
        self.add_entry("Total amount (LKR)", "amount")
        self.add_entry("Delivery instructions (optional)", "instructions")

        buttons = ttk.Frame(self.form)
        buttons.pack(fill="x", pady=(16, 10))
        ttk.Button(buttons, text="SAVE SENDER DETAILS", command=self.save_sender_settings).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="CLEAR FORM", command=self.clear_form).pack(side="left", padx=8)
        ttk.Button(buttons, text="WAYBILL HISTORY", command=self.show_history).pack(side="left", padx=8)
        ttk.Button(buttons, text="GENERATE PDF WAYBILL", style="Primary.TButton",
                   command=self.generate).pack(side="right")

        note = tk.Label(self, text="PDF output: generated_waybills  |  Paper size: 4 × 6 inches",
                        bg="#f1f5f9", fg="#64748b", font=("Segoe UI", 8))
        note.pack(pady=(0, 8))

    def add_section(self, title):
        frame = ttk.Frame(self.form, style="Card.TFrame", padding=(14, 10))
        frame.pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text=title, style="Section.TLabel").pack(anchor="w")

    def add_entry(self, label, key, multiline=False):
        # Attach fields to the most recent section frame.
        frame = self.form.winfo_children()[-1]
        wrap = ttk.Frame(frame, style="Card.TFrame")
        wrap.pack(fill="x", pady=4)
        ttk.Label(wrap, text=label, width=28).pack(side="left", anchor="n", pady=6)
        if multiline:
            widget = tk.Text(wrap, height=3, width=65, font=("Segoe UI", 9), relief="solid", bd=1,
                             wrap="word", bg="#ffffff")
            widget.pack(side="left", fill="x", expand=True)
            self.vars[key] = widget
        else:
            var = tk.StringVar()
            ent = ttk.Entry(wrap, textvariable=var, font=("Segoe UI", 9))
            ent.pack(side="left", fill="x", expand=True, ipady=4)
            self.vars[key] = var

    def get_value(self, key):
        obj = self.vars[key]
        if isinstance(obj, tk.Text):
            return obj.get("1.0", "end-1c").strip()
        return obj.get().strip()

    def put_value(self, key, value):
        obj = self.vars[key]
        if isinstance(obj, tk.Text):
            obj.delete("1.0", "end")
            obj.insert("1.0", value)
        else:
            obj.set(value)

    def load_sender_settings(self):
        for key in ("sender_name", "sender_phone", "sender_address"):
            self.put_value(key, get_setting(key))

    def save_sender_settings(self):
        for key in ("sender_name", "sender_phone", "sender_address"):
            set_setting(key, self.get_value(key))
        messagebox.showinfo("Saved", "Sender/business details have been saved.")

    def clear_form(self):
        for key in self.vars:
            if key in ("sender_name", "sender_phone", "sender_address"):
                continue
            self.put_value(key, "")
        self.load_sender_settings()

    def generate(self):
        data = {key: self.get_value(key) for key in self.vars}
        if not data["order_id"] or not data["customer_name"] or not data["customer_address"]:
            messagebox.showwarning("Required details", "Please enter Order ID, Customer name and Full delivery address.")
            return
        if not data["sender_name"]:
            messagebox.showwarning("Sender details", "Please enter your business name.")
            return
        data["date"] = datetime.now().strftime("%d %b %Y")
        filename = safe_filename(data["order_id"]) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"
        path = PDF_DIR / filename
        try:
            create_pdf(data, path)
            with db_connect() as con:
                con.execute("""INSERT INTO waybills
                    (order_id,created_at,sender_name,sender_phone,sender_address,
                     customer_name,customer_phone,customer_address,amount,instructions,pdf_path)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (data["order_id"], datetime.now().isoformat(timespec="seconds"),
                     data["sender_name"], data["sender_phone"], data["sender_address"],
                     data["customer_name"], data["customer_phone"], data["customer_address"],
                     data["amount"], data["instructions"], str(path)))
            answer = messagebox.askyesno("Waybill created",
                f"Waybill PDF created successfully.\\n\\n{path}\\n\\nOpen the PDF now?")
            if answer:
                os.startfile(str(path))
        except Exception as exc:
            messagebox.showerror("Error", f"Could not create waybill:\\n{exc}")

    def show_history(self):
        win = tk.Toplevel(self)
        win.title("Waybill History")
        win.geometry("850x420")
        win.configure(bg="white")
        cols = ("order", "date", "customer", "amount", "file")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for col, label, width in [
            ("order", "Order ID", 120), ("date", "Created", 150),
            ("customer", "Customer", 180), ("amount", "Amount (LKR)", 120),
            ("file", "PDF file", 250)]:
            tree.heading(col, text=label)
            tree.column(col, width=width)
        tree.pack(fill="both", expand=True, padx=12, pady=12)
        with db_connect() as con:
            rows = con.execute("SELECT order_id,created_at,customer_name,amount,pdf_path FROM waybills ORDER BY id DESC").fetchall()
        for row in rows:
            tree.insert("", "end", values=(row[0], row[1].replace("T", " "), row[2], row[3], row[4]))

        def open_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select a waybill", "Please select a record.")
                return
            path = tree.item(sel[0], "values")[4]
            if os.path.exists(path):
                os.startfile(path)
            else:
                messagebox.showerror("File missing", "The PDF file could not be found.")
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(bar, text="OPEN SELECTED PDF", command=open_selected).pack(side="right")

if __name__ == "__main__":
    init_db()
    app = WaybillApp()
    app.mainloop()
