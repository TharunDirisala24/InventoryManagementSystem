import os
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from mysql.connector import Error
from database import get_connection

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")


def fetch_all(query, params=()):
    db = get_connection()
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


def fetch_one(query, params=()):
    db = get_connection()
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()


def valid_money(value, field_name):
    try:
        amount = Decimal(value)
        if amount < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return amount
    except (InvalidOperation, TypeError):
        raise ValueError(f"Enter a valid {field_name.lower()}.")


@app.route("/")
def dashboard():
    stats = fetch_one("""
        SELECT COUNT(*) AS product_count,
               COALESCE(SUM(quantity), 0) AS units_in_stock,
               COALESCE(SUM(quantity * purchase_price), 0) AS stock_value,
               COALESCE(SUM(quantity * selling_price), 0) AS retail_value
        FROM products
    """)
    low_stock = fetch_all("""
        SELECT * FROM products
        WHERE quantity <= reorder_level
        ORDER BY quantity ASC, name ASC
    """)
    recent_sales = fetch_all("""
        SELECT s.*, p.name AS product_name, p.sku
        FROM sales s JOIN products p ON p.id = s.product_id
        ORDER BY s.sale_date DESC LIMIT 8
    """)
    month_sales = fetch_one("""
        SELECT COALESCE(SUM(total_amount), 0) AS amount,
               COALESCE(SUM(quantity), 0) AS units
        FROM sales
        WHERE YEAR(sale_date)=YEAR(CURDATE())
          AND MONTH(sale_date)=MONTH(CURDATE())
    """)
    category_rows = fetch_all("""
        SELECT category, SUM(quantity) AS units
        FROM products GROUP BY category ORDER BY units DESC
    """)
    month_rows = fetch_all("""
    SELECT
        YEAR(sale_date) AS sale_year,
        MONTH(sale_date) AS sale_month,
        DATE_FORMAT(sale_date, '%b %Y') AS month,
        SUM(total_amount) AS total
    FROM sales
    GROUP BY
        YEAR(sale_date),
        MONTH(sale_date),
        DATE_FORMAT(sale_date, '%b %Y')
    ORDER BY
        YEAR(sale_date),
        MONTH(sale_date)
""")
      
    return render_template(
        "dashboard.html", stats=stats, low_stock=low_stock,
        recent_sales=recent_sales, month_sales=month_sales,
        category_rows=category_rows, month_rows=month_rows
    )


@app.route("/products")
def products():
    search = request.args.get("q", "").strip()
    rows = fetch_all("""
        SELECT * FROM products
        WHERE name LIKE %s OR sku LIKE %s OR category LIKE %s
        ORDER BY name
    """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    return render_template("products.html", products=rows, search=search)


@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            sku = request.form["sku"].strip().upper()
            category = request.form["category"].strip()
            purchase = valid_money(request.form["purchase_price"], "Purchase price")
            selling = valid_money(request.form["selling_price"], "Selling price")
            quantity = int(request.form["quantity"])
            reorder = int(request.form["reorder_level"])
            if not name or not sku or not category:
                raise ValueError("Please complete all required fields.")
            if quantity < 0 or reorder < 0:
                raise ValueError("Quantity and reorder level cannot be negative.")

            db = get_connection()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO products
                (name, sku, category, purchase_price, selling_price, quantity, reorder_level)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (name, sku, category, purchase, selling, quantity, reorder))
            product_id = cursor.lastrowid
            if quantity:
                cursor.execute("""
                    INSERT INTO stock_movements (product_id, movement_type, quantity, note)
                    VALUES (%s, 'STOCK_IN', %s, 'Opening stock')
                """, (product_id, quantity))
            db.commit()
            cursor.close()
            db.close()
            flash("Product added successfully.", "success")
            return redirect(url_for("products"))
        except (ValueError, Error) as exc:
            flash(str(exc), "danger")
    return render_template("product_form.html", product=None, page_title="Add Product")


@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = fetch_one("SELECT * FROM products WHERE id=%s", (product_id,))
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("products"))

    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            sku = request.form["sku"].strip().upper()
            category = request.form["category"].strip()
            purchase = valid_money(request.form["purchase_price"], "Purchase price")
            selling = valid_money(request.form["selling_price"], "Selling price")
            reorder = int(request.form["reorder_level"])
            if not name or not sku or not category or reorder < 0:
                raise ValueError("Enter valid product details.")
            db = get_connection()
            cursor = db.cursor()
            cursor.execute("""
                UPDATE products SET name=%s, sku=%s, category=%s,
                purchase_price=%s, selling_price=%s, reorder_level=%s
                WHERE id=%s
            """, (name, sku, category, purchase, selling, reorder, product_id))
            db.commit()
            cursor.close()
            db.close()
            flash("Product updated successfully.", "success")
            return redirect(url_for("products"))
        except (ValueError, Error) as exc:
            flash(str(exc), "danger")
    return render_template("product_form.html", product=product, page_title="Edit Product")


