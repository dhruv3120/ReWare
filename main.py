import tkinter as tk
from tkinter import messagebox, scrolledtext
import sqlite3
import hashlib
from datetime import datetime
from urllib.request import urlopen
from PIL import Image, ImageTk
import io

# ---------- DB Setup ----------
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create fresh tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        points INTEGER DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS swap_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        item_name TEXT,
        item_points INTEGER,
        phone TEXT,
        address TEXT,
        pincode TEXT,
        swap_date TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_email TEXT,
        category TEXT,
        item_name TEXT,
        item_points INTEGER,
        image_url TEXT
    )
''')
conn.commit()

# ---------- App Setup ----------
app = tk.Tk()
app.geometry("850x750")
app.title("ReWear")

logged_in_user = None
search_var = tk.StringVar()

# ---------- Static Items ----------
def estimate_points(item_name):
    length = len(item_name.strip())
    if length <= 5:
        return 5
    elif length <= 10:
        return 10
    else:
        return 12

categorized_items = {
    "Men's Wear": [
        ("Denim Jacket", estimate_points("Denim Jacket"), "https://i.imgur.com/LN0YUN2.jpg"),
        ("Leather Boots", estimate_points("Leather Boots"), "https://i.imgur.com/NnKPhXJ.jpg")
    ],
    "Women's Wear": [
        ("Red Saree", estimate_points("Red Saree"), "https://i.imgur.com/LZoZfD7.jpg"),
        ("Designer Kurti", estimate_points("Designer Kurti"), "https://i.imgur.com/39sX3jz.jpg")
    ],
    "Kids Wear": [
        ("Cartoon Shirt", estimate_points("Cartoon Shirt"), "https://i.imgur.com/vMZ8GKR.jpg")
    ],
    "For Gen Z": [
        ("Oversized Hoodie", estimate_points("Oversized Hoodie"), "https://i.imgur.com/O9KfGVG.jpg")
    ],
    "For Millennials": [
        ("Formal Shirt", estimate_points("Formal Shirt"), "https://i.imgur.com/jIPyJ6G.jpg")
    ]
}

# ---------- Core Functions ----------
def update_points():
    cursor.execute("SELECT points FROM users WHERE email= ?", (logged_in_user,))
    pts = cursor.fetchone()
    if pts:
        points_label.config(text=f"Points: {pts[0]}")

def upload_item():
    win = tk.Toplevel(app)
    win.title("Upload Item")
    win.geometry("400x350")

    tk.Label(win, text="Item Name").pack(pady=5)
    name_entry = tk.Entry(win)
    name_entry.pack(pady=5, fill="x", padx=20)

    tk.Label(win, text="Category").pack(pady=5)
    cat_entry = tk.Entry(win)
    cat_entry.pack(pady=5, fill="x", padx=20)

    tk.Label(win, text="Image URL").pack(pady=5)
    img_entry = tk.Entry(win)
    img_entry.pack(pady=5, fill="x", padx=20)

    def save_item():
        name = name_entry.get()
        cat = cat_entry.get()
        url = img_entry.get()

        if not name or not cat or not url:
            messagebox.showerror("Error", "Please fill all fields")
            return

        pts = estimate_points(name)

        cursor.execute("INSERT INTO user_items (owner_email, category, item_name, item_points, image_url) VALUES (?, ?, ?, ?, ?)",
                       (logged_in_user, cat, name, pts, url))
        conn.commit()
        messagebox.showinfo("Success", "Item uploaded for swap!")
        win.destroy()
        load_user_uploaded_items()
        show_categories()

    tk.Button(win, text="Submit", command=save_item).pack(pady=20)

def load_user_uploaded_items():
    cursor.execute("SELECT category, item_name, item_points, image_url FROM user_items")
    for cat, name, pts, url in cursor.fetchall():
        if cat not in categorized_items:
            categorized_items[cat] = []
        if (name, pts, url) not in categorized_items[cat]:
            categorized_items[cat].append((name, pts, url))

def open_swap_form(item_name, item_points):
    win = tk.Toplevel(app)
    win.title("Swap Item")
    win.geometry("350x400")

    tk.Label(win, text="Phone Number").pack(pady=5)
    phone_entry = tk.Entry(win)
    phone_entry.pack(pady=5, fill="x", padx=20)

    tk.Label(win, text="Shipping Address").pack(pady=5)
    address_entry = tk.Entry(win)
    address_entry.pack(pady=5, fill="x", padx=20)

    tk.Label(win, text="Pincode").pack(pady=5)
    pincode_entry = tk.Entry(win)
    pincode_entry.pack(pady=5, fill="x", padx=20)

    def confirm():
        phone = phone_entry.get()
        address = address_entry.get()
        pincode = pincode_entry.get()

        if not phone or not address or not pincode:
            messagebox.showerror("Error", "Please fill all personal details")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute("INSERT INTO swap_requests (user_email, item_name, item_points, phone, address, pincode, swap_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (logged_in_user, item_name, item_points, phone, address, pincode, now))
            cursor.execute("UPDATE users SET points = points + ? WHERE email=?", (item_points, logged_in_user))
            conn.commit()
            update_points()
            messagebox.showinfo("Success", f"Swapped {item_name} successfully!")
            win.destroy()
        except sqlite3.OperationalError as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(win, text="Confirm Swap", command=confirm).pack(pady=20)

def show_items(category):
    # Clear browse_frame
    for widget in browse_frame.winfo_children():
        widget.destroy()
    tk.Label(browse_frame, text=category, font=("Arial", 18)).pack(pady=5)
    for item, pts, img_url in categorized_items.get(category, []):
        frame = tk.Frame(browse_frame, bd=1, relief="solid")
        frame.pack(pady=5, padx=10, fill="x")
        tk.Label(frame, text=f"{item} - Earn {pts} pts").pack(side="left", padx=10)
        tk.Button(frame, text="Swap", command=lambda i=item, p=pts: open_swap_form(i, p)).pack(side="right", padx=10)

def show_categories():
    for widget in browse_frame.winfo_children():
        widget.destroy()
    tk.Label(browse_frame, text="Browse Categories", font=("Arial", 18)).pack(pady=5)
    for cat in categorized_items.keys():
        tk.Button(browse_frame, text=cat, width=30, command=lambda c=cat: show_items(c)).pack(pady=5)

def show_profile():
    for widget in browse_frame.winfo_children():
        widget.destroy()
    tk.Label(browse_frame, text="User Profile", font=("Arial", 18)).pack(pady=10)
    cursor.execute("SELECT full_name, points FROM users WHERE email=?", (logged_in_user,))
    result = cursor.fetchone()
    full_name, points = result if result else ("N/A", 0)
    tk.Label(browse_frame, text=f"Name: {full_name}", font=("Arial", 14)).pack(pady=5)
    tk.Label(browse_frame, text=f"Total Points: {points}", font=("Arial", 14)).pack(pady=5)
    tk.Label(browse_frame, text="Swapped Items:", font=("Arial", 14)).pack(pady=10)
    cursor.execute("SELECT item_name FROM swap_requests WHERE user_email=?", (logged_in_user,))
    items = cursor.fetchall()
    if items:
        for item in items:
            tk.Label(browse_frame, text=f"• {item[0]}").pack()
    else:
        tk.Label(browse_frame, text="No items swapped yet.").pack()

def logout():
    global logged_in_user
    logged_in_user = None
    dashboard_frame.pack_forget()
    login_frame.pack(pady=30)

# ---------- Authentication ----------
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login():
    global logged_in_user
    email = login_email.get()
    password = login_pass.get()
    if not email or not password:
        messagebox.showerror("Error", "All fields required")
        return
    hashed = hash_password(password)
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hashed))
    result = cursor.fetchone()
    if result:
        logged_in_user = email
        login_frame.pack_forget()
        update_points()
        dashboard_frame.pack(pady=10, fill="both", expand=True)
        show_categories()
    else:
        messagebox.showerror("Error", "Invalid credentials")

def register():
    name = reg_name.get()
    email = reg_email.get()
    password = reg_pass.get()
    confirm = reg_confirm.get()
    if not name or not email or not password or not confirm:
        messagebox.showerror("Error", "Please fill all fields")
        return
    if password != confirm:
        messagebox.showerror("Error", "Passwords do not match")
        return
    hashed = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)", (name, email, hashed))
        conn.commit()
        messagebox.showinfo("Success", "Registered successfully!")
        switch_to_login()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Email already exists")

def switch_to_register():
    login_frame.pack_forget()
    register_frame.pack(pady=30)

def switch_to_login():
    register_frame.pack_forget()
    login_frame.pack(pady=30)

# ---------- Login UI ----------
login_frame = tk.Frame(app)
tk.Label(login_frame, text="Welcome to ReWear", font=("Arial", 24)).pack(pady=10)
login_email = tk.Entry(login_frame, width=30)
login_email.pack(pady=10)
login_email.insert(0, "Email")
login_pass = tk.Entry(login_frame, width=30, show="*")
login_pass.pack(pady=10)
login_pass.insert(0, "Password")
tk.Button(login_frame, text="Login", command=login).pack(pady=20)
tk.Label(login_frame, text="Don't have an account?").pack()
tk.Button(login_frame, text="Register here", command=switch_to_register, fg="blue", relief="flat").pack()

# ---------- Register UI ----------
register_frame = tk.Frame(app)
tk.Label(register_frame, text="Register", font=("Arial", 24)).pack(pady=10)
reg_name = tk.Entry(register_frame, width=30)
reg_name.pack(pady=10)
reg_name.insert(0, "Full Name")
reg_email = tk.Entry(register_frame, width=30)
reg_email.pack(pady=10)
reg_email.insert(0, "Email")
reg_pass = tk.Entry(register_frame, width=30, show="*")
reg_pass.pack(pady=10)
reg_pass.insert(0, "Password")
reg_confirm = tk.Entry(register_frame, width=30, show="*")
reg_confirm.pack(pady=10)
reg_confirm.insert(0, "Confirm Password")
tk.Button(register_frame, text="Register", command=register).pack(pady=20)
tk.Label(register_frame, text="Already have an account?").pack()
tk.Button(register_frame, text="Login here", command=switch_to_login, fg="blue", relief="flat").pack()

# ---------- Dashboard UI ----------
dashboard_frame = tk.Frame(app)
navbar = tk.Frame(dashboard_frame)
navbar.pack(fill="x", pady=5)
tk.Button(navbar, text="Browse Categories", command=show_categories).pack(side="left", padx=10)
tk.Button(navbar, text="Profile", command=show_profile).pack(side="left", padx=10)
tk.Button(navbar, text="Upload Item", command=upload_item).pack(side="left", padx=10)
tk.Button(navbar, text="Logout", command=logout).pack(side="right", padx=10)
points_label = tk.Label(dashboard_frame, text="Points: 0", font=("Arial", 16))
points_label.pack()

# Scrollable frame for browsing
browse_canvas = tk.Canvas(dashboard_frame, width=700, height=500)
browse_scrollbar = tk.Scrollbar(dashboard_frame, orient="vertical", command=browse_canvas.yview)
browse_frame = tk.Frame(browse_canvas)

browse_frame.bind(
    "<Configure>",
    lambda e: browse_canvas.configure(
        scrollregion=browse_canvas.bbox("all")
    )
)

browse_canvas.create_window((0, 0), window=browse_frame, anchor="nw")
browse_canvas.configure(yscrollcommand=browse_scrollbar.set)

browse_canvas.pack(side="left", fill="both", expand=True)
browse_scrollbar.pack(side="right", fill="y")

# ---------- Show login initially ----------
login_frame.pack(pady=30)

# ---------- Mainloop ----------
app.mainloop()
