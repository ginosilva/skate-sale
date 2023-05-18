import json
import requests
import time
import csv
from fuzzywuzzy import process
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://your_username:your_password@localhost/skatedb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def reset_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_url = db.Column(db.String(256))
    title = db.Column(db.String(256))
    handle = db.Column(db.String(256))
    vendor = db.Column(db.String(256))
    product_type = db.Column(db.String(256))
    available = db.Column(db.Boolean)
    price = db.Column(db.Float)
    compare_at_price = db.Column(db.Float)
    body_html = db.Column(db.Text)
    image_src = db.Column(db.String(256))
    option1 = db.Column(db.String(256))
    option2 = db.Column(db.String(256))
    option3 = db.Column(db.String(256))

    def __init__(self, product_url, title, handle, vendor, product_type, available, price, compare_at_price, body_html, image_src, option1, option2, option3):
        self.product_url = product_url
        self.title = title
        self.handle = handle
        self.vendor = vendor
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
    
standard_sizes = [
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

def load_standard_size_mappings():
    size_mappings = {}
    with open('/Users/scandarsilvapayne/Documents/Skate Sale Aggregator/Data Cleaning/standard_size_mappings.csv', mode='r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            size_mappings[row[0]] = row[1]
    return size_mappings

size_mappings = load_standard_size_mappings()

def clean_sizes(items):
    for item in items:
        if item.product_type == 'Shoes':
            item.option1 = size_mappings.get(item.option1, 'Check Size on Store')
        elif item.product_type in ['Hats & Beanies', 'Other Accessories', 'Bags', 'Completes', 'Decks', 'Trucks', 'Wheels', 'Other Hardware', 'DVDs & Media', 'Protection', 'Other Clothing', 'Other']:
            item.option1 = ''
        else:
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

    print(f"Store name: {store_name}")  # Add this print statement
    return store_name


# ... Keep the load_category_mappings function here ...
def load_category_mappings(store_name):
    with open('store_category_mappings.csv', mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        category_mappings = {}

        for row in reader:
            if row['Store'].lower() == store_name.lower():
                category_mappings[row['Category'].lower()] = row['Mapped Category']

    return category_mappings

# ... Keep the standardize_category function here ...
def standardize_category(value, store_category_mappings):
    if value.strip() == '':
        return ''
    value_lower = value.lower()
    standardized_value = store_category_mappings.get(value_lower, value)
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

def clean_database(newly_added_items):
    # Process categories
    store_name = get_store_name()
    items = clean_categories(newly_added_items, store_name)

    # Process sizes
    print("Processing sizes")
    items = clean_sizes(newly_added_items)

    # Process brands
    print("Processing brands")
    items = process_brands(newly_added_items)

    # Commit the changes to the database
    db.session.commit()





def clean_html(html):
    if html is None:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(strip=True)

urls = [
    "https://www.5050store.com/products.json?limit=250",
    "https://www.baddestskateshop.com/products.json?limit=250",
    "https://www.slamcity.com/products.json?limit=250",
    "https://www.altarskateshop.co.uk/products.json?limit=250",
    "https://www.cardiffskateboardclub.com/products.json?limit=250",
    "https://campusskatestore.com/products.json?limit=250",
    "https://www.decadestore.co.uk/products.json?limit=250",
    "https://www.decimalstore.com/products.json?limit=250",
    "https://www.flavourskateshop.co.uk/products.json?limit=250",
    "http://www.focuspocus.co.uk/products.json?limit=250",
    "http://www.freestyleskatestore.com/products.json?limit=250",
    "http://www.idealbirmingham.co.uk/products.json?limit=250",
    "http://www.junestore.co.uk/products.json?limit=250",
    "http://www.lariatt.com/products.json?limit=250",
    "http://www.legacyskatestore.co.uk/products.json?limit=250",
    "http://www.levelskateboards.co.uk/products.json?limit=250",
    "https://mooseskateshop.com/products.json?limit=250",
    "http://www.noteshop.co.uk/products.json?limit=250",
    "https://primedelux.com/products.json?limit=250",
    "https://www.sluggerskatestore.co.uk/products.json?limit=250",
    "https://seedskateshop.com/products.json?limit=250",
    "https://www.aylesburyskateboards.co.uk/products.json?limit=250",
    "https://www.tuesdaysskateshop.co.uk/products.json?limit=250",
    "https://www.forw4rd.com/products.json?limit=250",
    "https://www.sourceskate.com/products.json?limit=250",
    "https://illicitskate.com/products.json?limit=250",
    "https://welcomeleeds.com/products.json?limit=250",
    "https://www.dissentskateshop.co.uk/products.json?limit=250",
    "https://tvsc.co/products.json?limit=250",
    "https://pretendsupply.co/products.json?limit=250",
    "https://theboredroom.store/products.json?limit=250",
    "https://www.thepalomino.com/products.json?limit=250"
]

def scrape_website(url):
    sale_items = {}
    page = 1

    # Get the store name for the current URL
    store_name = ''
    with open('store_category_mappings.csv', mode='r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row['Store'].lower() in url.lower():
                store_name = row['Store']
                break

    store_category_mappings = load_category_mappings(store_name)

    while True:
        paginated_url = f"{url}&page={page}"
        response = requests.get(paginated_url)

        if response.status_code == 200:
            try:
                shopify_data = response.json()
            except json.JSONDecodeError:
                print(f"Invalid JSON data received from {url}")
                continue

            if not shopify_data['products']:
                break

            for product in shopify_data['products']:
                for variant in product['variants']:
                    compare_at_price_float = float(variant['compare_at_price']) if variant['compare_at_price'] is not None else None
                    price_float = float(variant['price']) if variant['price'] is not None else None
                    
                    if (compare_at_price_float is not None and
                            compare_at_price_float != 0.00 and
                            compare_at_price_float != price_float and
                            variant['available']):
                        sale_item = {
                            'product_url': f"{urlparse(url).scheme}://{urlparse(url).netloc}/products/{product['handle']}",
                            'title': product['title'],
                            'handle': product['handle'],
                            'vendor': product['vendor'],
                            'product_type': standardize_category(product['product_type'], store_category_mappings),
                            'available': variant['available'],
                            'price': variant['price'],
                            'compare_at_price': variant['compare_at_price'],
                            'body_html': clean_html(product['body_html']),
                            'option1': variant['option1'],
                            'option2': variant['option2'],
                            'option3': variant['option3']
                        }

                        if product.get('images'):
                            sale_item['image_src'] = product['images'][0]['src']

                        # Get the available sizes
                        sizes = []
                        if variant['option1']:
                            sizes.append(variant['option1'])

                        # Check if the sale item already exists in the dictionary
                        sale_item_key = f"{product['handle']}-{product['id']}"
                        for size in sizes:
                            # Create a unique key based on the product handle, ID, and size
                            sale_item_key = f"{product['handle']}-{product['id']}-{size}"
                            if sale_item_key not in sale_items:
                                # Create a new SaleItem object for each size
                                sale_item_copy = sale_item.copy()
                                sale_item_copy['option1'] = size
                                sale_items[sale_item_key] = sale_item_copy



            page += 1

        else:
            print(f"Error fetching data for {url}: {response.status_code}")
            break

    return sale_items





@app.route('/scrape')
def scrape():
    all_sale_items = {}
    for url in urls:
        sale_items = scrape_website(url)
        all_sale_items.update(sale_items)
        time.sleep(1)  # Pause for a second between requests to avoid overloading the websites

    newly_added_items = []  # Create an empty list to store newly added items
    for _, sale_item in all_sale_items.items():
        # Check if an item with the same handle and product URL already exists in the database
        existing_item = SaleItem.query.filter_by(handle=sale_item['handle'], product_url=sale_item['product_url'], option1=sale_item['option1']).first()
        if existing_item:
            # Skip adding the item if it already exists in the database
            continue

        new_item = SaleItem(
            product_url=sale_item['product_url'],
            title=sale_item['title'],
            handle=sale_item['handle'],
            vendor=sale_item['vendor'],
            product_type=sale_item['product_type'],
            available=sale_item['available'],
            price=sale_item['price'],
            compare_at_price=sale_item['compare_at_price'],
            body_html=sale_item['body_html'],
            image_src=sale_item.get('image_src', None),
            option1=sale_item['option1'],
            option2=sale_item['option2'],
            option3=sale_item['option3']
        )

        db.session.add(new_item)
        newly_added_items.append(new_item)  # Add the new_item to the list of newly_added_items

    db.session.commit()

    clean_database(newly_added_items)  # Pass the newly_added_items list to the clean_database function
    return jsonify({'result': 'success'})


@app.route('/items')
def get_items():
    items = SaleItem.query.limit(5000).all()  # Change the number 10 to any limit you prefer
    return jsonify([item.as_dict() for item in items])

@app.route('/resetdb')
def reset_db():
    reset_database()
    return jsonify({'result': 'success'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

