# ==============================================================================
# STUDENT PORTAL FLASK BACKEND - DESKTOP APP UPDATE & ADMIN UPLOAD LEVEL
# Includes: PostgreSQL SQLAlchemy, Admin Panel with .exe Uploader, & Version API
# ==============================================================================

import os
from flask import Flask, jsonify, redirect, render_template, request, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load local environment variables if a .env file exists (ignored safely on Render)
load_dotenv()

app = Flask(__name__)

# --- Environment Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure folder to store uploaded .exe application files on the server
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'releases')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# --- SQLAlchemy Database Models ---
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "course": self.course}

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "content": self.content}

class AppRelease(db.Model):
    __tablename__ = 'app_releases'
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    changelog = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "version": self.version,
            "download_url": f"https://student-portal-yllr.onrender.com/download/app/{self.filename}",
            "changelog": self.changelog or "Bug fixes and performance improvements."
        }

# Create tables within application context
with app.app_context():
    db.create_all()


# --- Web Admin Interface (CRUD Operations & App Upload) ---
@app.route("/admin")
def admin_dashboard():
    students_db = Student.query.all()
    announcements_db = Announcement.query.order_by(Announcement.id.desc()).all()
    latest_release = AppRelease.query.order_by(AppRelease.id.desc()).first()
    return render_template(
        "admin.html", 
        students=students_db, 
        announcements=announcements_db,
        latest_release=latest_release
    )


@app.route("/admin/student/add", methods=["POST"])
def admin_add_student():
    name = request.form.get("name")
    email = request.form.get("email")
    course = request.form.get("course")
    
    if name and email:
        existing = Student.query.filter_by(email=email).first()
        if not existing:
            new_student = Student(name=name, email=email, course=course)
            db.session.add(new_student)
            db.session.commit()
            
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/student/delete/<int:student_id>", methods=["POST"])
def admin_delete_student(student_id):
    student = Student.query.get(student_id)
    if student:
        db.session.delete(student)
        db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/announcement/add", methods=["POST"])
def admin_add_announcement():
    title = request.form.get("title")
    content = request.form.get("content")
    
    if title and content:
        new_announcement = Announcement(title=title, content=content)
        db.session.add(new_announcement)
        db.session.commit()
        
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/app/upload", methods=["POST"])
def admin_upload_app():
    version = request.form.get("version")
    changelog = request.form.get("changelog")
    file = request.files.get("exe_file")

    if version and file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save record in database
        new_release = AppRelease(version=version, filename=filename, changelog=changelog)
        db.session.add(new_release)
        db.session.commit()

    return redirect(url_for("admin_dashboard"))


# --- Root & Home Route ---
@app.route("/")
def home():
    return jsonify({
        "status": "success", 
        "message": "Student Portal API with Desktop App Uploader is live!"
    })


# --- Mobile & Desktop App REST APIs ---
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("name"):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    existing_student = Student.query.filter_by(email=data["email"]).first()
    if existing_student:
        return jsonify({"status": "error", "message": "Email already registered"}), 400

    new_student = Student(
        name=data["name"],
        email=data["email"],
        course=data.get("course", "General")
    )
    db.session.add(new_student)
    db.session.commit()

    return jsonify({
        "status": "success", 
        "message": "Registration successful", 
        "student": new_student.to_dict()
    }), 201


@app.route("/api/announcements", methods=["GET"])
def api_get_announcements():
    announcements = Announcement.query.order_by(Announcement.id.desc()).all()
    return jsonify({
        "status": "success", 
        "announcements": [a.to_dict() for a in announcements]
    })


# --- Desktop App Version Check & Download Endpoints ---
@app.route("/api/app-version", methods=["GET"])
def api_app_version():
    latest = AppRelease.query.order_by(AppRelease.id.desc()).first()
    if not latest:
        return jsonify({"status": "error", "message": "No releases found"}), 404

    return jsonify({
        "status": "success",
        "latest_version": latest.version,
        "download_url": f"https://student-portal-yllr.onrender.com/download/app/{latest.filename}",
        "changelog": latest.changelog
    }), 200


@app.route("/download/app/<path:filename>", methods=["GET"])
def download_app_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)