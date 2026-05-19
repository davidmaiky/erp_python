import sqlite3
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

data_dir = os.environ.get("DATA_DIR", "/data")
os.makedirs(data_dir, exist_ok=True)
DB_PATH = os.path.join(data_dir, "cadastro.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def to_upper_except_email(data):
    for key, value in data.items():
        if key == "email":
            continue
        if isinstance(value, str):
            data[key] = value.upper()
    return data


def init_db():
    conn = get_db()
    conn.execute("DROP TABLE IF EXISTS clientes")
    conn.execute("""
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            rg TEXT,
            data_nascimento TEXT,
            email TEXT NOT NULL UNIQUE,
            telefone TEXT,
            celular TEXT,
            endereco TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT,
            observacoes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/clientes", methods=["GET"])
def listar():
    db = get_db()
    termo = request.args.get("busca", "").strip()
    if termo:
        clientes = db.execute(
            "SELECT * FROM clientes WHERE nome LIKE ? OR email LIKE ? ORDER BY id DESC",
            (f"%{termo}%", f"%{termo}%")
        ).fetchall()
    else:
        clientes = db.execute("SELECT * FROM clientes ORDER BY id DESC").fetchall()
    db.close()
    return jsonify([dict(c) for c in clientes])


@app.route("/api/clientes", methods=["POST"])
def criar():
    data = to_upper_except_email(request.json)
    if not data.get("nome") or not data.get("email"):
        return jsonify({"erro": "nome e email sao obrigatorios"}), 400
    try:
        db = get_db()
        cur = db.execute(
            "INSERT INTO clientes (nome, cpf, rg, data_nascimento, email, telefone, celular, endereco, cidade, estado, cep, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data.get("nome"), data.get("cpf"), data.get("rg"), data.get("data_nascimento"),
             data.get("email"), data.get("telefone"), data.get("celular"), data.get("endereco"),
             data.get("cidade"), data.get("estado"), data.get("cep"), data.get("observacoes")),
        )
        db.commit()
        cliente = db.execute("SELECT * FROM clientes WHERE id = ?", (cur.lastrowid,)).fetchone()
        db.close()
        return jsonify(dict(cliente)), 201
    except sqlite3.IntegrityError:
        return jsonify({"erro": "email ja cadastrado"}), 409


@app.route("/api/clientes/<int:id>", methods=["GET"])
def detalhes(id):
    db = get_db()
    cliente = db.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
    db.close()
    return jsonify(dict(cliente))


@app.route("/api/clientes/<int:id>", methods=["PUT"])
def atualizar(id):
    data = to_upper_except_email(request.json)
    if not data.get("nome") or not data.get("email"):
        return jsonify({"erro": "nome e email sao obrigatorios"}), 400
    try:
        db = get_db()
        db.execute(
            "UPDATE clientes SET nome=?, cpf=?, rg=?, data_nascimento=?, email=?, telefone=?, celular=?, endereco=?, cidade=?, estado=?, cep=?, observacoes=? WHERE id=?",
            (data.get("nome"), data.get("cpf"), data.get("rg"), data.get("data_nascimento"),
             data.get("email"), data.get("telefone"), data.get("celular"), data.get("endereco"),
             data.get("cidade"), data.get("estado"), data.get("cep"), data.get("observacoes"), id),
        )
        db.commit()
        cliente = db.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
        db.close()
        return jsonify(dict(cliente))
    except sqlite3.IntegrityError:
        return jsonify({"erro": "email ja cadastrado"}), 409


@app.route("/api/clientes/<int:id>", methods=["DELETE"])
def deletar(id):
    db = get_db()
    db.execute("DELETE FROM clientes WHERE id = ?", (id,))
    db.commit()
    db.close()
    return "", 204


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    db = get_db()
    total = db.execute("SELECT COUNT(*) as c FROM clientes").fetchone()["c"]
    ultimos = db.execute("SELECT COUNT(*) as c FROM clientes WHERE criado_em >= datetime('now', '-7 days')").fetchone()["c"]
    db.close()
    return jsonify({"total": total, "ultimos_7_dias": ultimos})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
