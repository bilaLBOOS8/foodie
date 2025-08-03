from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
# احذف: from flask_migrate import Migrate
from datetime import datetime
import json
import os
import uuid
from werkzeug.utils import secure_filename
from config import config
from models import db, MenuItem, Order, Settings
from database import init_database, get_settings, update_setting

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    # احذف: migrate = Migrate(app, db)
    
    # Initialize database
    init_database(app)
    
    return app

app = create_app()

# Load settings from database
with app.app_context():
    SETTINGS = get_settings()
    RESTAURANT_INFO = SETTINGS.get('restaurant_info', {})
    ADMIN_CREDENTIALS = SETTINGS.get('admin_credentials', {'username': 'admin', 'password': 'admin'})
    ADMIN_USERNAME = ADMIN_CREDENTIALS['username']
    ADMIN_PASSWORD = ADMIN_CREDENTIALS['password']

# Languages
LANGUAGES = {
    'ar': {
        'name': 'العربية',
        'home': 'الرئيسية',
        'menu': 'القائمة',
        'cart': 'السلة',
        'admin': 'الإدارة',
        'language': 'اللغة',
        'order_success': 'تم إرسال طلبك بنجاح!',
        'order_updated': 'تم تحديث حالة الطلب',
        'item_added': 'تم إضافة العنصر بنجاح',
        'item_updated': 'تم تحديث العنصر بنجاح',
        'item_deleted': 'تم حذف العنصر بنجاح',
        'added_to_cart': 'تم إضافة الوجبة إلى السلة',
        'cart_updated': 'تم تحديث السلة',
        'cart_empty': 'السلة فارغة',
        'currency': 'د.م'
    },
    'fr': {
        'name': 'Français',
        'home': 'Accueil',
        'menu': 'Menu',
        'cart': 'Panier',
        'admin': 'Administration',
        'language': 'Langue',
        'order_success': 'Votre commande a été envoyée avec succès!',
        'order_updated': 'Statut de la commande mis à jour',
        'item_added': 'Article ajouté avec succès',
        'item_updated': 'Article mis à jour avec succès',
        'item_deleted': 'Article supprimé avec succès',
        'added_to_cart': 'Plat ajouté au panier',
        'cart_updated': 'Panier mis à jour',
        'cart_empty': 'Panier vide',
        'currency': 'MAD'
    }
}

def get_language():
    return session.get('language', 'ar')

def get_text(key):
    return LANGUAGES.get(get_language(), {}).get(key, key)

@app.context_processor
def inject_language():
    return {
        'get_language': get_language,
        'get_text': get_text,
        'languages': LANGUAGES,
        'restaurant_info': RESTAURANT_INFO
    }

# Authentication
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def check_admin_credentials(username, password):
    # Refresh credentials from database
    with app.app_context():
        settings = get_settings()
        admin_creds = settings.get('admin_credentials', {})
        return (username == admin_creds.get('username') and 
                password == admin_creds.get('password'))

# File upload configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    # Get featured menu items
    featured_items = MenuItem.query.filter_by(available=True).limit(6).all()
    return render_template('index.html', featured_items=[item.to_dict() for item in featured_items])

