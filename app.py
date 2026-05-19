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
    conn.execute("DROP TABLE IF EXISTS fornecedores")
    conn.execute("""
        CREATE TABLE fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razao_social TEXT NOT NULL,
            nome_fantasia TEXT,
            cnpj TEXT UNIQUE,
            ie TEXT,
            email TEXT,
            telefone TEXT,
            celular TEXT,
            contato TEXT,
            endereco TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT,
            banco TEXT,
            agencia TEXT,
            conta TEXT,
            tipo_conta TEXT,
            observacoes TEXT,
            ativo INTEGER DEFAULT 1,
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
    total_fornecedores = db.execute("SELECT COUNT(*) as c FROM fornecedores WHERE ativo = 1").fetchone()["c"]
    db.close()
    return jsonify({"total": total, "ultimos_7_dias": ultimos, "total_fornecedores": total_fornecedores})


@app.route("/api/fornecedores", methods=["GET"])
def listar_fornecedores():
    db = get_db()
    termo = request.args.get("busca", "").strip()
    if termo:
        fornecedores = db.execute(
            "SELECT * FROM fornecedores WHERE (razao_social LIKE ? OR nome_fantasia LIKE ? OR cnpj LIKE ?) AND ativo = 1 ORDER BY id DESC",
            (f"%{termo}%", f"%{termo}%", f"%{termo}%")
        ).fetchall()
    else:
        fornecedores = db.execute("SELECT * FROM fornecedores WHERE ativo = 1 ORDER BY id DESC").fetchall()
    db.close()
    return jsonify([dict(f) for f in fornecedores])


@app.route("/api/fornecedores", methods=["POST"])
def criar_fornecedor():
    data = to_upper_except_email(request.json)
    if not data.get("razao_social"):
        return jsonify({"erro": "razao social e obrigatoria"}), 400
    try:
        db = get_db()
        cur = db.execute(
            """INSERT INTO fornecedores (razao_social, nome_fantasia, cnpj, ie, email, telefone, celular, contato, endereco, numero, complemento, bairro, cidade, estado, cep, banco, agencia, conta, tipo_conta, observacoes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("razao_social"), data.get("nome_fantasia"), data.get("cnpj"), data.get("ie"),
             data.get("email"), data.get("telefone"), data.get("celular"), data.get("contato"),
             data.get("endereco"), data.get("numero"), data.get("complemento"), data.get("bairro"),
             data.get("cidade"), data.get("estado"), data.get("cep"), data.get("banco"),
             data.get("agencia"), data.get("conta"), data.get("tipo_conta"), data.get("observacoes")),
        )
        db.commit()
        fornecedor = db.execute("SELECT * FROM fornecedores WHERE id = ?", (cur.lastrowid,)).fetchone()
        db.close()
        return jsonify(dict(fornecedor)), 201
    except sqlite3.IntegrityError as e:
        if "cnpj" in str(e):
            return jsonify({"erro": "cnpj ja cadastrado"}), 409
        return jsonify({"erro": "erro ao salvar fornecedor"}), 409


@app.route("/api/fornecedores/<int:id>", methods=["GET"])
def detalhes_fornecedor(id):
    db = get_db()
    fornecedor = db.execute("SELECT * FROM fornecedores WHERE id = ?", (id,)).fetchone()
    db.close()
    if fornecedor:
        return jsonify(dict(fornecedor))
    return jsonify({"erro": "fornecedor nao encontrado"}), 404


@app.route("/api/fornecedores/<int:id>", methods=["PUT"])
def atualizar_fornecedor(id):
    data = to_upper_except_email(request.json)
    if not data.get("razao_social"):
        return jsonify({"erro": "razao social e obrigatoria"}), 400
    try:
        db = get_db()
        db.execute(
            """UPDATE fornecedores SET razao_social=?, nome_fantasia=?, cnpj=?, ie=?, email=?, telefone=?, celular=?, contato=?, endereco=?, numero=?, complemento=?, bairro=?, cidade=?, estado=?, cep=?, banco=?, agencia=?, conta=?, tipo_conta=?, observacoes=? WHERE id=?""",
            (data.get("razao_social"), data.get("nome_fantasia"), data.get("cnpj"), data.get("ie"),
             data.get("email"), data.get("telefone"), data.get("celular"), data.get("contato"),
             data.get("endereco"), data.get("numero"), data.get("complemento"), data.get("bairro"),
             data.get("cidade"), data.get("estado"), data.get("cep"), data.get("banco"),
             data.get("agencia"), data.get("conta"), data.get("tipo_conta"), data.get("observacoes"), id),
        )
        db.commit()
        fornecedor = db.execute("SELECT * FROM fornecedores WHERE id = ?", (id,)).fetchone()
        db.close()
        return jsonify(dict(fornecedor))
    except sqlite3.IntegrityError as e:
        if "cnpj" in str(e):
            return jsonify({"erro": "cnpj ja cadastrado"}), 409
        return jsonify({"erro": "erro ao atualizar fornecedor"}), 409


@app.route("/api/fornecedores/<int:id>", methods=["DELETE"])
def deletar_fornecedor(id):
    db = get_db()
    db.execute("UPDATE fornecedores SET ativo = 0 WHERE id = ?", (id,))
    db.commit()
    db.close()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
