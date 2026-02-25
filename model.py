from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()

class Vendor(db.Model):
    __tablename__ = 'vendor'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='vendor', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    Unit = db.Column(db.String(25), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)
    stock_quantity = db.Column(db.Integer, default=0)
    Stock = db.Column(db.Enum('Available', 'out_of_stock'), nullable=False)
    price = db.Column(db.Numeric(10,2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InventryTransactions(db.Model):
    __tablename__ = "inventry_transactions"

    id = db.Column(db.Integer, primary_key=True)
    Product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    change_amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100))
    reference = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    __tablename__ = 'owner_contacts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(100))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification_log(db.Model):
    __tablename__ = 'notifications_log'

    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.Enum('email', 'sms'), nullable=False)
    recipient = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    status = db.Column(db.Enum('sent', 'failed'), default='sent')
    response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class loan_calculator(db.Model):
    __tablename__ = 'loan_dataset'

    id = db.Column(db.Integer, primary_key=True)
    principal_amount = db.Column(db.Numeric(10, 2), nullable=False)
    annual_rate = db.Column(db.Numeric(5, 2), nullable=False)
    term_year = db.Column(db.Integer, nullable=False)
    interest = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=00.00)
    monthly_payment = db.Column(db.Numeric(10, 2), nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=False)

    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

