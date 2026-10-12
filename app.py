from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

# In-memory database lists for demonstration
students_db = [
    {
        "id": 1,
        "name": "Alice Smith",
        "email": "alice@student.com",
        "course": "Computer Science",
    },
    {
        "id": 2,
        "name": "Bob Jones",
        "email": "bob@student.com",
        "course": "Mathematics",
    },
]

announcements_db = [
    {
        "id": 1,
        "title": "Welcome Back!",
        "content": (
            "Semester registration is now open. Update your profiles via the"
            " mobile app."
        ),
    }
]


# --- Web Admin Interface (CRUD Operations) ---
@app.route("/admin")
def admin_dashboard():
  return render_template(
      "admin.html", students=students_db, announcements=announcements_db
  )


@app.route("/admin/student/add", methods=["POST"])
def admin_add_student():
  new_id = len(students_db) + 1
  name = request.form.get("name")
  email = request.form.get("email")
  course = request.form.get("course")
  if name and email:
    students_db.append(
        {"id": new_id, "name": name, "email": email, "course": course}
    )
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/student/delete/<int:student_id>", methods=["POST"])
def admin_delete_student(student_id):
  global students_db
  students_db = [s for s in students_db if s["id"] != student_id]
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/announcement/add", methods=["POST"])
def admin_add_announcement():
  new_id = len(announcements_db) + 1
  title = request.form.get("title")
  content = request.form.get("content")
  if title and content:
    announcements_db.append({"id": new_id, "title": title, "content": content})
  return redirect(url_for("admin_dashboard"))




# --- Root & Home Route ---
@app.route("/")
def home():
  return jsonify(
      {"status": "success", "message": "Student Portal API is running live!"}
  )




# --- Mobile App REST APIs ---
@app.route("/api/register", methods=["POST"])
def api_register():
  data = request.get_json()
  if not data or not data.get("email") or not data.get("name"):
    return (
        jsonify({"status": "error", "message": "Missing required fields"}),
        400,
    )

  # Check if email exists
  for s in students_db:
    if s["email"] == data["email"]:
      return jsonify({"status": "error", "message": "Email already registered"}), 400

  new_id = len(students_db) + 1
  new_student = {
      "id": new_id,
      "name": data["name"],
      "email": data["email"],
      "course": data.get("course", "General"),
  }
  students_db.append(new_student)
  return jsonify(
      {"status": "success", "message": "Registration successful", "student": new_student}
  ), 201


@app.route("/api/announcements", methods=["GET"])
def api_get_announcements():
  return jsonify({"status": "success", "announcements": announcements_db})


if __name__ == "__main__":
  app.run(debug=True)