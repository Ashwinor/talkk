from flask import Flask, render_template, request, redirect, flash, session
import pandas as pd
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "talkk_secret"

# ===== ADMIN =====
ADMIN_PASSWORD = "admin2002"
maintenance = False   # Start online

# ===== DATABASE =====
FILE = "talkk_users.xlsx"
if not os.path.exists(FILE):
    pd.DataFrame(columns=["Username","Email","Password"]).to_excel(FILE,index=False)

# ===== ROUTES =====

@app.route("/")
def intro():
    if maintenance and not session.get("admin"):
        return render_template("maintenance.html")
    return render_template("index.html")

@app.route("/splash")
def splash():
    if maintenance and not session.get("admin"):
        return render_template("maintenance.html")
    return render_template("splash.html")

# ===== HOME UI =====

@app.route("/home")
def home():
    if maintenance and not session.get("admin"):
        return render_template("maintenance.html")
    return render_template("home/home.html")

@app.route("/home/<page>")
def home_pages(page):
    allowed = ["video", "chat", "profile", "settings"]
    if page not in allowed:
        return redirect("/home")
    return render_template(f"home/{page}.html")

# ===== ADMIN =====

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
    return render_template("admin_panel.html", maintenance=maintenance)

@app.route("/admin2002on", methods=["POST"])
def admin_on():
    global maintenance
    if session.get("admin"):
        maintenance = False
    return redirect("/admin_panel")

@app.route("/admin2002off", methods=["POST"])
def admin_off():
    global maintenance
    if session.get("admin"):
        maintenance = True
    return redirect("/admin_panel")

# ===== AUTH =====

@app.route("/login", methods=["GET","POST"])
def login():
    if maintenance and not session.get("admin"):
        return render_template("maintenance.html")

    if request.method=="POST":
        df = pd.read_excel(FILE)
        for _,row in df.iterrows():
            if row["Email"]==request.form["email"] and check_password_hash(row["Password"],request.form["password"]):
                return redirect("/home")
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if maintenance and not session.get("admin"):
        return render_template("maintenance.html")

    if request.method=="POST":
        df = pd.read_excel(FILE)
        if request.form["email"] in df["Email"].values:
            flash("Email already exists")
            return redirect("/signup")

        df.loc[len(df)] = [
            request.form["username"],
            request.form["email"],
            generate_password_hash(request.form["password"])
        ]
        df.to_excel(FILE,index=False)
        return redirect("/login")

    return render_template("signup.html")

@app.route("/forgot")
def forgot():
    if maintenance and not session.get("admin"):
        return render_template("maintenance.html")
    return render_template("forgot.html")

@app.route("/dashboard")
def dashboard():
    if maintenance and not session.get("admin"):
        return render_template("maintenance.html")
    return render_template("dashboard.html")

# ===== RUN =====
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
