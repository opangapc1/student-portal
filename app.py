import os
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables from a local .env file if it exists
load_dotenv()

app = Flask(__name__)


# Pulling multiple environment variables securely
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# You can also read custom configuration flags
app_mode = os.environ.get('FLASK_ENV')


db = SQLAlchemy(app)

# --- SQLAlchemy Models ---
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "course": self.course
        }

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content
        }

# Create tables inside application context
with app.app_context():
    db.create_all()


# --- Web Admin Interface (CRUD Operations) ---
@app.route("/admin")
def admin_dashboard():
    students_db = Student.query.all()
    announcements_db = Announcement.query.order_by(Announcement.id.desc()).all()
    return render_template(
        "admin.html", students=students_db, announcements=announcements_db
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


# --- Root & Home Route ---
@app.route("/")
def home():
    return jsonify({
        "status": "success", 
        "message": "Student Portal API with Environment Variables is running!"
    })


# --- Mobile App REST APIs ---
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


if __name__ == "__main__":
    app.run(debug=True)