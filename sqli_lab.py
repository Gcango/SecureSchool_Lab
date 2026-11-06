"""
Laboratório de Injeção SQL vs. Prepared Statements (versão web da demonstração de terminal).

Cada pedido usa uma base SQLite em memória, isolada da base real da aplicação,
por isso nenhum ataque testado aqui afeta os dados do SecureSchool Lab.
"""
import sqlite3

DEMO_USERS = [
    (1, "maria", "hash123", "maria@escola.pt", "aluna"),
    (2, "joao", "hash456", "joao@escola.pt", "aluno"),
    (3, "prof_gamboa", "admin123", "gamboa@escola.pt", "professor"),
    (4, "admin", "superadmin", "admin@escola.pt", "administrador"),
]

COLUMNS = ("id", "username", "password", "email", "role")

SAFE_QUERY = "SELECT * FROM users WHERE username = ?"

# Cenários da demonstração completa (equivalente a demonstrar_ataque()).
SCENARIOS = [
    ("Cenário normal (input legítimo)", "maria"),
    ("Ataque básico — devolve todos os utilizadores", "' OR '1'='1"),
    ("Ataque com comentário SQL — '--' ignora o resto da query", "admin' --"),
]

# Sugestões de inputs (equivalente à opção 5 do menu).
SUGGESTIONS = [
    ("maria", "Input legítimo"),
    ("' OR '1'='1", "Retorna todos"),
    ("' OR '1'='1' --", "Com comentário"),
    ("admin' --", "Entra como admin"),
    ("' UNION SELECT 1,2,3,4,5 --", "Explora a estrutura (5 colunas)"),
    ("' UNION SELECT id, username, password, email, role FROM users --", "Fuga de passwords"),
    ("'; DROP TABLE users; --", "Tentativa de apagar a tabela"),
]


def _demo_connection():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, role TEXT)"
    )
    conn.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", DEMO_USERS)
    conn.commit()
    return conn


def _run(query, params=()):
    conn = _demo_connection()
    try:
        rows = conn.execute(query, params).fetchall()
        return rows, None
    except sqlite3.Error as e:
        return [], str(e)
    finally:
        conn.close()


def metodo_vulneravel(username_input):
    """MÉTODO A: concatenação direta — VULNERÁVEL."""
    query = "SELECT * FROM users WHERE username = '" + username_input + "'"
    rows, error = _run(query)
    return {"query": query, "params": None, "rows": rows, "error": error}


def metodo_seguro(username_input):
    """MÉTODO B: prepared statement — SEGURO."""
    rows, error = _run(SAFE_QUERY, (username_input,))
    return {"query": SAFE_QUERY, "params": (username_input,), "rows": rows, "error": error}


def comparar(username_input):
    return {
        "input": username_input,
        "vulneravel": metodo_vulneravel(username_input),
        "seguro": metodo_seguro(username_input),
    }


def todos_os_utilizadores():
    rows, _ = _run("SELECT * FROM users ORDER BY id")
    return rows
