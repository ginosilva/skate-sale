import os
import csv
import glob
from fuzzywuzzy import process
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://your_username:your_password@localhost/skatedb'
db = SQLAlchemy(app)

# ... Keep the SaleItem class definition here ...
class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_url = db.Column(db.String(256))
    title = db.Column(db.String(256))
    handle = db.Column(db.String(256))
    vendor = db.Column(db.String(256))
    tags = db.Column(db.String(256))
    product_type = db.Column(db.String(256))
    available = db.Column(db.Boolean)
    price = db.Column(db.Float)
    compare_at_price = db.Column(db.Float)
    body_html = db.Column(db.Text)
    image_src = db.Column(db.String(256))
    option1 = db.Column(db.String(256))
    option2 = db.Column(db.String(256))
    option3 = db.Column(db.String(256))

    def __init__(self, product_url, title, handle, vendor, tags, product_type, available, price, compare_at_price, body_html, image_src, option1, option2, option3):
        self.product_url = product_url
        self.title = title
        self.handle = handle
        self.vendor = vendor
        self.tags = tags
        self.product_type = product_type
        self.available = available
        self.price = price
        self.compare_at_price = compare_at_price
        self.body_html = body_html
        self.image_src = image_src
        self.option1 = option1
        self.option2 = option2
        self.option3 = option3

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ... Keep the definitions from the first and second scripts here ...

# Definitions from the first script
standard_sizes = [
    "US6/UK5/EU38",
    "US6.5/UK5.5/EU39",
    "US7/UK6/EU39.5",
    "US7.5/UK6.5/EU40",
    "US8/UK7/EU41",
    "US8.5/UK7.5/EU41.5",
    "US9/UK8/EU42",
    "US9.5/UK8.5/EU42.5",
    "US10/UK9/EU43",
    "US10.5/UK9.5/EU44",
    "US11/UK10/EU44.5",
    "US11.5/UK10.5/EU45",
    "US12/UK11/EU46",
    "US12.5/UK11.5/EU46.5",
    "US13/UK12/EU47",
    "US13.5/UK12.5/EU48",
    "US14/UK13/EU49",
    "US14.5/UK13.5/EU49.5",
    "US15/UK14/EU50",
    "US16/UK15/EU51"
    "28x30",
    "29x30",
    "30x30",
    "30x32",
    "32x30",
    "32x32",
    "34x30",
    "34x32",
    "36x30",
    "36x32",
    "XXS",
    "XS",
    "S",
    "M",
    "L",
    "XL",
    "XXL",
    "XXXL"
]

def standardize_value(value, standard_values, threshold=80):
    best_match, score = process.extractOne(value, standard_values)
    if score >= threshold:
        return best_match
    return ''

def clean_sizes(items):
    for item in items:
        item.option1 = standardize_value(item.option1, standard_sizes)
    return items

with open('/Users/scandarsilvapayne/Documents/Skate Sale Aggregator/Data Cleaning/List for script/final_brand_list.csv', mode='r') as infile:
    reader = csv.reader(infile)
    standardized_brands = [row[0] for row in reader]

def standardize_brand(value):
    if value.strip() == '':
        return ''
    best_match, _ = process.extractOne(value, standardized_brands)
    return best_match

def process_brands(items):
    for item in items:
        item.vendor = standardize_brand(item.vendor)
    return items

# Definitions from the third script
def get_store_name():
    # Get the first item from the database
    first_item = db.session.query(SaleItem).first()
    if not first_item:
        return ''

    product_url = first_item.product_url
    store_name = ''

    # Read the store_category_mappings.csv file and look for the store name in the product_url
    with open('store_category_mappings.csv', mode='r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row['Store'].lower() in product_url.lower():
                store_name = row['Store']
                break

    return store_name

# ... Keep the load_category_mappings function here ...
def load_category_mappings(store_name):
    with open('store_category_mappings.csv', mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        category_mappings = {}

        for row in reader:
            if row['Store'].lower() == store_name.lower():
                category_mappings[row['Category']] = row['Mapped Category']

    return category_mappings
# ... Keep the standardize_category function here ...
def standardize_category(value, store_category_mappings):
    if value.strip() == '':
        return ''
    standardized_value = store_category_mappings.get(value, value)
    print(f"Original value: {value}, Standardized value: {standardized_value}")  # Add this line to print the original and standardized values
    return standardized_value
# ... Keep the clean_categories function here ...
def clean_categories(items, store_name):
    store_category_mappings = load_category_mappings(store_name)
    print(f"Store category mappings: {store_category_mappings}")

    if not store_category_mappings:
        print(f"No category mappings found for {store_name}")
        return items

    for item in items:
        item.product_type = standardize_category(item.product_type, store_category_mappings)
    return items

def clean_database(session):
    items = session.query(SaleItem).all()

    # Process sizes
    print("Processing sizes")
    items = clean_sizes(items)

    # Process brands
    print("Processing brands")
    items = process_brands(items)

    # Process categories
    print("Processing categories")
    store_name = get_store_name()
    items = clean_categories(items, store_name)

    # Commit the changes to the database
    session.commit()

# At the end of the script, call the clean_database function with the active session
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
    clean_database(db.session)
