# Foodie Restaurant Management System

نظام إدارة مطعم شامل مع دعم اللغتين العربية والفرنسية، مبني باستخدام Flask و PostgreSQL.

## المميزات

- 🍽️ إدارة قائمة الطعام مع الصور
- 🛒 نظام سلة التسوق
- 📱 واجهة متجاوبة مع الهواتف المحمولة
- 🌐 دعم اللغتين العربية والفرنسية
- 📊 لوحة تحكم للإدارة
- 📦 تتبع الطلبات
- 🔐 نظام مصادقة آمن
- 🖼️ رفع وإدارة الصور

## التقنيات المستخدمة

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: PostgreSQL (Production), SQLite (Development)
- **Deployment**: Render

## التثبيت المحلي

1. استنساخ المشروع:
```bash
git clone <repository-url>
cd Foodie
```

2. إنشاء بيئة افتراضية:
```bash
python -m venv venv
source venv/bin/activate  # على Linux/Mac
venv\Scripts\activate     # على Windows
```

3. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

4. إعداد متغيرات البيئة:
```bash
cp .env.example .env
# قم بتحرير ملف .env وإضافة القيم المناسبة
```

5. تشغيل التطبيق:
```bash
python app.py
```

## النشر على Render

### 1. إعداد قاعدة البيانات

1. انتقل إلى [Render Dashboard](https://dashboard.render.com)
2. أنشئ خدمة PostgreSQL جديدة:
   - اختر "New" > "PostgreSQL"
   - أدخل اسم قاعدة البيانات
   - اختر المنطقة المناسبة
   - انقر "Create Database"

3. احفظ معلومات الاتصال:
   - `Database URL` (Internal)
   - `Database URL` (External)

### 2. نشر التطبيق

1. أنشئ خدمة ويب جديدة:
   - اختر "New" > "Web Service"
   - اربط مستودع GitHub الخاص بك
   - اختر فرع النشر

2. إعداد الخدمة:
   - **Name**: اسم التطبيق
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

3. إضافة متغيرات البيئة:
   ```
   FLASK_ENV=production
   DEBUG=False
   DATABASE_URL=<database-url-from-step-1>
   SECRET_KEY=<your-secret-key>
   ```

4. انقر "Create Web Service"

### 3. إعداد قاعدة البيانات

بعد نشر التطبيق، ستتم تهيئة قاعدة البيانات تلقائياً مع:
- إنشاء الجداول المطلوبة
- تحميل البيانات الافتراضية من ملفات JSON (إن وجدت)
- إعداد حساب المدير الافتراضي

## بيانات الدخول الافتراضية

- **اسم المستخدم**: admin
- **كلمة المرور**: admin

⚠️ **مهم**: قم بتغيير بيانات الدخول فور النشر من لوحة الإعدادات.

## هيكل المشروع

```
Foodie/
├── app.py              # التطبيق الرئيسي
├── models.py           # نماذج قاعدة البيانات
├── config.py           # إعدادات التطبيق
├── database.py         # إدارة قاعدة البيانات
├── requirements.txt    # متطلبات Python
├── Procfile           # إعدادات Render
├── runtime.txt        # إصدار Python
├── templates/         # قوالب HTML
├── static/           # ملفات CSS, JS, الصور
├── data/             # ملفات JSON (للتطوير)
└── migrations/       # ملفات ترحيل قاعدة البيانات
```

## الدعم

للحصول على المساعدة أو الإبلاغ عن مشاكل، يرجى فتح issue في المستودع.

## الترخيص

هذا المشروع مرخص تحت رخصة MIT.