
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = "bookstore.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


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
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", books=books)


@app.route("/add", methods=["POST"])
def add_book():
    title = request.form["title"].strip()
    author = request.form["author"].strip()
    price = float(request.form["price"])
    quantity = int(request.form["quantity"])

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO books (title, author, price, quantity) VALUES (?, ?, ?, ?)",
        (title, author, price, quantity)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/update/<int:book_id>", methods=["POST"])
def update_book(book_id):
    title = request.form["title"].strip()
    author = request.form["author"].strip()
    price = float(request.form["price"])
    quantity = int(request.form["quantity"])

    conn = get_db_connection()
    conn.execute(
        "UPDATE books SET title=?, author=?, price=?, quantity=? WHERE id=?",
        (title, author, price, quantity, book_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/order", methods=["POST"])
def add_order():
    customer_name = request.form["customer_name"].strip()
    book_id = int(request.form["book_id"])
    quantity = int(request.form["quantity"])

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO orders (customer_name, book_id, quantity) VALUES (?, ?, ?)",
        (customer_name, book_id, quantity)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("view_orders"))


@app.route("/orders")
def view_orders():
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT orders.id, orders.customer_name, books.title,
               orders.quantity, orders.status
        FROM orders
        JOIN books ON orders.book_id = books.id
        ORDER BY orders.id DESC
    """).fetchall()
    conn.close()
    return render_template("orders.html", orders=orders)


@app.route("/order/status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    status = request.form["status"]
    if status not in ("Pending", "Completed", "Cancelled"):
        return "Invalid order status", 400

    conn = get_db_connection()
    conn.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, order_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("view_orders"))


if __name__ == "__main__":
    create_table()
    app.run(debug=True)
