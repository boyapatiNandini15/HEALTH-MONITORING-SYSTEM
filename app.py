rom flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import os
import joblib
import numpy as np
app = Flask(__name__)
app.config["SECRET_KEY"] = "health-monitor-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///health.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    bmi = db.Column(db.Float)
    blood_pressure = db.Column(db.String(20))
    heart_rate = db.Column(db.Float)
    blood_sugar = db.Column(db.Float)
    sleep_hours = db.Column(db.Float)
    activity_minutes = db.Column(db.Float)
    risk = db.Column(db.String(50))
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    available_time = db.Column(db.String(100))
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    doctor_id = db.Column(db.Integer)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    reason = db.Column(db.String(300))
    status = db.Column(db.String(50), default="Confirmed")
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("register"))
        hashed_password = generate_password_hash(password)
        user = User(
            name=name,
            email=email,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful.")
        return redirect(url_for("login"))
    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
@app.route("/dashboard")
@login_required
def dashboard():
    records = HealthRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(
        HealthRecord.id.desc()
    ).all()
    appointments = Appointment.query.filter_by(
        user_id=current_user.id
    ).all()
    return render_template(
        "dashboard.html",
        records=records,
        appointments=appointments
    )
@app.route("/health", methods=["GET", "POST"])
@login_required
def health():
    if request.method == "POST":
        age = int(request.form["age"])
        weight = float(request.form["weight"])
        height = float(request.form["height"])
        blood_pressure = request.form["blood_pressure"]
        heart_rate = float(request.form["heart_rate"])
        blood_sugar = float(request.form["blood_sugar"])
        sleep_hours = float(request.form["sleep_hours"])
        activity_minutes = float(
            request.form["activity_minutes"]
        )
        height_m = height / 100
        bmi = weight / (height_m * height_m)
        if bmi < 18.5:
            risk = "Low"
        elif bmi < 25:
            risk = "Normal"
        elif bmi < 30:
            risk = "Moderate"
        else:
            risk = "High"
        record = HealthRecord(
            user_id=current_user.id,
            age=age,
            weight=weight,
            height=height,
            bmi=round(bmi, 2),
            blood_pressure=blood_pressure,
            heart_rate=heart_rate,
            blood_sugar=blood_sugar,
            sleep_hours=sleep_hours,
            activity_minutes=activity_minutes,
            risk=risk
        )
        db.session.add(record)
        db.session.commit()
        return redirect(url_for("prediction"))
    return render_template("health.html")
@app.route("/prediction")
@login_required
def prediction():
    record = HealthRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(
        HealthRecord.id.desc()
    ).first()
    if record is None:
        flash("Please enter your health information first.")
        return redirect(url_for("health"))
    risk = record.risk
    if risk == "High":
        recommendation = (
            "Please consider consulting a qualified healthcare professional."
        )
    elif risk == "Moderate":
        recommendation = (
            "Maintain healthy habits and monitor your health regularly."
        )
    else:
        recommendation = (
            "Continue maintaining healthy lifestyle habits."
        )
    return render_template(
        "prediction.html",
        record=record,
        risk=risk,
        recommendation=recommendation
    )
@app.route("/doctors")
@login_required
def doctors():
    doctors = Doctor.query.all()
    return render_template(
        "doctors.html",
        doctors=doctors
    )
@app.route("/appointment/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == "POST":
        date = request.form["date"]
        time = request.form["time"]
        reason = request.form["reason"]
        new_appointment = Appointment(
            user_id=current_user.id,
            doctor_id=doctor.id,
            date=date,
            time=time,
            reason=reason,
            status="Confirmed"
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash("Appointment booked successfully.")
        return redirect(url_for("appointments"))
    return render_template(
        "appointment.html",
        doctor=doctor
    )
@app.route("/appointments")
@login_required
def appointments():
    appointments = Appointment.query.filter_by(
        user_id=current_user.id
    ).all()
    return render_template(
        "appointments.html",
        appointments=appointments
    )
with app.app_context():
    db.create_all()
    if Doctor.query.count() == 0:
        doctor1 = Doctor(
            name="Dr. Anil Kumar",
            specialization="General Physician",
            experience=10,
            available_time="10:00 AM - 1:00 PM"
        )
        doctor2 = Doctor(
            name="Dr. Priya Sharma",
            specialization="Cardiologist",
            experience=8,
            available_time="2:00 PM - 5:00 PM"
        )
        doctor3 = Doctor(
            name="Dr. Rahul Reddy",
            specialization="Nutrition Specialist",
            experience=7,
            available_time="10:00 AM - 2:00 PM"
        )
        db.session.add_all([
            doctor1,
            doctor2,
            doctor3
        ])
        db.session.commit()
if __name__ == "__main__":
    app.run(debug=True)
