
from datetime import date
from operator import and_
from flask import Flask, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from models import *
import sqlite3
from sqlalchemy import create_engine, or_, and_
import pandas as pd
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email


THIS_YEAR = date.today().year
USER_FIRST_NAME = "Ninerd"

class AuthForm(FlaskForm):
    username = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label="Log In")

class RowsPerPage(FlaskForm):
    rows_per_page = SelectField(u'Rows Per Page', choices=[(10, '10'), (25, '25'), (50, '50')], coerce=int)
    submit = SubmitField(label="Update")

class Query(FlaskForm):
    query = StringField()

def create_app():
    app = Flask(__name__)
    app.secret_key = "any-string-you-want-just-keep-it-secret"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ropla.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    Bootstrap(app)

    login_manager = LoginManager()
    login_manager.login_view = '/login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app


app = create_app()


@app.route('/')
@login_required
def index():
    global THIS_YEAR
    return render_template('index.html', year=THIS_YEAR, Username=current_user.preferred_name)

@app.route('/login', methods=["GET", "POST"])
def login():
    global THIS_YEAR
    validation_form = AuthForm()
    if validation_form.validate_on_submit():

        user = User.query.filter_by(email=validation_form.username.data).first()
        # VERIFY FORM INPUT WITH USERS DATABASE
        if not user or user.password != validation_form.password.data:
        # TODO: CACHE LOG IN STATUS
            return render_template('login.html', form=validation_form, year=THIS_YEAR, login_incorrect="block")
        else:
            login_user(user, remember=True)
            return redirect('/')
    return render_template('login.html', form=validation_form, year=THIS_YEAR, login_incorrect="none")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/reports/buildable', methods=['GET','POST'])
def buildable():
    global THIS_YEAR
    function_name='buildable'

    rows_per_page = RowsPerPage()
    if rows_per_page.validate_on_submit():
        ROWS_PER_PAGE = rows_per_page.rows_per_page.data
    else:
        ROWS_PER_PAGE = 10
    page = request.args.get('page', 1, type=int)


    sold_to_param = request.form.get('sold_to_query')
    order_number_param = request.form.get('order_number_query')

    params=[sold_to_param, order_number_param]
    

    if sold_to_param != None or order_number_param != None:
        table = OrderDetail.query.filter(and_(or_
            (OrderDetail.sold_to_number==sold_to_param,
            OrderDetail.order_number==order_number_param),
            OrderDetail.buildable==True) 
            ).paginate(page=page, per_page=ROWS_PER_PAGE)
    else:
        table = OrderDetail.query.filter( OrderDetail.buildable==True).paginate(page=page, per_page=ROWS_PER_PAGE)

    return render_template('reports.html', 
    function_name=function_name, 
    params=params,
    table=table, 
    selector=rows_per_page, 
    sold_to_param=sold_to_param, 
    year=THIS_YEAR)

@app.route('/reports/oor', methods=['GET','POST'])
def oor():
    global THIS_YEAR
    function_name='oor'


    rows_per_page = RowsPerPage()
    if rows_per_page.validate_on_submit():
        ROWS_PER_PAGE = rows_per_page.rows_per_page.data
    else:
        ROWS_PER_PAGE = 10

    page = request.args.get('page', 1, type=int)
    filter_param=request.form.get('query2')
    print(filter_param)
    if filter_param == None or filter_param == "":
        table = OrderDetail.query.paginate(page=page, per_page=ROWS_PER_PAGE)
    else:
        table = OrderDetail.query.filter_by(order_number=filter_param).paginate(page=page, per_page=ROWS_PER_PAGE)

    return render_template('reports.html', function_name=function_name, table=table, selector=rows_per_page, param2=filter_param, year=THIS_YEAR)

@app.route('/signup')
def signup():
    pass

if __name__ == "__main__":
    app.run(debug=True)