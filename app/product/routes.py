import os
from flask import (render_template, url_for, flash, redirect, 
                    request, Blueprint, current_app)
from flask_security import login_required, current_user, roles_required
from app.product.forms import ProductForm
from app.product.models import Product
from app import product_pics, db

product = Blueprint('product', __name__,
                 template_folder='templates',
                 url_prefix='/admin')

@product.route('/products')
@login_required
@roles_required('admin')
def products():
    products = Product.query.all()
    return render_template('products.html', title='Products', products=products)

@product.route('/add-product', methods=["POST", "GET"])
@login_required
@roles_required('admin')
def add_product():
    form=ProductForm()
    default_image = url_for('static', filename='images/preview.png')
    if form.validate_on_submit():
        if form.image.data:
            product = Product(
                name = form.name.data,
                price = form.price.data
            )
            db.session.add(product)
            db.session.commit()
            image_filename = product_pics.save(form.image.data, name=f'{product.id}.')
            image_url = url_for(
                "_uploads.uploaded_file", 
                setname=product_pics.name, 
                filename=image_filename
            )
            product.image_filename = image_filename
            product.image_url = image_url
            db.session.commit()
            flash('product saved successfully', 'success')
            return redirect(url_for("product.products"))
        else:
            flash('Please select an image', 'danger')
    return render_template('addProduct.html', title='Add Product', form=form, default_image = default_image)

@product.route('/edit-product/<int:product_id>', methods=["POST", "GET"])
@login_required
@roles_required('admin')
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    default_image = product.image_url
    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        if form.image.data:
            previos_image_path = product_pics.path(product.image_filename)
            os.remove(previos_image_path)
            image_filename = product_pics.save(form.image.data, name=f'{product.id}.')
            image_url = url_for(
                "_uploads.uploaded_file", 
                setname=product_pics.name, 
                filename=image_filename
            )
            product.image_filename = image_filename
            product.image_url = image_url
        db.session.commit()
        flash('product saved successfully', 'success')
        return redirect(url_for('product.products'))
    elif request.method == 'GET':
        form.name.data = product.name
        form.price.data = product.price
    return render_template('addProduct.html', title='Edit Product', form=form, default_image = default_image)

@product.route('/delete-product/<int:product_id>', methods=["POST"])
@login_required
@roles_required('admin')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('product.products'))