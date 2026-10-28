import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Database configuration
if os.environ.get("VERCEL"):
    DATABASE = "/tmp/bookstore.db"
else:
    DATABASE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "bookstore.db"
    )


# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Create required database tables
def create_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            book_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)

    conn.commit()
    conn.close()


# Display all books
@app.route("/")
def index():
    conn = get_db_connection()
    books = conn.execute(
        "SELECT * FROM books ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("index.html", books=books)


# Add a new book
@app.route("/add", methods=["POST"])
def add_book():
    try:
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        price = float(request.form["price"])
        quantity = int(request.form["quantity"])

        if not title or not author or price < 0 or quantity < 0:
            return "Please enter valid book details.", 400

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO books (title, author, price, quantity)
            VALUES (?, ?, ?, ?)
            """,
            (title, author, price, quantity)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    except (ValueError, KeyError):
        return "Invalid book details.", 400


# Update book details
@app.route("/update/<int:book_id>", methods=["POST"])
def update_book(book_id):
    try:
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        price = float(request.form["price"])
        quantity = int(request.form["quantity"])

        if not title or not author or price < 0 or quantity < 0:
            return "Please enter valid book details.", 400

        conn = get_db_connection()
        conn.execute(
            """
            UPDATE books
            SET title = ?, author = ?, price = ?, quantity = ?
            WHERE id = ?
            """,
            (title, author, price, quantity, book_id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    except (ValueError, KeyError):
        return "Invalid book details.", 400


# Delete a book
@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    conn = get_db_connection()

    existing_order = conn.execute(
        "SELECT id FROM orders WHERE book_id = ? LIMIT 1",
        (book_id,)
    ).fetchone()

    if existing_order:
        conn.close()
        return "This book has existing orders and cannot be deleted.", 400

    conn.execute(
        "DELETE FROM books WHERE id = ?",
        (book_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# Create a customer order
@app.route("/order", methods=["POST"])
def add_order():
    try:
        customer_name = request.form["customer_name"].strip()
        book_id = int(request.form["book_id"])
        quantity = int(request.form["quantity"])

        if not customer_name or quantity <= 0:
            return "Please enter valid order details.", 400

        conn = get_db_connection()

        book = conn.execute(
            "SELECT id, quantity FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if book is None:
            conn.close()
            return "Selected book was not found.", 404

        if quantity > book["quantity"]:
            conn.close()
            return "Requested quantity exceeds available stock.", 400

        conn.execute(
            """
            INSERT INTO orders (customer_name, book_id, quantity)
            VALUES (?, ?, ?)
            """,
            (customer_name, book_id, quantity)
        )

        conn.execute(
            "UPDATE books SET quantity = quantity - ? WHERE id = ?",
            (quantity, book_id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("view_orders"))

    except (ValueError, KeyError):
        return "Invalid order details.", 400


# Display all customer orders
@app.route("/orders")
def view_orders():
    conn = get_db_connection()

    orders = conn.execute("""
        SELECT
            orders.id,
            orders.customer_name,
            books.title,
            orders.quantity,
            orders.status
        FROM orders
        JOIN books ON orders.book_id = books.id
        ORDER BY orders.id DESC
    """).fetchall()

    conn.close()

    return render_template("orders.html", orders=orders)


# Update customer order status
@app.route("/order/status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    status = request.form.get("status", "")

    if status not in ("Pending", "Completed", "Cancelled"):
        return "Invalid order status.", 400

    conn = get_db_connection()

    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("view_orders"))


# Initialize database tables when the app loads
create_table()


# Run the app locally
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )