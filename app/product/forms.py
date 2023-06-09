from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, FloatField, IntegerField, DateField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed
from app import product_pics

class ProductForm(FlaskForm):
    name=StringField('Name', [DataRequired(message='Must not be empty')])
    description=StringField('Description', [DataRequired(message='Must not be empty')])
    price=FloatField('Price', [NumberRange(min=0.1, message='The value must be greater than 0.1')])
    supplies=StringField('supplies')
    image=FileField(validators=[FileAllowed(product_pics, 'Image only')])
    save = SubmitField('Save product')

class MakeForm(FlaskForm):
    expiration_date = DateField('Expiration date', [DataRequired('Must not be empty')])
    quantity = IntegerField('Quantity', [DataRequired('Must not be empty'),
                                         NumberRange(min=1, message='The value must be greater than 1.')])
    submit = SubmitField('Make product')