from flask import Flask, request, redirect, url_for, render_template_string, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super-secret-key"
DB_NAME = "project.db"


BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 0;
        }
        .navbar {
            background: #1f2937;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
        }
        .navbar a {
            color: white;
            text-decoration: none;
            margin-left: 15px;
        }
        .container {
            width: 80%;
            max-width: 900px;
            margin: 30px auto;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 0 14px rgba(0,0,0,0.08);
        }
        h1, h2 {
            margin-top: 0;
        }
        form {
            margin-bottom: 20px;
        }
        input, select {
            padding: 10px;
            margin: 8px 0;
            width: 100%;
            box-sizing: border-box;
        }
        button {
            padding: 10px 16px;
            border: none;
            background: #2563eb;
            color: white;
            border-radius: 6px;
            cursor: pointer;
        }
        button:hover {
            background: #1d4ed8;
        }
        .task {
            border: 1px solid #ddd;
            border-left: 5px solid #2563eb;
            padding: 15px;
            margin-bottom: 12px;
            border-radius: 8px;
            background: #fafafa;
        }
        .done {
            border-left-color: green;
            opacity: 0.75;
        }
        .meta {
            color: #555;
            font-size: 14px;
            margin-top: 6px;
        }
        .actions a {
            margin-right: 12px;
            text-decoration: none;
            color: #2563eb;
        }
        .actions a.delete {
            color: red;
        }
        .flash {
            padding: 10px;
            background: #fef3c7;
            border: 1px solid #facc15;
            margin-bottom: 15px;
            border-radius: 6px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .card {
            padding: 20px;
            border-radius: 10px;
            background: #f8fafc;
            border: 1px solid #e5e7eb;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div><strong>Heavy Python Project</strong></div>
        <div>
            {% if session.get("user_id") %}
                <a href="{{ url_for('dashboard') }}">Dashboard</a>
                <a href="{{ url_for('tasks') }}">Tasks</a>
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('register') }}">Register</a>
            {% endif %}
        </div>
    </div>

    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}
                    <div class="flash">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {{ content|safe }}
    </div>
</body>
</html>
"""


def render_page(content, title="App"):
    return render_template_string(BASE_HTML, content=content, title=title)


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            due_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def current_user():
    return session.get("user_id")


@app.route("/")
def home():
    if current_user():
        return redirect(url_for("dashboard"))
    content = """
        <h1>Welcome</h1>
        <p>This is a heavy Flask project with login, register, dashboard, and task manager.</p>
        <a href="/register"><button>Get Started</button></a>
    """
    return render_page(content, "Home")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            conn.close()
            flash("Registration successful. Please login.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("register"))

    content = """
        <h2>Register</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
    """
    return render_page(content, "Register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful.")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")
        return redirect(url_for("login"))

    content = """
        <h2>Login</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    """
    return render_page(content, "Login")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not current_user():
        return redirect(url_for("login"))

    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS count FROM tasks WHERE user_id = ?", (current_user(),)).fetchone()["count"]
    pending = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND status = 'Pending'",
        (current_user(),)
    ).fetchone()["count"]
    completed = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND status = 'Completed'",
        (current_user(),)
    ).fetchone()["count"]
    conn.close()

    content = f"""
        <h1>Dashboard</h1>
        <p>Welcome, <strong>{session.get("username")}</strong></p>
        <div class="grid">
            <div class="card">
                <h3>Total Tasks</h3>
                <p>{total}</p>
            </div>
            <div class="card">
                <h3>Pending Tasks</h3>
                <p>{pending}</p>
            </div>
            <div class="card">
                <h3>Completed Tasks</h3>
                <p>{completed}</p>
            </div>
        </div>
        <br>
        <a href="/tasks"><button>Manage Tasks</button></a>
    """
    return render_page(content, "Dashboard")


@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if not current_user():
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        priority = request.form["priority"]
        due_date = request.form["due_date"]

        if title:
            conn.execute("""
                INSERT INTO tasks (user_id, title, description, priority, due_date)
                VALUES (?, ?, ?, ?, ?)
            """, (current_user(), title, description, priority, due_date))
            conn.commit()
            flash("Task added successfully.")
        return redirect(url_for("tasks"))

    task_rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC",
        (current_user(),)
    ).fetchall()
    conn.close()

    task_html = ""
    for task in task_rows:
        task_html += f"""
            <div class="task {'done' if task['status'] == 'Completed' else ''}">
                <h3>{task['title']}</h3>
                <p>{task['description'] or 'No description'}</p>
                <div class="meta">
                    Priority: <strong>{task['priority']}</strong> |
                    Status: <strong>{task['status']}</strong> |
                    Due Date: <strong>{task['due_date'] or 'N/A'}</strong>
                </div>
                <div class="actions" style="margin-top:10px;">
                    <a href="/complete/{task['id']}">Mark Completed</a>
                    <a class="delete" href="/delete/{task['id']}">Delete</a>
                </div>
            </div>
        """

    content = f"""
        <h1>Task Manager</h1>
        <form method="POST">
            <input type="text" name="title" placeholder="Task title" required>
            <input type="text" name="description" placeholder="Task description">
            <select name="priority">
                <option>Low</option>
                <option selected>Medium</option>
                <option>High</option>
            </select>
            <input type="date" name="due_date">
            <button type="submit">Add Task</button>
        </form>

        <hr>
        <h2>Your Tasks</h2>
        {task_html if task_html else "<p>No tasks added yet.</p>"}
    """
    return render_page(content, "Tasks")


@app.route("/complete/<int:task_id>")
def complete(task_id):
    if not current_user():
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "UPDATE tasks SET status = 'Completed' WHERE id = ? AND user_id = ?",
        (task_id, current_user())
    )
    conn.commit()
    conn.close()
    flash("Task marked as completed.")
    return redirect(url_for("tasks"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    if not current_user():
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, current_user()))
    conn.commit()
    conn.close()
    flash("Task deleted.")
    return redirect(url_for("tasks"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)