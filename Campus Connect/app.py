from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import random
import time
import smtplib
from email.mime.text import MIMEText
from database import create_db

otp_expiry = 300

app = Flask(__name__, template_folder="templates")
CORS(app)

create_db()

otp_storage = {}

# ---------------- FRONTEND ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/setup")
def setup():
    return render_template("setup.html")

@app.route("/activity")
def activity():
    return render_template("activity.html")

@app.route("/update")
def update():
    return render_template("update.html")

#EMAIL

EMAIL = "divyacse2029@gmail.com"
EMAIL_PASSWORD = "zbjp ugxe yitz ppwv"


def send_email_otp(receiver, otp):
    subject = "Campus Connect OTP"
    body = f"Your OTP is: {otp}\nValid for 5 minutes"

    msg = MIMEText(body)
    msg["subject"] = subject
    msg["from"] = EMAIL
    msg["to"] = receiver

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


# OTP api

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    if not email.endswith("@srmist.edu.in"):
        return jsonify({"error": "Use SRM mail only"}), 403

    otp = random.randint(100000, 999999)

    otp_storage[email] = {
        "otp": otp,
        "time": time.time()
    }

    send_email_otp(email, otp)

    return jsonify({"message": "OTP sent"})


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()

    email = data.get("email")
    user_otp = data.get("otp")

    if not email or not user_otp:
        return jsonify({"error": "Missing details"}), 400

    try:
        user_otp = int(user_otp)
    except:
        return jsonify({"error": "OTP must be number"}), 400

    if email not in otp_storage:
        return jsonify({"error": "OTP not found"}), 404

    saved_otp = otp_storage[email]["otp"]
    saved_time = otp_storage[email]["time"]

    if time.time() - saved_time > otp_expiry:
        del otp_storage[email]
        return jsonify({"error": "OTP expired"}), 403

    if user_otp == saved_otp:
        del otp_storage[email]
        return jsonify({"message": "Login Successful"}), 200

    return jsonify({"error": "Invalid OTP"}), 401


#Profile Api

@app.route("/api/save-profile", methods=["POST"])
def save_profile():
    data = request.get_json()

    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users 
            (email, username, name, department, degree, year, gender, bio, interests)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            data["email"],
            data["username"],
            data["name"],
            data["department"],
            data["degree"],
            data["year"],
            data["gender"],
            data["bio"],
            data["interest"]
        ))

        conn.commit()
        conn.close()

        return jsonify({"message": "Profile saved"}), 200

    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409


@app.route("/api/get-profile", methods=["POST"])
def get_profile():
    data = request.get_json()
    email = data["email"]

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    conn.close()

    if not user:
        return jsonify({"error": "Profile not found"}), 404

    profile = {
        "email": user[0],
        "username": user[1],
        "name": user[2],
        "department": user[3],
        "degree": user[4],
        "year": user[5],
        "gender": user[6],
        "bio": user[7],
        "interest": user[8]
    }

    return jsonify(profile)

@app.route("/api/update-profile", methods=["POST"])
def update_profile():
    data = request.get_json()
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users
        SET username=?,
        name=?,
        department=?,
        degree=?,
        year=?,
        gender=?,
        bio=?,
        interests=?
    WHERE email=?""",
    (
        data["username"],
        data["name"],
        data["department"],
        data["degree"],
        data["year"],
        data["gender"],
        data["bio"],
        data["interest"],
        data["email"]
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message":"Profile Updated!"})


#follow api
@app.route("/api/send-follow",methods=["POST"])
def send_follow():
    data = request.get_json()
    
    sender = data["sender"]
    receiver = data["receiver"]
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO follows(sender,receiver,status)
    VALUES(?,?,?)
    """,(sender,receiver,"pending"))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message":"follow request sent"})

@app.route("/api/accept-follow",methods=["POST"])
def accept_follow():
    data = request.get_json()
    
    sender = data["sender"]
    receiver = data["receiver"]
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE follows
    SET status='accepted'
    WHERE sender=? AND receiver=?
    """,(sender,receiver))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message":"Follow request accepted"})

#send/accept follow api
@app.route("/api/send-follow-request",methods=["POST"])
def send_follow_request():
    data = request.get_json()
    
    sender = data["sender"]
    receiver = data["receiver"]
    
    if not sender or not receiver:
        return jsonify({"Error":"Messing Feilds"}),400
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO follow_requests VALUES (?,?)""",(sender,receiver))
        
        conn.commit()
        conn.close()
        
        return jsonify({"message":"Follow request sent"})
        
    except sqlite3.IntegrityError:
        return jsonify({"error":"request alredy exists"}),409

@app.route("/api/get-follow-requests",methods=["POST"])
def get_follow_request():
    data = request.get_json()
    email = data["email"]
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT sender_email FROM follow_requests WHERE receiver_email = ?
    """, (email,))
    
    requests = cursor.fetchall()
    conn.close()
    
    result = [r[0] for r in request]
    
    return jsonify(result)

@app.route("/api/accept-follow-request",methods=["POST"])
def accept_follow_request():
    data = request.get_json()
    
    sender = data.get("sender")
    receiver = data.get("receiver")
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    DELETE FROM follow_requests 
    WHERE sender_email=? AND receiver_email=?
    """, (sender, receiver))
    
    
    cursor.execute("""
    INSERT INTO followers VALUES (?,?)
    """, (sender, receiver))
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Follow request accepted"}), 200

#get follower count
@app.route("/api/follower-count",methods=["POSt"])
def follower_count():
    data = request.get_json()
    email= data.get("email")
    
    conn = sqlite3.connect("users.db")
    cursor= conn.cursor()
    
    cursor.execute("""
    SELECT COUNT(*) FROM followers WHERE following_email=?
    """, (email,))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({"count":count})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000,debug=True)