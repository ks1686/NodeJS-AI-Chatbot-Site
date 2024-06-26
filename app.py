# app.py
from flask import Flask, render_template
import json

app = Flask(__name__)

# Load menu data from JSON
with open("menu.json", "r") as f:
    menu_data = json.load(f)


# Route for the main page with category buttons
@app.route("/")
def index():
    return render_template("index.html")


# Route to handle category requests
@app.route("/category/<category_name>")
def category_items(category_name):
    items_in_category = [
        item
        for item in menu_data["data"]
        if item["category"] == category_name and item["in_stock"]
    ]
    return render_template(
        "category_items.html", category_name=category_name, items=items_in_category
    )


if __name__ == "__main__":
    app.run(debug=True)
