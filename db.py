import sqlite3
from pathlib import Path
from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_profiles (
    user_id INTEGER PRIMARY KEY,
    class_name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    grade REAL NOT NULL CHECK (grade >= 0 AND grade <= 20),
    updated_by INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def log_action(user_id, action, detail=""):
    db = get_db()
    db.execute(
        "INSERT INTO audit_logs (user_id, action, detail) VALUES (?, ?, ?)",
        (user_id, action, detail[:500]),
    )
    db.commit()


def initialise_database(force=False):
    db_path = Path(current_app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    Path(current_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    if db_path.exists() and not force:
        return False
    if db_path.exists() and force:
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    demo_users = [
        ("ana", "ana@escola.local", "Ana Silva", "AlunoAna!2026", "student"),
        ("joao", "joao@escola.local", "João Costa", "AlunoJoao!2026", "student"),
        ("prof1", "prof1@escola.local", "Prof. Marta Sousa", "Professor!2026", "teacher"),
        ("admin", "admin@escola.local", "Administrador Local", "Admin!2026Lab", "admin"),
    ]

    ids = {}
    for username, email, name, password, role in demo_users:
        cur = conn.execute(
            "INSERT INTO users (username, email, full_name, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (username, email, name, generate_password_hash(password), role),
        )
        ids[username] = cur.lastrowid

    profiles = [
        (ids["ana"], "12.º TDS", "Rua Exemplo 1, Fundão", "910000001"),
        (ids["joao"], "12.º TDS", "Rua Exemplo 2, Fundão", "910000002"),
    ]
    conn.executemany(
        "INSERT INTO student_profiles (user_id, class_name, address, phone) VALUES (?, ?, ?, ?)",
        profiles,
    )

    grades = [
        (ids["ana"], "Programação", 16.0, ids["prof1"]),
        (ids["ana"], "Redes", 15.0, ids["prof1"]),
        (ids["joao"], "Programação", 14.0, ids["prof1"]),
        (ids["joao"], "Redes", 17.0, ids["prof1"]),
    ]
    conn.executemany(
        "INSERT INTO grades (student_id, subject, grade, updated_by) VALUES (?, ?, ?, ?)",
        grades,
    )

    comments = [
        (ids["ana"], "Gostei muito desta aula de segurança de software."),
        (ids["joao"], "O laboratório ajuda a perceber onde surgem os riscos."),
    ]
    conn.executemany("INSERT INTO comments (user_id, body) VALUES (?, ?)", comments)
    conn.commit()
    conn.close()
    return True
