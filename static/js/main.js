// Foodie Restaurant JavaScript Functions

// تهيئة التطبيق عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // تطبيق الرسوم المتحركة
    animateElements();
    
    // تهيئة النماذج
    initializeForms();
    
    // تهيئة السلة
    initializeCart();
    
    // تهيئة الإشعارات
    initializeNotifications();
    
    // تحديث الوقت
    updateTime();
}

// الرسوم المتحركة
function animateElements() {
    // تحريك البطاقات عند الظهور
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
    
    // تحريك الأزرار
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.classList.add('pulse');
        });
        
        button.addEventListener('mouseleave', function() {
            this.classList.remove('pulse');
        });
    });
}

// تهيئة النماذج
function initializeForms() {
    // التحقق من صحة النماذج
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        if (form) {
            form.addEventListener('submit', function(event) {
                if (!validateForm(this)) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                this.classList.add('was-validated');
            });
        }
    });
    
    // تنسيق أرقام الهاتف
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        if (input) {
            input.addEventListener('input', function() {
                formatPhoneNumber(this);
            });
        }
    });
    
    // تغيير حجم النص التلقائي
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        if (textarea) {
            textarea.addEventListener('input', function() {
                autoResize(this);
            });
        }
    });
}

// تهيئة السلة
function initializeCart() {
    // تحديث عداد السلة
    updateCartCount();
    
    // أزرار الكمية
    const quantityButtons = document.querySelectorAll('.quantity-btn');
    quantityButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            const itemId = this.dataset.itemId;
            updateQuantity(itemId, action);
        });
    });
    
    // حفظ السلة في localStorage
    saveCartToStorage();
}

// تهيئة الإشعارات
function initializeNotifications() {
    // إخفاء الإشعارات تلقائياً
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            fadeOut(alert);
        }, 5000);
    });
}

// التحقق من صحة النماذج
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // التحقق من البريد الإلكتروني
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            field.classList.add('is-invalid');
            isValid = false;
        }
    });
    
    // التحقق من رقم الهاتف
    const phoneFields = form.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(field => {
        if (field.value && !isValidPhone(field.value)) {
            field.classList.add('is-invalid');
            isValid = false;
        }
    });
    
    return isValid;
}

// تنسيق رقم الهاتف
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    
    // تنسيق للأرقام المغربية
    if (value.startsWith('212')) {
        value = value.substring(3);
    }
    
    if (value.startsWith('0')) {
        value = value.substring(1);
    }
    
    if (value.length >= 9) {
        value = value.substring(0, 9);
        value = `+212 ${value.substring(0, 1)} ${value.substring(1, 3)} ${value.substring(3, 5)} ${value.substring(5, 7)} ${value.substring(7, 9)}`;
    }
    
    input.value = value;
}

// تحسين حجم textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// تحدية الكمية
function updateQuantity(itemId, action) {
    const quantityElement = document.querySelector(`#quantity-${itemId}`);
    let quantity = parseInt(quantityElement.textContent);
    
    if (action === 'increase') {
        quantity++;
    } else if (action === 'decrease' && quantity > 1) {
        quantity--;
    }
    
    quantityElement.textContent = quantity;
    
    // تحديث السعر الإجمالي
    updateItemTotal(itemId, quantity);
    updateCartTotal();
    
    // إرسال التحديث للخادم
    sendQuantityUpdate(itemId, action);
}

// تحديث إجمالي العنصر
function updateItemTotal(itemId, quantity) {
    const priceElement = document.querySelector(`#price-${itemId}`);
    const totalElement = document.querySelector(`#total-${itemId}`);
    
    if (priceElement && totalElement) {
        const price = parseFloat(priceElement.dataset.price);
        const total = price * quantity;
        totalElement.textContent = total.toFixed(2);
    }
}

// تحديث إجمالي السلة
function updateCartTotal() {
    const totalElements = document.querySelectorAll('[id^="total-"]');
    let grandTotal = 0;
    
    totalElements.forEach(element => {
        grandTotal += parseFloat(element.textContent);
    });
    
    const grandTotalElement = document.querySelector('#grand-total');
    if (grandTotalElement) {
        grandTotalElement.textContent = grandTotal.toFixed(2);
    }
    
    // تحديث رسوم التوصيل
    updateDeliveryFee(grandTotal);
}

