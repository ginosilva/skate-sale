from flask_sqlalchemy import SQLAlchemy
from config import app

db = SQLAlchemy(app)

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

    # ... Keep the rest of the code ...
