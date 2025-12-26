from flask import Flask, render_template, request, redirect, flash, session
import pandas as pd
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "talkk_secret"

# ===== ADMIN =====
ADMIN_PASSWORD = "admin2002"
MAINT_FILE = "maintenance.txt"

def get_maintenance():
    if not os.path.exists(MAINT_FILE):
        with open(MAINT_FILE, "w") as f:
            f.write("OFF")
        return False
    with open(MAINT_FILE, "r") as f:
        return f.read().strip() == "ON"

def set_maintenance(state):
    with open(MAINT_FILE, "w") as f:
        f.write("ON" if state else "OFF")

# ===== DATABASE =====
FILE = "talkk_users.xlsx"

if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["Username","Email","Password"])
    df.to_excel(FILE, index=False)

# ===== ROUTES =====

@app.route("/")
def intro():
    if get_maintenance() and not session.get("admin"):
        return render_template("maintenance.html")
    return render_template("index.html")

# ---------- ADMIN ----------
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form["password"]==ADMIN_PASSWORD:
            session["admin"]=True
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

# ---------- AUTH ----------

@app.route("/signup", methods=["GET","POST"])
def signup():
    if get_maintenance() and not session.get("admin"):
        return render_template("maintenance.html")

    if request.method=="POST":
        username=request.form["username"]
        email=request.form["email"]
        password=request.form["password"]

        df=pd.read_excel(FILE)
        if email in df["Email"].values:
            flash("Email already exists")
            return redirect("/signup")

        hashed=generate_password_hash(password)
        df.loc[len(df)]=[username,email,hashed]
        df.to_excel(FILE,index=False)

        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if get_maintenance() and not session.get("admin"):
        return render_template("maintenance.html")

    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]

        df=pd.read_excel(FILE)
        for _,row in df.iterrows():
            if row["Email"]==email and check_password_hash(row["Password"],password):
                session["user"]=row["Username"]
                return redirect("/home")

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/forgot")
def forgot():
    return render_template("forgot.html")

# ---------- HOME ----------
@app.route("/home")
def home():
    if not session.get("user"):
        return redirect("/login")
    return render_template("home/home.html", user=session["user"])

# ===== RUN =====
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))


