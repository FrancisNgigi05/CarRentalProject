from flask import Flask, render_template, url_for, redirect, flash, abort, request, jsonify
from flask_migrate import Migrate
from models import db, User, Car, Rental
from forms import RegisterForm, LoginForm
from flask_bcrypt import Bcrypt
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secretkey'

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
       
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# @app.route('/admin', methods=['GET', 'POST'])
# @login_required
# def admin_dashboard():
#     if current_user.role != 'admin':
#         abort(403)
#     return render_template('admin.html')


# @app.route('/dashboard', methods=['GET', 'POST'])
# @login_required
# def dashboard():
#     return render_template('dashboard.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/cars', methods=['GET'])
@login_required
def view_cars():
    cars = Car.query.filter_by(status='available').all()
    return render_template('cars.html', cars=cars)

@app.route('/cars/<int:car_id>/rent', methods=['POST'])
@login_required
def rent_car(car_id):
    car = Car.query.get_or_404(car_id)
    if car.status != 'available':
        flash("Car is not available.", "Warning")
        return redirect(url_for('view_cars'))
    car.status = 'rented'
    rental = Rental(user_id=current_user.id, car_id=car_id, start_date=datetime.utcnow(), status='ongoing')
    db.session.add(rental)
    db.session.commit()
    flash("Car rented successfully!", "success")
    return redirect(url_for('user_rentals'))

@app.route('/rentals/<int:rental_id>/return', methods=['POST'])
@login_required
def return_car(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.user_id != current_user.id:
        abort(403)
    rental.end_date = datetime.utcnow()
    rental.status = 'returned'
    rental.car.status = 'available'
    db.session.commit()
    flash("Car returned successfully", "success")
    return redirect(url_for('user_rentals'))

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return redirect(url_for('view_cars'))



@app.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    return redirect(url_for('admin_view_cars'))

@app.route('/admin/cars', methods=['GET'])
@login_required
def admin_view_cars():
    if current_user.role != 'admin':
        abort(403)
    cars = Car.query.all()
    return render_template('admin_cars.html', cars=cars)

@app.route('/admin/cars/add', methods=['POST'])
@login_required
def admin_add_car():
    if current_user.role != 'admin':
        abort(403)
    name = request.form.get('name')
    image = request.form.get('image') or 'https://via.placeholder.com/300x180?text=Car+Image'
    new_car = Car(name=name, status='available', image=image)
    db.session.add(new_car)
    db.session.commit()
    flash("Car added successfully!", "success")
    return redirect(url_for('admin_view_cars'))

@app.route('/admin/cars/<int:car_id>/delete', methods=['POST'])
@login_required
def admin_delete_car(car_id):
    if current_user.role != 'admin':
        abort(403)
    car = Car.query.get_or_404(car_id)
    db.session.delete(car)
    db.session.commit()
    flash("Car deleted.", "info")
    return redirect(url_for('admin_view_cars'))

@app.route('/admin/rentals', methods=['GET'])
@login_required
def admin_view_rentals():
    if current_user.role != 'admin':
        abort(403)
    rentals = Rental.query.all()
    return render_template('admin_rentals.html', rentals=rentals)

if __name__ == '__main__':
    app.run(debug=True)