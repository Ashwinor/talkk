from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "talkk_secret"

# ===== MAINTENANCE MODE =====
MAINTENANCE = True   # Default is ON
ADMIN_KEY = "admin2002"

# ===== DATABASE =====
FILE = "talkk_users.xlsx"

# Create Excel if not exists
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["Username", "Email", "Password"])
    df.to_excel(FILE, index=False)

# ===== ROUTES =====

@app.route("/")
def intro():
    if MAINTENANCE:
        return render_template("maintenance.html")
    return render_template("index.html")

# ----- MAINTENANCE TOGGLE -----

@app.route("/admin2002/on")
def site_on():
    global MAINTENANCE
    MAINTENANCE = False
    return "Talkk is now LIVE"

@app.route("/admin2002/off")
def site_off():
    global MAINTENANCE
    MAINTENANCE = True
    return "Talkk is now under maintenance"

# ----- AUTH SYSTEM -----

@app.route("/login", methods=["GET", "POST"])
def login():
    if MAINTENANCE:
        return render_template("maintenance.html")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        df = pd.read_excel(FILE)

        for index, row in df.iterrows():
            if row["Email"] == email and check_password_hash(row["Password"], password):
                return redirect(url_for("dashboard"))
        
        flash("Invalid Email or Password")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if MAINTENANCE:
        return render_template("maintenance.html")

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        df = pd.read_excel(FILE)

        if email in df["Email"].values:
            flash("Email already registered")
            return redirect(url_for("signup"))

        hashed = generate_password_hash(password)

        df.loc[len(df)] = [username, email, hashed]
        df.to_excel(FILE, index=False)

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/forgot")
def forgot():
    if MAINTENANCE:
        return render_template("maintenance.html")
    return render_template("forgot.html")

@app.route("/dashboard")
def dashboard():
    if MAINTENANCE:
        return render_template("maintenance.html")
    return render_template("dashboard.html")

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
