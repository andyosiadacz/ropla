# ROPLA v1.0 - COPYRIGHT 2022 ANDREW OSIADACZ 

from datetime import date
from forms import *
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import Model
from models import *
from sqlalchemy import create_engine, or_, and_
import pandas as pd


THIS_YEAR = date.today().year


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

# DEFINE FIELDS FOR VIEWABLE TABLES
# TODO: REFACTOR INTO NEW FILE
class Field():
    def __init__(self, name, model, html_form_name="", filterable=True) -> None:
        self.name = name
        self.model: Model = model
        self.html_form_name = html_form_name
        self.query_value = None
        self.filterable = filterable

    def check_query(self):
        """Check if filter form field is blank or None type, appending query 
        value from HTML form to field object if filled"""
        if request.form.get(self.html_form_name) != None and request.form.get(self.html_form_name) != "":
            self.query_value = request.form.get(self.html_form_name)



    def filter(self):
        """Returns SQLAlchemy filter parameter for field query_value, 
        defaulting to open wild card search for blank or None type HTML form inputs"""
        # TODO: Develop wildcard searches

        filter = or_(self.model.like("%%"),self.model==None)
        if self.query_value != None:
            filter = self.model.like(f"%{self.query_value}%")
            if self.query_value.lower() == "none":
                filter = self.model==None

        return filter
    

# FIELD DEFINITIONS
sold_to_number = Field(name= "Sold To No.", model=OrderDetail.sold_to_number, html_form_name="sold_to_no_query")
sold_to = Field(name= "Sold To", model=OrderDetail.sold_to, html_form_name="sold_to_query")
order_number = Field(name= "Order No.", model=OrderDetail.order_number, html_form_name="order_number_query")
item = Field(name= "Item", model=OrderDetail.item, html_form_name="item_query")
stocking_type = Field(name="Stk Type", model=OrderDetail.stocking_type, html_form_name="stocking_type_query")
concatenation_description = Field(name= "Description", model=OrderDetail.concatenation_description, filterable=False)
order_quantity = Field(name= "Order Quantity", model=OrderDetail.quantity_shipped, filterable=False)
hold_code = Field(name= "Hold Code", model=OrderDetail.hold_orders_code, html_form_name="hold_code_query")
ready_date = Field(name="Ready Date", model=OrderDetail.ready_date, filterable=False)

FIELDS = [sold_to_number, sold_to, order_number, item, stocking_type, concatenation_description, order_quantity, hold_code, ready_date]
ROWS_PER_PAGE = 10


@app.route('/reports/buildable', methods=['GET','POST'])
def buildable():
    global THIS_YEAR, ROWS_PER_PAGE
    function_name='buildable'

    # Initalize Pagination Flask Form
    rows_per_page = RowsPerPage()
    if rows_per_page.validate_on_submit():
        ROWS_PER_PAGE = rows_per_page.rows_per_page.data


    page = request.args.get('page', 1, type=int)

    # Check HTML form fields for filter inputs
    for field in FIELDS:
        field.check_query()
    
    #Initialize table and page filters list
    filters = []
    table = OrderDetail.query.filter(OrderDetail.buildable==True)

    # For BUILDABLE, add buildable filter
    filters.append(OrderDetail.buildable==True)

    # Apply filtered fields from HTML form to list of filters
    for field in FIELDS:
        filters.append(field.filter())

    # Apply all current filters to database query
    if filters != []:
        db_query = OrderDetail.query.filter(*filters)
        table = db_query.paginate(page=page, per_page=ROWS_PER_PAGE)

    return render_template('reports.html', 
        function_name=function_name, 
        fields=FIELDS,
        table=table, 
        selector=rows_per_page, 
        year=THIS_YEAR)



@app.route('/reports/oor', methods=['GET','POST'])
def oor():
    global THIS_YEAR, ROWS_PER_PAGE
    function_name='oor'
    
    # Initalize Pagination Flask Form
    rows_per_page = RowsPerPage()
    if rows_per_page.validate_on_submit():
        ROWS_PER_PAGE = rows_per_page.rows_per_page.data

    page = request.args.get('page', 1, type=int)


    # Initalize table with order detail
    table = OrderDetail.query.all()

    # Check HTML form fields for filter inputs
    for field in FIELDS:
        field.check_query()
    
    #Initialize page filters
    filters = []

    # Apply filtered fields to list of filters
    for field in FIELDS:
        filters.append(field.filter())

    # Apply all current filters to database query
    table = OrderDetail.query.filter(*filters).paginate(page=page, per_page=ROWS_PER_PAGE)

    return render_template('reports.html', 
        function_name=function_name, 
        fields=FIELDS,
        filters=filters,
        table=table, 
        selector=rows_per_page,
        year=THIS_YEAR)
    

@app.route('/reports/<function_name>/generate-report', methods=['GET'])
def generate_report(function_name):
    #Initialize page filters
    filters = []
    if function_name == 'buildable':
        filters.append(OrderDetail.buildable==True)
        
    # Apply filtered fields to list of filters
    for field in FIELDS:
        filters.append(field.filter())

    # Take raw SQL query and create Excel file from Pandas data frame object
    query = OrderDetail.query.filter(*filters).statement
    df = pd.read_sql_query(query, db.engine.connect())
    df.to_excel(f'NINER {function_name}.xlsx')

    return send_file(path_or_file=f'NINER {function_name}.xlsx', as_attachment=True, download_name=f'NINER {function_name.upper()} {date.today()}.xlsx')

   

@app.route('/reports/<root>/clear/<clear_field>/')
def clear_query_value(root, clear_field):
    """Clears query value for a particular field and returns to appropriate report page."""
    for field in FIELDS:
        if field.name == clear_field:
            field.query_value = None
    return redirect(f'/reports/{root}')



# RUN APP
if __name__ == "__main__":
    app.run(debug=True)