from functools import wraps
from pathlib import Path
from uuid import uuid4
import hmac
import secrets

from flask import (
    Flask, abort, flash, redirect, render_template, request,
    send_from_directory, session, url_for
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from db import close_db, get_db, initialise_database, log_action

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.teardown_appcontext(close_db)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        initialise_database(force=False)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Política simples suficiente para este laboratório sem JavaScript inline.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; img-src 'self' data:; "
            "font-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        )
        return response

    def current_user():
        uid = session.get("user_id")
        if not uid:
            return None
        return get_db().execute(
            "SELECT id, username, email, full_name, role FROM users WHERE id = ?",
            (uid,),
        ).fetchone()

    @app.context_processor
    def inject_globals():
        return {"current_user": current_user(), "csrf_token": get_csrf_token}

    def get_csrf_token():
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return token

    def verify_csrf():
        supplied = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not supplied or not expected or not hmac.compare_digest(supplied, expected):
            abort(400, "Pedido inválido: token CSRF em falta ou incorreto.")

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Inicie sessão para continuar.", "warning")
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def role_required(*roles):
        def decorator(view):
            @wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                user = current_user()
                if not user or user["role"] not in roles:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route("/")
    def index():
        return redirect(url_for("dashboard" if session.get("user_id") else "login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            verify_csrf()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or len(username) > 50 or not password:
                flash("Credenciais inválidas.", "danger")
                return render_template("login.html"), 400

            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()

            if not user or not check_password_hash(user["password_hash"], password):
                flash("Utilizador ou palavra-passe incorretos.", "danger")
                return render_template("login.html"), 401

            session.clear()
            session["user_id"] = user["id"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = True
            log_action(user["id"], "LOGIN_SUCCESS", f"Utilizador {user['username']} iniciou sessão")
            flash("Sessão iniciada com sucesso.", "success")
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        verify_csrf()
        uid = session.get("user_id")
        log_action(uid, "LOGOUT", "Fim de sessão")
        session.clear()
        flash("Sessão terminada.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        user = current_user()
        return render_template("dashboard.html", user=user)

    @app.route("/profile")
    @login_required
    def profile():
        user = current_user()
        profile_row = None
        if user["role"] == "student":
            profile_row = get_db().execute(
                "SELECT class_name, address, phone FROM student_profiles WHERE user_id = ?",
                (user["id"],),
            ).fetchone()
        return render_template("profile.html", user=user, profile=profile_row)

    @app.route("/students/<int:user_id>")
    @login_required
    def student_detail(user_id):
        viewer = current_user()
        if viewer["role"] == "student" and viewer["id"] != user_id:
            abort(403)
        row = get_db().execute(
            """
            SELECT u.id, u.full_name, u.username, u.email, sp.class_name, sp.address, sp.phone
            FROM users u JOIN student_profiles sp ON sp.user_id = u.id
            WHERE u.id = ? AND u.role = 'student'
            """,
            (user_id,),
        ).fetchone()
        if not row:
            abort(404)
        log_action(viewer["id"], "VIEW_STUDENT", f"Consulta do aluno id={user_id}")
        return render_template("student_detail.html", student=row)

    @app.route("/grades")
    @login_required
    def grades():
        user = current_user()
        db = get_db()
        if user["role"] == "student":
            rows = db.execute(
                "SELECT subject, grade, updated_at FROM grades WHERE student_id = ? ORDER BY subject",
                (user["id"],),
            ).fetchall()
            title = "As minhas avaliações"
        else:
            rows = db.execute(
                """
                SELECT g.subject, g.grade, g.updated_at, u.full_name
                FROM grades g JOIN users u ON u.id = g.student_id
                ORDER BY u.full_name, g.subject
                """
            ).fetchall()
            title = "Avaliações dos alunos"
        return render_template("grades.html", grades=rows, title=title, role=user["role"])

    @app.route("/comments", methods=["GET", "POST"])
    @login_required
    def comments():
        user = current_user()
        db = get_db()
        if request.method == "POST":
            verify_csrf()
            body = request.form.get("body", "").strip()
            if not body or len(body) > 500:
                flash("O comentário deve ter entre 1 e 500 caracteres.", "danger")
            else:
                db.execute("INSERT INTO comments (user_id, body) VALUES (?, ?)", (user["id"], body))
                db.commit()
                log_action(user["id"], "CREATE_COMMENT", "Novo comentário publicado")
                flash("Comentário publicado.", "success")
                return redirect(url_for("comments"))
        rows = db.execute(
            """
            SELECT c.id, c.body, c.created_at, u.full_name
            FROM comments c JOIN users u ON u.id = c.user_id
            ORDER BY c.id DESC
            """
        ).fetchall()
        return render_template("comments.html", comments=rows)

    @app.route("/uploads", methods=["GET", "POST"])
    @login_required
    def uploads():
        user = current_user()
        db = get_db()
        if request.method == "POST":
            verify_csrf()
            f = request.files.get("file")
            if not f or not f.filename:
                flash("Selecione um ficheiro.", "danger")
            elif not allowed_file(f.filename):
                flash("Tipo de ficheiro não permitido. Use PDF, DOCX ou TXT.", "danger")
            else:
                original = secure_filename(f.filename)
                ext = original.rsplit(".", 1)[1].lower()
                stored = f"{uuid4().hex}.{ext}"
                f.save(Path(app.config["UPLOAD_FOLDER"]) / stored)
                db.execute(
                    "INSERT INTO uploads (user_id, original_name, stored_name) VALUES (?, ?, ?)",
                    (user["id"], original, stored),
                )
                db.commit()
                log_action(user["id"], "UPLOAD_FILE", f"Upload: {original}")
                flash("Ficheiro enviado com sucesso.", "success")
                return redirect(url_for("uploads"))

        if user["role"] == "student":
            rows = db.execute(
                "SELECT * FROM uploads WHERE user_id = ? ORDER BY id DESC", (user["id"],)
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT up.*, u.full_name FROM uploads up
                JOIN users u ON u.id = up.user_id ORDER BY up.id DESC
                """
            ).fetchall()
        return render_template("uploads.html", uploads=rows, role=user["role"])

    @app.route("/uploads/<int:upload_id>/download")
    @login_required
    def download_upload(upload_id):
        user = current_user()
        row = get_db().execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()
        if not row:
            abort(404)
        if user["role"] == "student" and row["user_id"] != user["id"]:
            abort(403)
        log_action(user["id"], "DOWNLOAD_FILE", f"Download upload id={upload_id}")
        return send_from_directory(
            app.config["UPLOAD_FOLDER"], row["stored_name"],
            as_attachment=True, download_name=row["original_name"]
        )

    @app.route("/teacher/students")
    @role_required("teacher", "admin")
    def teacher_students():
        rows = get_db().execute(
            """
            SELECT u.id, u.full_name, u.username, u.email, sp.class_name
            FROM users u JOIN student_profiles sp ON sp.user_id = u.id
            WHERE u.role = 'student' ORDER BY u.full_name
            """
        ).fetchall()
        return render_template("students.html", students=rows)

    @app.route("/teacher/grades/<int:student_id>", methods=["GET", "POST"])
    @role_required("teacher", "admin")
    def teacher_grade_student(student_id):
        db = get_db()
        teacher = current_user()
        student = db.execute(
            "SELECT id, full_name FROM users WHERE id = ? AND role = 'student'", (student_id,)
        ).fetchone()
        if not student:
            abort(404)

        if request.method == "POST":
            verify_csrf()
            subject = request.form.get("subject", "").strip()
            try:
                grade = float(request.form.get("grade", ""))
            except ValueError:
                grade = -1
            if not subject or len(subject) > 80 or not (0 <= grade <= 20):
                flash("Indique uma disciplina válida e uma nota entre 0 e 20.", "danger")
            else:
                db.execute(
                    "INSERT INTO grades (student_id, subject, grade, updated_by) VALUES (?, ?, ?, ?)",
                    (student_id, subject, grade, teacher["id"]),
                )
                db.commit()
                log_action(teacher["id"], "ADD_GRADE", f"Aluno id={student_id}, {subject}={grade}")
                flash("Avaliação registada.", "success")
                return redirect(url_for("teacher_grade_student", student_id=student_id))

        rows = db.execute(
            "SELECT subject, grade, updated_at FROM grades WHERE student_id = ? ORDER BY id DESC",
            (student_id,),
        ).fetchall()
        return render_template("teacher_grades.html", student=student, grades=rows)

    @app.route("/admin/users")
    @role_required("admin")
    def admin_users():
        rows = get_db().execute(
            "SELECT id, username, email, full_name, role, created_at FROM users ORDER BY id"
        ).fetchall()
        return render_template("admin_users.html", users=rows)

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, message=str(getattr(e, "description", "Pedido inválido."))), 400

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, message="Não tem autorização para aceder a este recurso."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="O recurso solicitado não foi encontrado."), 404

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("error.html", code=413, message="O ficheiro excede o limite de 2 MB."), 413

    return app


app = create_app()

if __name__ == "__main__":
    # Debug desativado de propósito. Este laboratório deve correr apenas em localhost.
    app.run(host="127.0.0.1", port=5000, debug=False)
