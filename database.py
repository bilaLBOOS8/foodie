import json
import os
from models import db, MenuItem, Order, Settings
from datetime import datetime
import uuid

def init_database(app):
    """Initialize database and migrate data from JSON files if needed"""
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            print("Database tables created successfully")
            
            # Check if data already exists before migrating
            if MenuItem.query.first() is None:
                migrate_menu_data()
            
            if Settings.query.first() is None:
                migrate_settings_data()
            
            # Migrate orders if any exist in JSON
            migrate_orders_data()
            
            print("Data migration completed")
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Create basic structure if migration fails
        try:
            with app.app_context():
                db.create_all()
                print("Basic database structure created")
        except Exception as inner_e:
            print(f"Critical database error: {inner_e}")

def migrate_menu_data():
    """Migrate menu data from JSON to database"""
    menu_file = os.path.join('data', 'menu.json')
    if os.path.exists(menu_file):
        with open(menu_file, 'r', encoding='utf-8') as f:
            menu_data = json.load(f)
        
        for item_data in menu_data:
            # تصحيح التعامل مع التاريخ
            created_at_str = item_data.get('created_at')
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except ValueError:
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()
            
            menu_item = MenuItem(
                id=item_data.get('id'),
                name=item_data.get('name'),
                name_fr=item_data.get('name_fr'),
                description=item_data.get('description'),
                description_fr=item_data.get('description_fr'),
                price=item_data.get('price'),
                category=item_data.get('category'),
                category_fr=item_data.get('category_fr'),
                image=item_data.get('image'),
                available=item_data.get('available', True),
                preparation_time=item_data.get('preparation_time', 15),
                ingredients=json.dumps(item_data.get('ingredients', []), ensure_ascii=False),
                ingredients_fr=json.dumps(item_data.get('ingredients_fr', []), ensure_ascii=False),
                created_at=created_at
            )
            db.session.add(menu_item)
        
        db.session.commit()
        print(f"Migrated {len(menu_data)} menu items to database")

def migrate_orders_data():
    """Migrate orders data from JSON to database"""
    orders_file = os.path.join('data', 'orders.json')
    if os.path.exists(orders_file):
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders_data = json.load(f)
        
        for order_data in orders_data:
            # Check if order already exists
            tracking_code = order_data.get('tracking_code') or order_data.get('order_number') or str(uuid.uuid4())[:8].upper()
            existing_order = Order.query.filter_by(tracking_code=tracking_code).first()
            if not existing_order:
                order = Order(
                    tracking_code=tracking_code,
                    customer_name=order_data.get('customer_name'),
                    customer_phone=order_data.get('customer_phone'),
                    customer_address=order_data.get('customer_address'),
                    items=json.dumps(order_data.get('items', []), ensure_ascii=False),
                    total_amount=order_data.get('total_amount') or order_data.get('total'),
                    status=order_data.get('status', 'جديد'),
                    notes=order_data.get('notes', ''),
                    created_at=datetime.fromisoformat(order_data.get('created_at', datetime.utcnow().isoformat())),
                    updated_at=datetime.fromisoformat(order_data.get('updated_at', order_data.get('created_at', datetime.utcnow().isoformat())))
                )
                db.session.add(order)
        
        db.session.commit()
        print(f"Migrated {len(orders_data)} orders to database")

def migrate_settings_data():
    """Migrate settings data from JSON to database"""
    settings_file = os.path.join('data', 'settings.json')
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings_data = json.load(f)
        
        # Store each top-level setting as a separate record
        for key, value in settings_data.items():
            setting = Settings(
                key=key,
                value=json.dumps(value, ensure_ascii=False)
            )
            db.session.add(setting)
        
        db.session.commit()
        print("Migrated settings to database")
    else:
        # Create default settings
        default_settings = {
            'restaurant_info': {
                'name': 'مطعم فودي',
                'name_fr': 'Restaurant Foodie',
                'address': 'الدار البيضاء، المغرب',
                'address_fr': 'Casablanca, Maroc',
                'phone': '+212 5XX-XXXXXX',
                'email': 'info@foodie.ma',
                'description': 'مطعم مغربي أصيل يقدم أشهى الأطباق التقليدية',
                'description_fr': 'Restaurant marocain authentique servant les plats traditionnels les plus délicieux'
            },
            'admin_credentials': {
                'username': 'restaurant_admin',
                'password': 'SecurePass@2024!'
            }
        }
        
        for key, value in default_settings.items():
            setting = Settings(
                key=key,
                value=json.dumps(value, ensure_ascii=False)
            )
            db.session.add(setting)
        
        db.session.commit()
        print("Created default settings in database")

def get_settings():
    """Get all settings from database"""
    settings = {}
    for setting in Settings.query.all():
        settings[setting.key] = json.loads(setting.value)
    return settings

def update_setting(key, value):
    """Update a setting in database"""
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        setting.value = json.dumps(value, ensure_ascii=False)
        setting.updated_at = datetime.utcnow()
    else:
        setting = Settings(
            key=key,
            value=json.dumps(value, ensure_ascii=False)
        )
        db.session.add(setting)
    
    db.session.commit()
    return setting