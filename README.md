# StockWise - Inventory Management System

An intermediate-level inventory management web application built with Python, Flask, MySQL, HTML, CSS and Chart.js.

## Features
- Dashboard with product, stock, inventory value and monthly sales summaries
- Add, view, search, edit and delete products
- Record incoming stock and maintain stock movement history
- Record sales with stock validation and automatic quantity deduction
- Low-stock alerts based on each product's reorder level
- Date-filtered sales report and current stock valuation report
- Charts for monthly sales revenue and stock by category

## Requirements
- Python 3.10+
- MySQL Server
- VS Code (recommended)

## Setup (Windows PowerShell)

1. Open this project folder in VS Code.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```

3. Install packages:

   ```powershell
   pip install -r requirements.txt
   ```

4. Open MySQL Workbench or the MySQL command line and run all SQL statements from `database.sql`.

5. Copy `.env.example` to a new file named `.env`. Put your MySQL password in `.env`:

   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_actual_password
   DB_NAME=inventory_management
   SECRET_KEY=replace-with-a-random-secret
   ```

   Do not upload `.env` to GitHub. It is ignored by `.gitignore`.

6. Start the application:

   ```powershell
   python app.py
   ```

7. Open http://127.0.0.1:5000 in your browser.

## Main pages
- `/` Dashboard
- `/products` Product catalogue
- `/products/add` Add product
- `/stock-in` Add stock
- `/sales` Record sale and view sales history
- `/reports` Sales and stock reports

## Notes
- A product's SKU must be unique.
- Quantity cannot be negative.
- Sales are rejected when there is not enough stock.
- Products with sales or stock history cannot be deleted, preserving report history.
- Chart.js is loaded from a CDN, so charts need an internet connection.

## Suggested next improvements
- Login and role-based access
- Supplier and purchase-order management
- Export reports to Excel/PDF
- Pagination and advanced filters
- Automated database backups
