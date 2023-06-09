import os, json
from flask import (render_template, url_for, flash, redirect, 
                    request, Blueprint, current_app)
from flask_security import login_required, roles_required, roles_accepted, current_user
from sqlalchemy import text
from app.product.forms import ProductForm, MakeForm
from app.product.models import Product, ProductSupplies, ProductInventory
from app.supply.models import Supply, SupplyBuys
from app import product_pics, db
from datetime import date


product = Blueprint('product', __name__,
                 template_folder='templates',
                 url_prefix='/admin')


@product.route('/products')
@login_required
@roles_accepted('admin', 'stocker')
def products():
    products = Product.query.all()
    return render_template('products.html', title='Products', products=products)


@product.route('/add-product', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def add_product():
    form=ProductForm()
    default_image = url_for('static', filename='images/preview.png')
    supplies = db.session.execute(text("CALL get_product_supplies(:id)"), {'id': 0}).mappings().all()
    if form.validate_on_submit():
        try:
            supplies_data = json.loads(form.supplies.data)
            if len(supplies_data) > 0:
                if form.image.data:
                    product = Product(
                        name = form.name.data,
                        description = form.description.data,
                        price = form.price.data
                    )
                    db.session.add(product)
                    db.session.commit()

                    for supply in supplies_data:
                        productSupplies = ProductSupplies(
                            product_id = product.id,
                            supply_id = supply['id'],
                            quantity = supply['amount']
                        )
                        db.session.add(productSupplies)



                    image_filename = product_pics.save(form.image.data, name=f'{product.id}.')
                    image_url = url_for(
                        "_uploads.uploaded_file", 
                        setname=product_pics.name, 
                        filename=image_filename
                    )
                    product.image_filename = image_filename
                    product.image_url = image_url
                    db.session.commit()
                    current_app.logger.critical(f"PRODUCT {product.name} ADDED BY {current_user.email}")
                    flash('Product saved successfully', 'success')
                    return redirect(url_for("product.products"))
                else:
                    flash('Please select an image', 'danger')
            else:
                flash('Please select some suplies', 'danger')
        except:
            flash('Invalid supplies format', 'danger')
    return render_template('addProduct.html', title='Add Product', form=form, default_image = default_image, supplies=supplies)


@product.route('/edit-product/<int:product_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def edit_product(product_id):
    # rewrite query to include amount and checked state in supplies object and
    # add it to the template, so no extra code in needed in the frontend nor
    # backend
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    supplies = db.session.execute(text("CALL get_product_supplies(:id)"), {'id': product.id}).mappings().all()
    default_image = product.image_url
    if form.validate_on_submit():
        try:
            supplies_data = json.loads(form.supplies.data)
            if len(supplies_data) > 0:
                product.name = form.name.data
                product.description = form.description.data
                product.price = form.price.data

                for productSupply in product.productSupplies:
                    db.session.delete(productSupply)


                for supply in supplies_data:
                    productSupplies = ProductSupplies(
                        product_id = product.id,
                        supply_id = supply['id'],
                        quantity = supply['amount']
                    )
                    db.session.add(productSupplies)

                db.session.commit()

                if form.image.data:
                    previos_image_path = product_pics.path(product.image_filename)
                    try:
                        os.remove(previos_image_path)
                    except:
                        pass
                    image_filename = product_pics.save(form.image.data, name=f'{product.id}.')
                    image_url = url_for(
                        "_uploads.uploaded_file", 
                        setname=product_pics.name, 
                        filename=image_filename
                    )
                
                    product.image_filename = image_filename
                    product.image_url = image_url

                db.session.commit()
                current_app.logger.critical(f"PRODUCT {product.name} MODIFIED BY {current_user.email}")
                flash('Product saved successfully', 'success')
                return redirect(url_for('product.products'))
            else:
                flash('Please select some suplies', 'danger')
        except:
            flash('Invalid supplies format', 'danger')
    elif request.method == 'GET':
        form.name.data = product.name
        form.price.data = product.price
        form.description.data = product.description
    return render_template('addProduct.html', title='Edit Product', form=form, default_image = default_image, supplies = supplies)


@product.route('/delete-product/<int:product_id>', methods=["POST"])
@login_required
@roles_accepted('admin', 'stocker')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    previos_image_path = product_pics.path(product.image_filename)
    try:
        os.remove(previos_image_path)
    except:
        pass
    db.session.delete(product)
    db.session.commit()
    current_app.logger.critical(f"PRODUCT {product.name} DELETED BY {current_user.email}")
    flash('Product deleted successfully', 'success')
    return redirect(url_for('product.products'))


@product.route('/products/search', methods=["POST", "GET"])
@login_required
def search():
    word = request.form.get('search')
    search = ''
    products = []
    if(word != None and word != ''):
        search="%{}%".format(word)
        products = Product.query.filter(Product.name.like(search)).all()

    return render_template('search.html', title='Results of "'+search.replace('%', '')+'"', products=products)


@product.route('/product-details/<int:product_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def details(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('productDetails.html', 
                           title='Product Details', 
                           product=product)


@product.route('/product-make/<int:product_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def make(product_id):
    product = Product.query.get_or_404(product_id)
    form = MakeForm()
    if form.validate_on_submit():
        missing = product.can_produce(form.quantity.data)
        if len(missing) == 0:
            inventory = ProductInventory(
                expiration_date = form.expiration_date.data,
                quantity = form.quantity.data,
                available_quantity = form.quantity.data,
                unit_cost = product.production_cost,
                product_id = product_id
            )
            db.session.add(inventory)
            db.session.commit()
            for supply in product.productSupplies:
                spent_quantity = supply.quantity * form.quantity.data
                buys = supply.supply.buys.filter(SupplyBuys.expiration_date > date.today()).order_by(SupplyBuys.expiration_date).all()
                index = 0
                remaining = spent_quantity
                while True:
                    buy = buys[index]
                    difference = buy.available_use_quantity - remaining 
                    if difference >= 0:
                        buy.available_use_quantity = difference
                        db.session.commit()
                        break
                    remaining = abs(difference)
                    difference = 0
                    buy.available_use_quantity = 0
                    db.session.commit()
                    index += 1
            flash('Product made successfully', 'success')
            current_app.logger.critical(f"PRODUCT {product.name} MADE BY {current_user.email}")
            return redirect(url_for('product.details', product_id=product_id))
        else:
            flash('Not enough supplies to produce that amount of product', 'danger')
            return render_template('makeProduct.html', 
                                title='Product Details', 
                                product=product,
                                form = form,
                                missing = missing)
    return render_template('makeProduct.html', 
                        title='Make product', 
                        product=product,
                        form = form,)


@product.route('/product-info/<int:product_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def productInfo(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('singleProduct.html', title='Details', product=product)

@product.route('/product-inventory/<int:product_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def product_inventory(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('productInventory.html', title='Inventory', product=product)

@product.route('/production/<int:product_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def product_production(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('production.html', 
                           title='Production', 
                           product=product,)

