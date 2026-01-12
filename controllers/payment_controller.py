from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from models import PaymentModel, SecurityLogModel
from datetime import datetime

payment_bp = Blueprint('payment', __name__)
payment_model = PaymentModel()
security_model = SecurityLogModel()

@payment_bp.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        # Condition: User MUST have an account (be logged in)
        if not current_user.is_authenticated:
            # Handle failure due to no account
            # Create a localized payment entry for failed guest attempt (if needed, or just log security)
            # Since PaymentModel expects a structure, we can adapt or just log security event.
            # Using PaymentModel.create for logging failed attempt if desired, but user is anonymous.
            
            security_model.create("Unauthenticated Payment", "محاولة دفع بدون حساب", severity="medium")
            flash('لا يمكن إتمام عملية التحويل إلا لمن لديهم حساب على الموقع. يرجى تسجيل الدخول أولاً.')
            return redirect(url_for('login')) # Assuming 'login' route exists in main app or user controller
            
        try:
            amount = request.form.get('amount')
            method = request.form.get('method')
            transaction_id = request.form.get('transaction_id')
            
            if not amount or float(amount) <= 0:
                raise ValueError("مبلغ غير صحيح")

            # Successfully logged as pending
            payment_model.create({
                'username': current_user.username,
                'full_name': current_user.full_name,
                'amount': amount,
                'method': method,
                'transaction_id': transaction_id,
                'status': 'success (Pending Approval)'
            })
            flash('تم إرسال بيانات الدفع بنجاح، سيتم مراجعتها من قبل الإدارة.')
        except Exception as e:
            # Log failure
            payment_model.create({
                'username': current_user.username,
                'full_name': current_user.full_name,
                'amount': request.form.get('amount', '0'),
                'method': request.form.get('method', 'unknown'),
                'transaction_id': request.form.get('transaction_id', 'N/A'),
                'status': f'failed ({str(e)})'
            })
            flash('فشلت محاولة تسجيل الدفع. تأكد من إدخال البيانات بشكل صحيح.')
            
        return redirect(url_for('web.index')) # Redirect to home
    
    # GET request check
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول للوصول لصفحة الدفع')
        return redirect(url_for('login')) # Assuming login is global or in user_controller
        
    return render_template('payment.html')
