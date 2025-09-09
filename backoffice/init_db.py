#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/app')

from app import app
from models import db, Backend_Users, Profile, Organizacao, Backyard, Atleta, AtletaBackyard, Loop, AtletaLoop
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize database with tables and default data"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Create default profiles if they don't exist
        if not Profile.query.filter_by(nome='Admin').first():
            print("Creating Admin profile...")
            admin_profile = Profile(nome='Admin')
            db.session.add(admin_profile)
            db.session.commit()
            print("Admin profile created!")
        
        if not Profile.query.filter_by(nome='Organizador').first():
            print("Creating Organizador profile...")
            organizador_profile = Profile(nome='Organizador')
            db.session.add(organizador_profile)
            db.session.commit()
            print("Organizador profile created!")
        
        # Create default admin user if no users exist
        if not Backend_Users.query.first():
            print("Creating default admin user...")
            admin_profile = Profile.query.filter_by(nome='Admin').first()
            admin_user = Backend_Users(
                nome='Administrator',
                email='admin@btl.com',
                password=generate_password_hash('admin123'),
                profile_id=admin_profile.id
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: admin@btl.com / admin123")
        
        print("Database initialization completed successfully!")

if __name__ == '__main__':
    init_database()