// تحديث رسوم التوصيل
function updateDeliveryFee(total) {
    const deliveryElement = document.querySelector('#delivery-fee');
    const finalTotalElement = document.querySelector('#final-total');
    
    if (deliveryElement && finalTotalElement) {
        const deliveryFee = total >= 100 ? 0 : 15;
        deliveryElement.textContent = deliveryFee.toFixed(2);
        finalTotalElement.textContent = (total + deliveryFee).toFixed(2);
    }
}

// إرسال تحديث الكمية للخادم
function sendQuantityUpdate(itemId, action) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/update_cart';
    
    const itemIdInput = document.createElement('input');
    itemIdInput.type = 'hidden';
    itemIdInput.name = 'item_id';
    itemIdInput.value = itemId;
    
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = action;
    
    form.appendChild(itemIdInput);
    form.appendChild(actionInput);
    document.body.appendChild(form);
    
    // إرسال النموذج بشكل غير متزامن
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
    }).then(response => {
        if (response.ok) {
            updateCartCount();
        }
    }).catch(error => {
        console.error('خطأ في تحديث السلة:', error);
    });
    
    document.body.removeChild(form);
}

// تحديث عداد السلة
function updateCartCount() {
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge) {
        const cartItems = document.querySelectorAll('[id^="quantity-"]');
        let totalItems = 0;
        
        cartItems.forEach(item => {
            totalItems += parseInt(item.textContent);
        });
        
        cartBadge.textContent = totalItems;
        
        if (totalItems === 0) {
            cartBadge.style.display = 'none';
        } else {
            cartBadge.style.display = 'block';
        }
    }
}

// حفظ السلة في التخزين المحلي
function saveCartToStorage() {
    const cartItems = [];
    const items = document.querySelectorAll('[data-item-id]');
    
    items.forEach(item => {
        const itemId = item.dataset.itemId;
        const quantity = document.querySelector(`#quantity-${itemId}`)?.textContent || 0;
        
        if (quantity > 0) {
            cartItems.push({
                id: itemId,
                quantity: parseInt(quantity)
            });
        }
    });
    
    localStorage.setItem('foodie_cart', JSON.stringify(cartItems));
}

// عرض الإشعارات
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(notification, container.firstChild);
        
        // إخفاء الإشعار تلقائياً
        setTimeout(() => {
            fadeOut(notification);
        }, 5000);
    }
}

// إخفاء العنصر تدريجياً
function fadeOut(element) {
    element.style.transition = 'opacity 0.5s';
    element.style.opacity = '0';
    
    setTimeout(() => {
        if (element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }, 500);
}

// التحقق من صحة البريد الإلكتروني
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// التحقق من صحة رقم الهاتف
function isValidPhone(phone) {
    const phoneRegex = /^\+?[0-9\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

// تحديث الوقت
function updateTime() {
    const timeElements = document.querySelectorAll('.current-time');
    
    if (timeElements.length > 0) {
        setInterval(() => {
            const now = new Date();
            const timeString = now.toLocaleTimeString('ar-MA');
            
            timeElements.forEach(element => {
                element.textContent = timeString;
            });
        }, 1000);
    }
}

// تحميل الصور بشكل تدريجي
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// تصدير الوظائف للاستخدام العام
window.FoodieApp = {
    showNotification,
    updateQuantity,
    validateForm,
    formatPhoneNumber,
    updateCartCount,
    saveCartToStorage
};

// تهيئة تحميل الصور التدريجي
if ('IntersectionObserver' in window) {
    lazyLoadImages();
}

// إضافة مستمع للأخطاء العامة
window.addEventListener('error', function(e) {
    console.error('خطأ في التطبيق:', e.error);
});

// تحسين الأداء - تأجيل تحميل الموارد غير الضرورية
window.addEventListener('load', function() {
    // تحميل الموارد الإضافية بعد تحميل الصفحة
    setTimeout(() => {
        // يمكن إضافة تحميل موارد إضافية هنا
    }, 1000);
});