from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_security import login_required, current_user, roles_required, roles_accepted

home = Blueprint('home', __name__,
                 template_folder='templates')
            
@home.route('/')
def index():
    return render_template('home.html', title='Brea Fragances - Home')

@home.route('/products')
@login_required
@roles_accepted('customer', 'admin')
def products():
    return render_template('allProducts.html', title='Products')