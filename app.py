import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config["UPLOAD_FOLDER"] = "static/uploads/"

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Connect to the database
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=os.environ['DB_PORT']
    )
    return conn

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM roommates ORDER BY id")
    roommates = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", roommates=roommates)

@app.route("/balances")
def show_balances():
    query = """
    SELECT r.name,
           COALESCE(SUM(CASE WHEN r.id = e.payer_id THEN es.share ELSE -es.share END), 0) AS balance
    FROM roommates r
    LEFT JOIN expense_splits es ON r.id = es.roommate_id
    LEFT JOIN expenses e ON es.expense_id = e.id
    GROUP BY r.id, r.name
    ORDER BY balance DESC
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query)
    balances = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("balances.html", balances=balances)

@app.route("/expenses")
def show_expenses():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Get the list of expenses to show in the table
    cur.execute("""
        SELECT e.*, r.name AS payer_name
        FROM expenses e
        JOIN roommates r ON e.payer_id = r.id
        ORDER BY e.date DESC
    """)
    expenses = cur.fetchall()

    # 2. Get the list of roommates for the dropdown menu
    cur.execute("SELECT * FROM roommates ORDER BY name")
    roommates = cur.fetchall()

    cur.close()
    conn.close()
    
    # 3. Pass BOTH lists to the HTML
    return render_template("expenses.html", expenses=expenses, roommates=roommates)

@app.route("/add_roommate", methods=["POST"])
def add_roommate_route():
    name = request.form.get("name")
    if name:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO roommates (name) VALUES (%s)", (name,))
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    return redirect(url_for("index"))

@app.route("/delete_roommate", methods=["POST"])
def delete_roommate_route():
    name = request.form.get("name")
    if name:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM roommates WHERE name = %s", (name,))
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for("index"))

@app.route("/add_expense", methods=["POST"])
def add_expense_route():
    name = request.form.get("name")
    amount = float(request.form.get("amount"))
    payer_id = int(request.form.get("payer"))
    
    file = request.files.get("bill_photo")
    saved_file = None
    if file and file.filename:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        saved_file = file.filename

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Insert Expense and get the new ID
        cur.execute("""
            INSERT INTO expenses (name, amount, payer_id, date, bill_photo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (name, amount, payer_id, datetime.now(), saved_file))
        
        expense_id = cur.fetchone()['id']

        # 2. Get roommates count
        cur.execute("SELECT id FROM roommates")
        roommates = cur.fetchall()
        
        if roommates:
            split_amount = amount / len(roommates)
            for r in roommates:
                cur.execute("""
                    INSERT INTO expense_splits (expense_id, roommate_id, share)
                    VALUES (%s, %s, %s)
                """, (expense_id, r['id'], split_amount))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("show_expenses"))

if __name__ == "__main__":
    app.run(debug=True)


