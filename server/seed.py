from app import app
from models import db, User, Car, Rental
from flask_bcrypt import Bcrypt
from faker import Faker
from datetime import datetime, timedelta
import random

bcrypt = Bcrypt()
fake = Faker()

with app.app_context():
    db.drop_all()
    db.create_all()

    # Admin
    admin = User(username='admin', password=bcrypt.generate_password_hash('adminpass').decode('utf-8'), role='admin')
    db.session.add(admin)
    frank = User(username = 'frank', password=bcrypt.generate_password_hash('adminpass').decode('utf-8'), role='user')
    db.session.add(frank)

    # Users
    users = []
    for _ in range(5):
        username = fake.user_name()
        password = bcrypt.generate_password_hash('password').decode('utf-8')
        users.append(User(username=username, password=password, role='user'))
    db.session.add_all(users)
    db.session.commit()

    # Cars
    statuses = ['available', 'rented']
    cars = []
    for _ in range(10):
        car = Car(
            name=fake.company() + " " + fake.word().capitalize(),
            status=fake.random_element(elements=statuses),
            image='https://via.placeholder.com/300x180?text=Car+Image'
        )
        cars.append(car)
    db.session.add_all(cars)
    db.session.commit()

    # Rentals (only for cars marked as 'rented')
    rented_cars = Car.query.filter_by(status='rented').all()
    all_users = User.query.filter_by(role='user').all()
    for i in range(min(len(rented_cars), len(all_users))):
        start_date = datetime.now() - timedelta(days=random.randint(1, 10))
        end_date = start_date + timedelta(days=random.randint(1, 7))
        rental = Rental(
            user_id=all_users[i].id,
            car_id=rented_cars[i].id,
            start_date=start_date,
            end_date=end_date,
            status='ongoing'
        )
        db.session.add(rental)

    db.session.commit()
    print("Database seeded successfully.")