@app.route('/menu')
@app.route('/menu/<category>')
def menu(category=None):
    if category:
        menu_items = MenuItem.query.filter_by(category=category, available=True).all()
    else:
        menu_items = MenuItem.query.filter_by(available=True).all()
    
    # Get unique categories
    categories = db.session.query(MenuItem.category).filter_by(available=True).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('menu.html', 
                         menu=[item.to_dict() for item in menu_items], 
                         categories=categories, 
                         current_category=category)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = int(request.form['item_id'])
    quantity = int(request.form.get('quantity', 1))
    
    # Get item from database
    item = MenuItem.query.get_or_404(item_id)
    
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    # Check if item already in cart
    found = False
    for cart_item in cart:
        if cart_item['id'] == item_id:
            cart_item['quantity'] += quantity
            found = True
            break
    
    if not found:
        cart.append({
            'id': item_id,
            'name': item.name,
            'price': item.price,
            'quantity': quantity,
            'image': item.image
        })
    
    session['cart'] = cart
    session.modified = True
    
    flash(get_text('added_to_cart'), 'success')
    return redirect(url_for('menu'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session.get('cart', [])
    
    for i, item in enumerate(cart):
        quantity_key = f'quantity_{item["id"]}'
        if quantity_key in request.form:
            new_quantity = int(request.form[quantity_key])
            if new_quantity > 0:
                cart[i]['quantity'] = new_quantity
            else:
                cart.pop(i)
                break
    
    session['cart'] = cart
    session.modified = True
    
    flash(get_text('cart_updated'), 'success')
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash(get_text('cart_empty'), 'warning')
        return redirect(url_for('menu'))
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place_order', methods=['POST'])
def place_order():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash(get_text('cart_empty'), 'warning')
        return redirect(url_for('menu'))
    
    # Generate tracking code
    tracking_code = str(uuid.uuid4())[:8].upper()
    
    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Create order
    order = Order(
        tracking_code=tracking_code,
        customer_name=request.form['customer_name'],
        customer_phone=request.form['customer_phone'],
        customer_address=request.form['customer_address'],
        items=json.dumps(cart_items, ensure_ascii=False),
        total_amount=total,
        notes=request.form.get('notes', ''),
        status='جديد'
    )
    
    db.session.add(order)
    db.session.commit()
    
    # Clear cart
    session.pop('cart', None)
    
    # إنشاء قاموس order للقالب مع الحقول المطلوبة
    order_data = {
        'id': order.id,
        'tracking_code': order.tracking_code,
        'customer_name': order.customer_name,
        'phone': order.customer_phone,  # القالب يتوقع 'phone'
        'address': order.customer_address,  # القالب يتوقع 'address'
        'items': cart_items,  # استخدام cart_items مباشرة
        'total': total,  # القالب يتوقع 'total'
        'status': order.status,
        'date': order.created_at.strftime('%Y-%m-%d %H:%M'),  # القالب يتوقع 'date'
        'notes': order.notes
    }
    
    flash(get_text('order_success'), 'success')
    return render_template('order_success.html', order=order_data, tracking_code=tracking_code)

@app.route('/track_order', methods=['GET', 'POST'])
def track_order():
    if request.method == 'POST':
        tracking_code = request.form['tracking_code']
        order = Order.query.filter_by(tracking_code=tracking_code).first()
        
        if order:
            return render_template('track_order.html', order=order.to_dict(), found=True)
        else:
            flash('رمز التتبع غير صحيح', 'error')
            return render_template('track_order.html', found=False)
    
    return render_template('track_order.html', found=False)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if check_admin_credentials(username, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin():
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        menu_items = MenuItem.query.all()  # إضافة قوائم الطعام
        
        # تحويل الطلبات إلى قواميس للعرض الصحيح
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            # التأكد من أن items هو قائمة وليس string
            if isinstance(order_dict['items'], str):
                try:
                    order_dict['items'] = json.loads(order_dict['items'])
                except:
                    order_dict['items'] = []
            
            # حساب المجموع إذا لم يكن موجوداً
            if not order_dict.get('total'):
                order_dict['total'] = sum(
                    item.get('price', 0) * item.get('quantity', 1) 
                    for item in order_dict['items']
                )
            else:
                order_dict['total'] = order.total_amount
            
            orders_data.append(order_dict)
        
        return render_template('admin.html', orders=orders_data, menu=menu_items)
    except Exception as e:
        print(f"Admin route error: {e}")
        return render_template('admin.html', orders=[], menu=[])

@app.route('/update_order_status', methods=['POST'])
@login_required
def update_order_status():
    order_id = int(request.form['order_id'])
    new_status = request.form['status']
    
    order = Order.query.get_or_404(order_id)
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(get_text('order_updated'), 'success')
    return redirect(url_for('admin'))

@app.route('/add_menu_item', methods=['POST'])
@login_required
def add_menu_item():
    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(file.filename)
            image_filename = f"{timestamp}_{filename}"
            file.save(os.path.join(UPLOAD_FOLDER, image_filename))
    
    # Create menu item
    menu_item = MenuItem(
        name=request.form['name'],
        name_fr=request.form.get('name_fr', ''),
        description=request.form['description'],
        description_fr=request.form.get('description_fr', ''),
        price=float(request.form['price']),
        category=request.form['category'],
        category_fr=request.form.get('category_fr', ''),
        image=image_filename,
        preparation_time=int(request.form.get('preparation_time', 15)),
        ingredients=json.dumps(request.form.get('ingredients', '').split(','), ensure_ascii=False),
        ingredients_fr=json.dumps(request.form.get('ingredients_fr', '').split(','), ensure_ascii=False)
    )
    
    db.session.add(menu_item)
    db.session.commit()
    
    flash(get_text('item_added'), 'success')
    return redirect(url_for('admin'))

@app.route('/edit_menu_item', methods=['POST'])
@login_required
def edit_menu_item():
    item_id = int(request.form['item_id'])
    item = MenuItem.query.get_or_404(item_id)
    
    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            # Delete old image
            if item.image:
                old_image_path = os.path.join(UPLOAD_FOLDER, item.image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(file.filename)
            image_filename = f"{timestamp}_{filename}"
            file.save(os.path.join(UPLOAD_FOLDER, image_filename))
            item.image = image_filename
    
    # Update item
    item.name = request.form['name']
    item.name_fr = request.form.get('name_fr', '')
    item.description = request.form['description']
    item.description_fr = request.form.get('description_fr', '')
    item.price = float(request.form['price'])
    item.category = request.form['category']
    item.category_fr = request.form.get('category_fr', '')
    item.preparation_time = int(request.form.get('preparation_time', 15))
    item.ingredients = json.dumps(request.form.get('ingredients', '').split(','), ensure_ascii=False)
    item.ingredients_fr = json.dumps(request.form.get('ingredients_fr', '').split(','), ensure_ascii=False)
    item.available = 'available' in request.form
    
    db.session.commit()
    
    flash(get_text('item_updated'), 'success')
    return redirect(url_for('admin'))

@app.route('/delete_menu_item', methods=['POST'])
@login_required
def delete_menu_item():
    item_id = int(request.form['item_id'])
    item = MenuItem.query.get_or_404(item_id)
    
    # Delete image file
    if item.image:
        image_path = os.path.join(UPLOAD_FOLDER, item.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(item)
    db.session.commit()
    
    flash(get_text('item_deleted'), 'success')
    return redirect(url_for('admin'))

@app.route('/toggle_item_availability', methods=['POST'])
@login_required
def toggle_item_availability():
    item_id = int(request.form['item_id'])
    item = MenuItem.query.get_or_404(item_id)
    
    item.available = not item.available
    db.session.commit()
    
    return jsonify({'success': True, 'available': item.available})

@app.route('/get_order_stats')
@login_required
def get_order_stats():
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='جديد').count()
    completed_orders = Order.query.filter_by(status='تم التوصيل').count()
    
    return jsonify({
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders
    })

@app.route('/set_language/<language>')
def set_language(language):
    if language in LANGUAGES:
        session['language'] = language
    return redirect(request.referrer or url_for('home'))

@app.route('/admin/settings')
@login_required
def admin_settings():
    settings = get_settings()
    return render_template('admin_settings.html', settings=settings)

@app.route('/update_restaurant_info', methods=['POST'])
@login_required
def update_restaurant_info():
    restaurant_info = {
        'name': request.form.get('name', ''),
        'name_fr': request.form.get('name_fr', ''),
        'phone': request.form.get('phone', ''),
        'location': request.form.get('location', ''),
        'location_fr': request.form.get('location_fr', ''),
        'address': request.form.get('address', ''),
        'address_fr': request.form.get('address_fr', ''),
        'email': request.form.get('email', ''),
        'working_hours': {
            'monday': {
                'open': request.form.get('monday_open', '09:00'), 
                'close': request.form.get('monday_close', '22:00'), 
                'closed': 'monday_closed' in request.form
            },
            'tuesday': {
                'open': request.form.get('tuesday_open', '09:00'), 
                'close': request.form.get('tuesday_close', '22:00'), 
                'closed': 'tuesday_closed' in request.form
            },
            'wednesday': {
                'open': request.form.get('wednesday_open', '09:00'), 
                'close': request.form.get('wednesday_close', '22:00'), 
                'closed': 'wednesday_closed' in request.form
            },
            'thursday': {
                'open': request.form.get('thursday_open', '09:00'), 
                'close': request.form.get('thursday_close', '22:00'), 
                'closed': 'thursday_closed' in request.form
            },
            'friday': {
                'open': request.form.get('friday_open', '09:00'), 
                'close': request.form.get('friday_close', '22:00'), 
                'closed': 'friday_closed' in request.form
            },
            'saturday': {
                'open': request.form.get('saturday_open', '09:00'), 
                'close': request.form.get('saturday_close', '22:00'), 
                'closed': 'saturday_closed' in request.form
            },
            'sunday': {
                'open': request.form.get('sunday_open', '09:00'), 
                'close': request.form.get('sunday_close', '22:00'), 
                'closed': 'sunday_closed' in request.form
            }
        },
        'social_media': {
            'facebook': request.form.get('facebook', ''),
            'instagram': request.form.get('instagram', ''),
            'twitter': request.form.get('twitter', '')
        }
    }
    
    update_setting('restaurant_info', restaurant_info)
    
    # Update global variable
    global RESTAURANT_INFO
    RESTAURANT_INFO = restaurant_info
    
    flash('تم تحديث معلومات المطعم بنجاح', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/update_admin_credentials', methods=['POST'])
@login_required
def update_admin_credentials():
    global ADMIN_USERNAME, ADMIN_PASSWORD
    
    current_password = request.form['current_password']
    new_username = request.form['new_username']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    # Verify current password
    if not check_admin_credentials(session.get('admin_username', ADMIN_USERNAME), current_password):
        flash('كلمة المرور الحالية غير صحيحة', 'error')
        return redirect(url_for('admin_settings'))
    
    # Check password confirmation
    if new_password != confirm_password:
        flash('كلمة المرور الجديدة غير متطابقة', 'error')
        return redirect(url_for('admin_settings'))
    
    # Update credentials
    admin_credentials = {
        'username': new_username,
        'password': new_password
    }
    
    update_setting('admin_credentials', admin_credentials)
    
    # Update global variables
    ADMIN_USERNAME = new_username
    ADMIN_PASSWORD = new_password
    
    # Update session
    session['admin_username'] = new_username
    
    flash('تم تحديث بيانات المدير بنجاح', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/update_app_settings', methods=['POST'])
@login_required
def update_app_settings():
    """Update application settings like currency, tax rate, etc."""
    try:
        app_settings = {
            'currency': request.form.get('currency', 'د.م'),
            'currency_fr': request.form.get('currency_fr', 'MAD'),
            'tax_rate': float(request.form.get('tax_rate', 0)),
            'delivery_fee': float(request.form.get('delivery_fee', 0)),
            'min_order_amount': float(request.form.get('min_order_amount', 0))
        }
        
        # Update the settings in database
        update_setting('app_settings', app_settings)
        
        flash('تم تحديث إعدادات التطبيق بنجاح', 'success')
        
    except ValueError as e:
        flash('خطأ في البيانات المدخلة. تأكد من صحة الأرقام.', 'error')
    except Exception as e:
        flash(f'حدث خطأ أثناء تحديث الإعدادات: {str(e)}', 'error')
    
    return redirect(url_for('admin_settings'))

# في بداية الملف، أضف هذا:
import os
os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=port)