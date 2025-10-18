from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ===========================
# DATABASE CONNECTION
# ===========================
try:
    db = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASS", "root"),
        database=os.environ.get("DB_NAME", "project_manager")
    )
    if db.is_connected():
        print("✅ Connected to MySQL Database")
except Exception as e:
    print("❌ Error connecting to database:", e)
    db = None  # prevent app crash

# ===========================
# ROUTES
# ===========================
@app.route('/')
def home():
    return render_template("index.html", title="Home")

@app.route('/dashboard')
def dashboard():
    if not db:
        return "Database not connected", 500

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total_projects FROM projects")
    total_projects = cursor.fetchone()['total_projects'] or 0

    cursor.execute("SELECT COUNT(*) AS total_tasks FROM tasks")
    total_tasks = cursor.fetchone()['total_tasks'] or 0

    cursor.execute("SELECT COUNT(*) AS completed_tasks FROM tasks WHERE status='Done'")
    completed_tasks = cursor.fetchone()['completed_tasks'] or 0

    cursor.close()
    return render_template(
        "dashboard.html",
        title="Dashboard",
        total_projects=total_projects,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks
    )

# -------------------- PROJECTS --------------------
@app.route('/projects')
def view_projects():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects ORDER BY id DESC")
    projects = cursor.fetchall()
    cursor.close()
    return render_template("projects.html", title="Projects", projects=projects)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        status = request.form['status']
        deadline = request.form['deadline']

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description, status, deadline) VALUES (%s, %s, %s, %s)",
            (name, description, status, deadline)
        )
        db.commit()
        cursor.close()
        return redirect('/projects')

    return render_template("add_project.html", title="Add Project")

@app.route('/edit_project/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects WHERE id=%s", (id,))
    project = cursor.fetchone()
    cursor.close()

    if not project:
        return "Project not found", 404

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        status = request.form['status']
        deadline = request.form['deadline']

        cursor = db.cursor()
        cursor.execute(
            "UPDATE projects SET name=%s, description=%s, status=%s, deadline=%s WHERE id=%s",
            (name, description, status, deadline, id)
        )
        db.commit()
        cursor.close()
        return redirect('/projects')

    return render_template("edit_project.html", title="Edit Project", project=project)

@app.route('/delete_project/<int:id>')
def delete_project(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM projects WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    return redirect('/projects')

# -------------------- TASKS --------------------
@app.route('/tasks')
def view_tasks():
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.id, t.title, t.status, t.deadline, p.name AS project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        ORDER BY t.id DESC
    """)
    tasks = cursor.fetchall()
    cursor.close()
    return render_template("tasks.html", title="Tasks", tasks=tasks)

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM projects")
    projects = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        project_id = request.form['project_id']
        title = request.form['title']
        description = request.form['description']
        status = request.form['status']
        deadline = request.form['deadline']

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tasks (project_id, title, description, status, deadline) VALUES (%s, %s, %s, %s, %s)",
            (project_id, title, description, status, deadline)
        )
        db.commit()
        cursor.close()
        return redirect('/tasks')

    return render_template("add_task.html", title="Add Task", projects=projects)

@app.route('/edit_task/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE id=%s", (id,))
    task = cursor.fetchone()
    cursor.close()

    if not task:
        return "Task not found", 404

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM projects")
    projects = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        project_id = request.form['project_id']
        title = request.form['title']
        description = request.form['description']
        status = request.form['status']
        deadline = request.form['deadline']

        cursor = db.cursor()
        cursor.execute(
            "UPDATE tasks SET project_id=%s, title=%s, description=%s, status=%s, deadline=%s WHERE id=%s",
            (project_id, title, description, status, deadline, id)
        )
        db.commit()
        cursor.close()
        return redirect('/tasks')

    return render_template("edit_task.html", title="Edit Task", task=task, projects=projects)

@app.route('/delete_task/<int:id>')
def delete_task(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    return redirect('/tasks')

# ===========================
# RUN THE APP
# ===========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