@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    try:
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
        db.commit()
        cursor.close()
        db.close()
        flash("Product deleted.", "success")
    except Error:
        flash("This product has sales or stock history and cannot be deleted.", "danger")
    return redirect(url_for("products"))


@app.route("/stock-in", methods=["GET", "POST"])
def stock_in():
    available = fetch_all("SELECT id, name, sku, quantity FROM products ORDER BY name")
    if request.method == "POST":
        try:
            product_id = int(request.form["product_id"])
            quantity = int(request.form["quantity"])
            note = request.form.get("note", "").strip()
            if quantity <= 0:
                raise ValueError("Stock quantity must be greater than zero.")
            db = get_connection()
            cursor = db.cursor()
            cursor.execute("UPDATE products SET quantity=quantity+%s WHERE id=%s", (quantity, product_id))
            if cursor.rowcount == 0:
                raise ValueError("Select a valid product.")
            cursor.execute("""
                INSERT INTO stock_movements (product_id, movement_type, quantity, note)
                VALUES (%s, 'STOCK_IN', %s, %s)
            """, (product_id, quantity, note or "Stock replenishment"))
            db.commit()
            cursor.close()
            db.close()
            flash("Stock added successfully.", "success")
            return redirect(url_for("products"))
        except (ValueError, Error) as exc:
            flash(str(exc), "danger")
    return render_template("stock_in.html", products=available)


@app.route("/sales", methods=["GET", "POST"])
def sales():
    available = fetch_all("SELECT id, name, sku, quantity, selling_price FROM products WHERE quantity > 0 ORDER BY name")
    if request.method == "POST":
        db = None
        cursor = None
        try:
            product_id = int(request.form["product_id"])
            quantity = int(request.form["quantity"])
            if quantity <= 0:
                raise ValueError("Sale quantity must be greater than zero.")
            db = get_connection()
            db.start_transaction()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE id=%s FOR UPDATE", (product_id,))
            product = cursor.fetchone()
            if not product:
                raise ValueError("Product not found.")
            if product["quantity"] < quantity:
                raise ValueError(f"Not enough stock. Available quantity: {product['quantity']}.")
            unit_price = product["selling_price"]
            total = unit_price * quantity
            cursor.execute("UPDATE products SET quantity=quantity-%s WHERE id=%s", (quantity, product_id))
            cursor.execute("""
                INSERT INTO sales (product_id, quantity, unit_price, total_amount)
                VALUES (%s,%s,%s,%s)
            """, (product_id, quantity, unit_price, total))
            cursor.execute("""
                INSERT INTO stock_movements (product_id, movement_type, quantity, note)
                VALUES (%s, 'SALE', %s, 'Sale recorded')
            """, (product_id, -quantity))
            db.commit()
            flash(f"Sale recorded. Total: ₹{total}", "success")
            return redirect(url_for("sales"))
        except (ValueError, Error) as exc:
            if db:
                db.rollback()
            flash(str(exc), "danger")
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    history = fetch_all("""
        SELECT s.*, p.name AS product_name, p.sku
        FROM sales s JOIN products p ON p.id=s.product_id
        ORDER BY s.sale_date DESC LIMIT 100
    """)
    return render_template("sales.html", products=available, sales=history)


@app.route("/reports")
def reports():
    start = request.args.get("start", (date.today() - timedelta(days=30)).isoformat())
    end = request.args.get("end", date.today().isoformat())
    sales_rows = fetch_all("""
        SELECT s.*, p.name AS product_name, p.sku
        FROM sales s JOIN products p ON p.id=s.product_id
        WHERE DATE(s.sale_date) BETWEEN %s AND %s
        ORDER BY s.sale_date DESC
    """, (start, end))
    summary = fetch_one("""
        SELECT COUNT(*) AS transactions,
               COALESCE(SUM(quantity),0) AS units_sold,
               COALESCE(SUM(total_amount),0) AS revenue
        FROM sales WHERE DATE(sale_date) BETWEEN %s AND %s
    """, (start, end))
    stock_rows = fetch_all("""
        SELECT name, sku, category, quantity, reorder_level,
               purchase_price, selling_price,
               quantity * purchase_price AS cost_value,
               quantity * selling_price AS retail_value
        FROM products ORDER BY name
    """)
    return render_template("reports.html", sales=sales_rows, summary=summary,
                           stock_rows=stock_rows, start=start, end=end)


if __name__ == "__main__":
    app.run(debug=True)
