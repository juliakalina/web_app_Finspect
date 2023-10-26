from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/db_app'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class FinancialTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('accounts', lazy=True))

def update_account_balance(account_id):
    account = Account.query.get(account_id)
    if account:
        transactions = FinancialTransaction.query.filter_by(account_id=account_id)
        total = sum(transaction.amount for transaction in transactions)
        account.balance = total
        db.session.commit()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            flash('Login successful.', 'success')
            return redirect(url_for('dashboard'))
        flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        transactions = FinancialTransaction.query.filter_by(user_id=user_id).all()
        accounts = Account.query.filter_by(user_id=user_id).all()
        return render_template('dashboard.html', transactions=transactions, accounts=accounts)
    return redirect(url_for('login'))

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if 'user_id' in session:
        if request.method == 'POST':
            user_id = session['user_id']
            date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            amount = float(request.form['amount'])
            category = request.form['category']
            source = request.form['source']
            account_id = int(request.form['account'])
            transaction = FinancialTransaction(date=date, amount=amount, category=category, source=source, user_id=user_id, account_id=account_id)
            db.session.add(transaction)
            db.session.commit()
            update_account_balance(account_id)
            flash('Transaction added successfully.', 'success')
            return redirect(url_for('dashboard'))
        accounts = Account.query.filter_by(user_id=session['user_id']).all()
        return render_template('add_transaction.html', accounts=accounts)
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

