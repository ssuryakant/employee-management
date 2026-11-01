import os
import logging
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.getenv("DB_PORT", "5432"),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode="require",
        connect_timeout=5
    )

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "DevOps 3-Tier Application Running",
        "database": "PostgreSQL"
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/ready", methods=["GET"])
def ready():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "ready"}), 200
    except Exception:
        app.logger.exception("Database connection failed")
        return jsonify({"status": "not ready"}), 503

@app.route("/customers", methods=["GET"])
def get_customers():
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, name, email, created_at "
                    "FROM customers ORDER BY id"
                )
                data = cur.fetchall()
        return jsonify(data), 200
    except Exception:
        app.logger.exception("Customer query failed")
        return jsonify({"error": "Database error"}), 500

@app.route("/customers", methods=["POST"])
def add_customer():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({"error": "Name and email required"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO customers (name, email)
                    VALUES (%s, %s)
                    RETURNING id, name, email, created_at
                    """,
                    (name, email)
                )
                customer = cur.fetchone()

        return jsonify(customer), 201

    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Email already exists"}), 409
    except Exception:
        app.logger.exception("Customer insert failed")
        return jsonify({"error": "Database error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
