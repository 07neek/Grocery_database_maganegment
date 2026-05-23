import os, io, base64, math
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from dotenv import load_dotenv
from model import db, Product, Vendor, Contact, InventryTransactions, Notification_log, loan_calculator
from flask_mail import Mail, Message
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devkey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///dev.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

#Mail config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
mail = Mail(app)


@app.route('/')
def dashboard():
    products = Product.query.all()
    sold_out_count = Product.query.filter_by(Stock="out_of_stock").count()
    return render_template('dashboard.html',
                           products=products,
                           sold_out_count=sold_out_count,                          
                           )

@app.route('/search')
def search():
    keyword = request.args.get('q', '')
    products = Product.query.filter(
        Product.name.ilike(f"%{keyword}%")
    )

    return jsonify([
        {
            'product_id': p.id,
            'product_name': p.name,
            'unit': p.Unit,
            'Available_Quantity': p.stock_quantity,
            'stock': p.Stock,
            'price': p.price
        } for p in products
    ])


@app.route('/soldout')
def soldout():
    sold_out_list = Product.query.filter_by(Stock='out_of_stock').all()
    return render_template('soldout.html',
                           sold_out_list=sold_out_list,
                           count=len(sold_out_list)
                           )

@app.route('/vendor')
def vendors():
    vendors = Vendor.query.order_by(Vendor.id).all()
    return render_template('vendor.html',
                           vendors=vendors)
    
@app.route('/profile')
def owner_contact():
    owner = Contact.query.all()
    return render_template('owner.html', owner=owner)

@app.route('/loan_calculator', methods=['GET', 'POST'])
def loan():
    loans = loan_calculator.query.all()
    if request.method == 'POST':
        P = float(request.form.get('principal_amount'))
        annual_rate = float(request.form.get('annual_rate'))
        Y = int(request.form.get('term_year'))

        r = annual_rate / 100 / 12
        n = Y * 12

        monthly_payment = (P * r * math.pow(1+r, n)) / (math.pow(1+r, n) - 1)
        total_amount = monthly_payment * n
        interest = total_amount - P

        loans = loan_calculator(
            principal_amount=P,
            annual_rate=annual_rate,
            term_year=Y,
            interest=round(interest,2),
            amount=round(total_amount,2),
            monthly_payment=round(monthly_payment,2),
            balance=round(total_amount,2),
        )

        try:
            db.session.add(loans)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving loan data: {str(e)}', 'error')
            return redirect('/loan_calculator')

        chart_folder = os.path.join('static', 'loan_charts')
        os.makedirs(chart_folder, exist_ok=True)

        # Pie Chart
        plt.figure()
        plt.pie(
            [P, interest, monthly_payment],
            labels=["Principal", "Interest", "Monthly Payment"],
            autopct='%1.1f%%'
        )
        plt.title("Loan Distribution")

        pie_path = os.path.join(chart_folder, f"loan_{loans.id}_pie.png")
        plt.savefig(pie_path)
        plt.close()

        # Line Chart
        plt.figure()
        plt.plot(
            ["Principal", "Total Amount", "Monthly Payment"],
            [P, total_amount, monthly_payment]
        )
        plt.title("Loan Comparison")
        plt.xlabel("Components")
        plt.ylabel("Amount")

        line_path = os.path.join(chart_folder, f"loan_{loans.id}_line.png")
        plt.savefig(line_path)
        plt.close()

        return redirect('/loan_calculator')

    
    return render_template('calculator.html', loans=loans)
  

