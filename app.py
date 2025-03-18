from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'medcare_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    stock = db.Column(db.Integer, default=0)
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)
    
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200), nullable=True)
    
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='pending')
    
class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Float, default=0)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

# Routes
@app.route('/')
def index():
    featured_products = Product.query.limit(6).all()
    doctors = Doctor.query.limit(3).all()
    return render_template('index.html', 
                          featured_products=featured_products,
                          doctors=doctors)

@app.route('/products')
def products():
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('search', '')
    
    if category_id:
        products = Product.query.filter_by(category_id=category_id).all()
    elif search_query:
        products = Product.query.filter(Product.name.contains(search_query)).all()
    else:
        products = Product.query.all()
        
    categories = Category.query.all()
    return render_template('products.html', products=products, categories=categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(category_id=product.category_id).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/doctors')
def doctors():
    doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=doctors)

@app.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    if 'user_id' not in session:
        flash('Please login to book an appointment', 'warning')
        return redirect(url_for('login'))
        
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        date = request.form.get('date')
        time = request.form.get('time')
        
        appointment = Appointment(
            user_id=session['user_id'],
            doctor_id=doctor_id,
            date=datetime.strptime(date, '%Y-%m-%d'),
            time=time
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('user_appointments'))
        
    return render_template('book_appointment.html', doctor=doctor)

@app.route('/hospitals')
def hospitals():
    hospitals = Hospital.query.all()
    return render_template('hospitals.html', hospitals=hospitals)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_admin'] = user.is_admin
            
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            flash('Email already registered', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password=hashed_password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Please login to add items to cart', 'warning')
        return redirect(url_for('login'))
        
    quantity = int(request.form.get('quantity', 1))
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(
        user_id=session['user_id'],
        product_id=product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=session['user_id'],
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
        
    db.session.commit()
    flash('Item added to cart!', 'success')
    
    return redirect(request.referrer or url_for('products'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view your cart', 'warning')
        return redirect(url_for('login'))
        
    cart_items = db.session.query(
        CartItem, Product
    ).join(
        Product, CartItem.product_id == Product.id
    ).filter(
        CartItem.user_id == session['user_id']
    ).all()
    
    total = sum(item.Product.price * item.CartItem.quantity for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    return render_template('user_dashboard.html')

@app.route('/user/appointments')
def user_appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    appointments = db.session.query(
        Appointment, Doctor
    ).join(
        Doctor, Appointment.doctor_id == Doctor.id
    ).filter(
        Appointment.user_id == session['user_id']
    ).all()
    
    return render_template('user_appointments.html', appointments=appointments)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
        
    product_count = Product.query.count()
    user_count = User.query.count()
    appointment_count = Appointment.query.count()
    
    return render_template('admin/dashboard.html', 
                          product_count=product_count,
                          user_count=user_count,
                          appointment_count=appointment_count)

# Initialize database
@app.cli.command('init-db')
def init_db():
    db.create_all()
    
    # Add sample data if database is empty
    if not Category.query.first():
        categories = [
            Category(name='Pain Relief'),
            Category(name='Antibiotics'),
            Category(name='Vitamins'),
            Category(name='First Aid'),
            Category(name='Skin Care')
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        products = [
            Product(name='Paracetamol', price=50, category_id=1, 
                   image_url='/static/images/products/paracetamol.jpg',
                   description='Effective pain relief medication', stock=100),
            Product(name='Ibuprofen', price=80, category_id=1, 
                   image_url='/static/images/products/ibuprofen.jpg',
                   description='Anti-inflammatory pain reliever', stock=75),
            Product(name='Amoxicillin', price=150, category_id=2, 
                   image_url='/static/images/products/amoxicillin.jpg',
                   description='Broad-spectrum antibiotic', stock=50),
            Product(name='Cetirizine', price=30, category_id=1, 
                   image_url='/static/images/products/cetirizine.jpg',
                   description='Antihistamine for allergies', stock=120),
            Product(name='Dolo 650', price=70, category_id=1, 
                   image_url='/static/images/products/dolo.jpg',
                   description='Fever and pain medication', stock=90),
            Product(name='Vitamin C', price=120, category_id=3, 
                   image_url='/static/images/products/vitamin_c.jpg',
                   description='Immunity booster', stock=200)
        ]
        db.session.add_all(products)
        
        doctors = [
            Doctor(name='Dr. Sarah Johnson', specialization='Cardiologist', 
                  experience=15, image_url='/static/images/doctors/doctor1.jpg'),
            Doctor(name='Dr. Michael Chen', specialization='Pediatrician', 
                  experience=10, image_url='/static/images/doctors/doctor2.jpg'),
            Doctor(name='Dr. Emily Williams', specialization='Dermatologist', 
                  experience=8, image_url='/static/images/doctors/doctor3.jpg')
        ]
        db.session.add_all(doctors)
        
        hospitals = [
            Hospital(name='City General Hospital', address='123 Main St, City Center', 
                    phone='555-1234', rating=4.5, latitude=40.7128, longitude=-74.0060),
            Hospital(name='MedCare Specialty Clinic', address='456 Park Ave, Downtown', 
                    phone='555-5678', rating=4.8, latitude=40.7308, longitude=-73.9973),
            Hospital(name='Community Health Center', address='789 Broadway, Uptown', 
                    phone='555-9012', rating=4.2, latitude=40.7589, longitude=-73.9851)
        ]
        db.session.add_all(hospitals)
        
        # Create admin user
        admin = User(
            name='Admin',
            email='admin@medcare.com',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        
        db.session.commit()
        print('Database initialized with sample data!')

if __name__ == '__main__':
    app.run(debug=True)

