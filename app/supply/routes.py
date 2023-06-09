import os
from flask import (render_template, url_for, flash, redirect, 
                    request, Blueprint, current_app)
from flask_security import login_required, roles_required, roles_accepted, current_user
from app.supply.forms import SupplyForm, BuySupplyForm
from app.supply.models import Supply, SupplyBuys
from app import supply_pics, db
from datetime import date

supply = Blueprint('supply', __name__,
                 template_folder='templates',
                 url_prefix='/admin')

@supply.route('/supplies')
@login_required
@roles_accepted('admin', 'stocker')
def supplies():
    supplies = Supply.query.all()
    return render_template('supplies.html', title='Supplies', supplies=supplies)


@supply.route('/buy-supply/<int:supply_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def buy_supply(supply_id):
    form = BuySupplyForm()
    supply = Supply.query.get_or_404(supply_id)
    if form.validate_on_submit():
        available_use_quantity = form.quantity.data * supply.equivalence
        buy = SupplyBuys(expiration_date=form.expiration_date.data,
                         quantity=form.quantity.data,
                         available_use_quantity=available_use_quantity,
                         unit_cost=supply.cost,
                         supply_id=supply_id)
        db.session.add(buy)
        db.session.commit()
        current_app.logger.critical(f"SUPPLY {supply.name} BOUGHT BY {current_user.email}")
        flash('Supply bought successfully', 'success')
        return redirect(url_for("supply.details", supply_id=supply_id))

    return render_template('buySupply.html',
                           title='Buy supply',
                           form=form)

@supply.route('/supply-details/<int:supply_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def details(supply_id):
    supply = Supply.query.get_or_404(supply_id)
    return render_template('supplyDetails.html', 
                           title='Supply Details', 
                           supply=supply,)


@supply.route('/add-supply', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def add_supply():
    form=SupplyForm()
    default_image = url_for('static', filename='images/preview.png')
    if form.validate_on_submit():
        if form.image.data:
            supply = Supply(
                name = form.name.data,
                cost = form.cost.data,
                buy_unit = form.buy_unit.data,
                use_unit = form.use_unit.data,
                equivalence = form.equivalence.data
            )
            db.session.add(supply)
            db.session.commit()
            image_filename = supply_pics.save(form.image.data, name=f'{supply.id}.')
            image_url = url_for(
                "_uploads.uploaded_file", 
                setname=supply_pics.name, 
                filename=image_filename
            )
            supply.image_filename = image_filename
            supply.image_url = image_url
            db.session.commit()
            flash('Supply saved successfully', 'success')
            current_app.logger.critical(f"SUPPLY {supply.name} ADDED BY {current_user.email}")
            return redirect(url_for("supply.supplies"))
        else:
            flash('Please select an image', 'danger')
    return render_template('addSupply.html', title='Add Supply', form=form, default_image = default_image)


@supply.route('/edit-supply/<int:supply_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def edit_supply(supply_id):
    supply = Supply.query.get_or_404(supply_id)
    form = SupplyForm()
    default_image = supply.image_url
    if form.validate_on_submit():
        supply.name = form.name.data
        supply.cost = form.cost.data
        supply.buy_unit = form.buy_unit.data
        supply.use_unit = form.use_unit.data
        supply.equivalence = form.equivalence.data
        if form.image.data:
            previos_image_path = supply_pics.path(supply.image_filename)
            try:
                os.remove(previos_image_path)
            except:
                pass
            image_filename = supply_pics.save(form.image.data, name=f'{supply.id}.')
            image_url = url_for(
                "_uploads.uploaded_file", 
                setname=supply_pics.name, 
                filename=image_filename
            )
            supply.image_filename = image_filename
            supply.image_url = image_url
        db.session.commit()
        current_app.logger.critical(f"SUPPLY {supply.name} MODIFY BY {current_user.email}")
        flash('Supply saved successfully', 'success')
        return redirect(url_for('supply.supplies'))
    elif request.method == 'GET':
        form.name.data = supply.name
        form.cost.data = supply.cost
        form.buy_unit.data = supply.buy_unit
        form.use_unit.data = supply.use_unit
        form.equivalence.data = supply.equivalence
    return render_template('addSupply.html', title='Edit supply', form=form, default_image = default_image)


@supply.route('/delete-supply/<int:supply_id>', methods=["POST"])
@login_required
@roles_accepted('admin', 'stocker')
def delete_supply(supply_id):
    supply = Supply.query.get_or_404(supply_id)
    previos_image_path = supply_pics.path(supply.image_filename)
    try:
        os.remove(previos_image_path)
    except:
        pass
    db.session.delete(supply)
    db.session.commit()
    current_app.logger.critical(f"SUPPLY {supply.name} DELETED BY {current_user.email}")
    flash('Supply deleted successfully', 'success')
    return redirect(url_for('supply.supplies'))

@supply.route('/supply-inventory/<int:supply_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def inventory(supply_id):
    supply = Supply.query.get_or_404(supply_id)
    return render_template('inventory.html', 
                           title='Inventory', 
                           supply=supply,)

@supply.route('/buys/<int:supply_id>', methods=["POST", "GET"])
@login_required
@roles_accepted('admin', 'stocker')
def buys(supply_id):
    supply = Supply.query.get_or_404(supply_id)
    return render_template('buys.html', 
                           title='Buys', 
                           supply=supply,)