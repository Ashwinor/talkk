from flask import Flask, render_template, request, redirect, flash, session
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "talkk_secret"

ADMIN_PASSWORD = "admin2002"
MAINT_FILE = "maintenance.txt"
DB = "users.db"

# =======================
# DATABASE
# =======================
def db():
    return sqlite3.connect(DB)

# Users table
if not os.path.exists(DB):
    conn = db()
    conn.execute("""
    CREATE TABLE users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

# Notifications table (CRITICAL)
conn = db()
conn.execute("""
CREATE TABLE IF NOT EXISTS notifications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    text TEXT,
    is_read INTEGER DEFAULT 0
)
""")
conn.commit()
conn.close()

# =======================
# MAINTENANCE MODE
# =======================
def get_maintenance():
    if not os.path.exists(MAINT_FILE):
        open(MAINT_FILE, "w").write("OFF")
    return open(MAINT_FILE).read().strip() == "ON"

def set_maintenance(state):
    open(MAINT_FILE, "w").write("ON" if state else "OFF")

@app.before_request
def maintenance_block():
    if get_maintenance() and not session.get("admin"):
        if not request.path.startswith(("/admin", "/static", "/api")):
            return render_template("maintenance.html")

# =======================
# ROUTES
# =======================

@app.route("/")
def intro():
    return render_template("index.html")

@app.route("/splash")
def splash():
    return render_template("splash.html")

# ---------- ADMIN ----------
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin_panel")
        flash("Wrong password")
    return render_template("admin.html")

@app.route("/admin_panel")
def admin_panel():
    if not session.get("admin"):
        return redirect("/admin")
    return render_template("admin_panel.html", maintenance=get_maintenance())

@app.route("/admin2002on", methods=["POST"])
def admin_on():
    if session.get("admin"):
        set_maintenance(False)
    return redirect("/admin_panel")

@app.route("/admin2002off", methods=["POST"])
def admin_off():
    if session.get("admin"):
        set_maintenance(True)
    return redirect("/admin_panel")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if get_maintenance() and not session.get("admin"):
        return render_template("maintenance.html")

    if request.method == "POST":
        u = request.form["username"].strip()
        e = request.form["email"].strip()
        p = request.form["password"]

        if len(u) > 15:
            flash("Username must be 15 characters or less")
            return redirect("/signup")

        conn = db()

        if conn.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
            conn.close()
            flash("Username already exists")
            return redirect("/signup")

        if conn.execute("SELECT 1 FROM users WHERE email=?", (e,)).fetchone():
            conn.close()
            flash("Email already exists")
            return redirect("/signup")

        hashed = generate_password_hash(p)
        conn.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",(u,e,hashed))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if get_maintenance() and not session.get("admin"):
        return render_template("maintenance.html")

    if request.method == "POST":
        e = request.form["email"]
        p = request.form["password"]

        conn = db()
        user = conn.execute("SELECT username,password FROM users WHERE email=?", (e,)).fetchone()
        conn.close()

        if not user:
            flash("Email not found")
        elif not check_password_hash(user[1], p):
            flash("Wrong password")
        else:
            session["user"] = user[0]

            # 🔥 Add demo notifications ONCE per login
            conn = db()
            conn.execute("INSERT INTO notifications(username,text) VALUES(?,?)",
                         (session["user"], "Welcome to Talkk 👋"))
            conn.execute("INSERT INTO notifications(username,text) VALUES(?,?)",
                         (session["user"], "You have a new follower"))
            conn.commit()
            conn.close()

            return redirect("/home")

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    response = redirect("/login")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ---------- HOME ----------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("home/home.html", user=session["user"])

# ---------- VIDEO ----------
@app.route("/video")
def video():
    if "user" not in session:
        return redirect("/login")
    return render_template("home/video.html")

# ===========================
# 🔔 NOTIFICATIONS API
# ===========================

@app.route("/api/notifications")
def get_notifications():
    if "user" not in session:
        return {"error":"login required"}

    conn = db()
    rows = conn.execute(
        "SELECT id,text,is_read FROM notifications WHERE username=? ORDER BY id DESC",
        (session["user"],)
    ).fetchall()
    conn.close()

    return {
        "notifications":[
            {"id":r[0],"text":r[1],"read":bool(r[2])} for r in rows
        ]
    }

@app.route("/api/read_all", methods=["POST"])
def read_all():
    if "user" not in session:
        return {"error":"login"}

    conn = db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE username=?", (session["user"],))
    conn.commit()
    conn.close()
    return {"ok":True}

@app.route("/api/delete/<int:nid>", methods=["POST"])
def delete_notification(nid):
    if "user" not in session:
        return {"error":"login"}

    conn = db()
    conn.execute(
        "DELETE FROM notifications WHERE id=? AND username=?",
        (nid,session["user"])
    )
    conn.commit()
    conn.close()
    return {"ok":True}

# =======================
# RUN
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
