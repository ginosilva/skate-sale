from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://your_username:your_password@localhost/skatedb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
