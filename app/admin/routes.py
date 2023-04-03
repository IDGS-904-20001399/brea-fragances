from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_security import login_required, current_user, roles_required
from app.forms import ProductForm

admin = Blueprint('admin', __name__,
                 template_folder='templates',
                 url_prefix='/admin')
            
@admin.route('/all-customers')
# @login_required
# @roles_required('admin')
def customers():
    return render_template('customers.html', title='Customers')

@admin.route('/all-products')
# @login_required
# @roles_required('admin')
def products():
    return render_template('products.html', title='Products')

@admin.route('/add-product', methods=["POST", "GET"])
# @login_required
# @roles_required('admin')
def addProduct():
    form=ProductForm(request.form)

    if request.method == "POST":
        return redirect(url_for("admin.products"))
    
    return render_template('addProduct.html', title='Add Product', form=form)