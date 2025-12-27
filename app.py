from flask import Flask, render_template, request, redirect, flash, session
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "talkk_secret"

ADMIN_PASSWORD = "admin2002"
MAINT_FILE = "maintenance.txt"
DB = "users.db"

# =======================
#  DATABASE
# =======================
def db():
    return sqlite3.connect(DB)

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

# =======================
#  MAINTENANCE MODE
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
        if not request.path.startswith(("/admin", "/static")):
            return render_template("maintenance.html")

# =======================
#  ROUTES
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
        u = request.form["username"]
        e = request.form["email"]
        p = generate_password_hash(request.form["password"])

        conn = db()
        try:
            conn.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",(u,e,p))
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            conn.close()
            flash("Email already exists")

    return render_template("signup.html")

# ---------- LOGIN (SMART ERRORS) ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if get_maintenance() and not session.get("admin"):
        return render_template("maintenance.html")

    if request.method == "POST":
        e = request.form["email"]
        p = request.form["password"]

        conn = db()
        user = conn.execute("SELECT username,password FROM users WHERE email=?",(e,)).fetchone()
        conn.close()

        if not user:
            flash("Email not found")
        elif not check_password_hash(user[1], p):
            flash("Wrong password")
        else:
            session["user"] = user[0]
            return redirect("/home")

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    r = redirect("/login")
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# ---------- FORGOT ----------
@app.route("/forgot")
def forgot():
    return render_template("forgot.html")

# ---------- HOME ----------
@app.route("/home")
def home():
    if not session.get("user"):
        return redirect("/login")
    return render_template("home/home.html", user=session["user"])

# ---------- VIDEO ----------
@app.route("/video")
def video():
    if not session.get("user"):
        return redirect("/login")
    return render_template("home/video.html")

# =======================
#  RUN
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