@app.route('/send_vendor_sms', methods=['POST'])
def send_vendor_sms():
    # Accept JSON or form-encoded data
    data = request.get_json(silent=True) or request.form.to_dict()
    method = (data.get('method') or 'email').lower()
    recipient = data.get('recipient')
    vendor_id = data.get('vendor_id')
    include_details_raw = data.get('include_details', True)
    include_details = False
    if isinstance(include_details_raw, bool):
        include_details = include_details_raw
    else:
        include_details = str(include_details_raw).lower() in ('1', 'true', 'yes', 'on')

    if not recipient:
        return jsonify({'status': 'failed', 'message': 'recipient is required'}), 400

    # for that vendor if vendor_id provided, otherwise global
    query = Product.query.filter(Product.stock_quantity <= 0)
    vendor_id_int = None
    if vendor_id:
        try:
            vendor_id_int = int(vendor_id)
            query = query.filter(Product.vendor_id == vendor_id_int)
        except Exception:
            pass

    sold_out_items = query.all()

    if not sold_out_items:
        return jsonify({'status': 'no_items', 'message': 'No sold-out items found'}), 200

    subject = 'Sold-out items notifications'
    body_lines = []
    if vendor_id_int:
        v = Vendor.query.get(vendor_id_int)
        if v:
            body_lines.append(f"Vendor: {v.name} / {v.company}")

    body_lines.append('Sold out items:')
    for p in sold_out_items:
        if include_details and getattr(p, 'sku', None):
            body_lines.append(f"- {p.name} (SKU: {getattr(p, 'sku')})")
        elif include_details:
            # fallback to id when SKU isn't available
            body_lines.append(f"- {p.name} (ID: {p.id})")
        else:
            body_lines.append(f"- {p.name}")
    body = '\n'.join(body_lines)

    status = 'failed'
    response_text = ''

    # send email if requested and configured
    if method == 'email' and app.config.get('MAIL_USERNAME'):
        try:
            msg = Message(subject=subject, recipients=[recipient], body=body, sender=app.config['MAIL_USERNAME'])
            mail.send(msg)
            status = 'sent'
            response_text = 'email sent'
        except Exception as e:
            status = 'failed'
            response_text = str(e)
    else:
        # sms via Twilio
        from twilio.rest import Client
        sid = os.getenv('TWILIO_ACCOUNT_SID')
        token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_from = os.getenv('TWILIO_PHONE')

        try:
            client = Client(sid, token)
            msgobj = client.messages.create(body=body, from_=twilio_from, to=recipient)
            status = 'sent'
            response_text = getattr(msgobj, 'sid', str(msgobj))
        except Exception as e:
            status = 'failed'
            response_text = str(e)

    # log
    log = Notification_log(method=('email' if method == 'email' else 'sms'), recipient=recipient, subject=subject, body=body, status=status, response=response_text)
    db.session.add(log)
    db.session.commit()

    return jsonify({'status': status, 'response': response_text}), (200 if status == 'sent' else 500)

#small API to update stock after a sale
@app.route('/api/decrease_stock', methods=['POST'])
def decrease_stock():
    data = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    if product_id is None:
        return jsonify({'error': 'product_id is required'}), 400
    amount = int(data.get('amount', 1))
    p = Product.query.get(product_id)
    if not p:
        return jsonify({'error': 'product_not_found'}), 404

    if p.stock_quantity <= 0:
        return jsonify({'error': 'out_of_stock'}), 400

    tx = InventryTransactions(product_id=product_id, change_amount=-amount, reason='sale')
    p.stock_quantity -= amount
    if p.stock_quantity <= 0:
        p.stock_quantity = 0
        p.Stock = 'out_of_stock'
    db.session.add(tx)
    db.session.commit()
    return jsonify({'product_id': p.id, 'Available_Quantity': p.stock_quantity}), 200

@app.route('/update_stock/<int:id>', methods=['POST'])
def update_stock(id):
    quantity = int(request.form.get('stock_quantity', 0))
    product = Product.query.get_or_404(id)
    product.stock_quantity = quantity

    if quantity == 0:
        product.Stock = 'out_of_stock'
    else:
        product.Stock = 'Available'

    db.session.add(product)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    vendor = Vendor(
        name=request.form['vendor_name'],
        company=request.form['company_name'],
        phone=request.form['phone'],
        email=request.form['email'],
        address=request.form.get('address', '')
    )
    db.session.add(vendor)
    db.session.commit()
    return redirect('/vendor')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')

