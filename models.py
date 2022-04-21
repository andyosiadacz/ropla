from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

# def create_db(app):    
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ropla.db'
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
    

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(25), unique=False, nullable=False)
    role = db.Column(db.String(20), unique=False, nullable=False)
    last_name = db.Column(db.String(30), unique=False, nullable=False)
    preferred_name = db.Column(db.String(30), unique=False, nullable=False) 
    first_name = db.Column(db.String(30), unique=False, nullable=False) 
    

class BillOfMaterials(db.Model):
    parent_item_description = db.Column(db.String(60), unique=False, nullable=False)
    parent_item_number = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    component_item_description = db.Column(db.String(60), unique=False, nullable=False)
    component_item_number = db.Column(db.Integer, unique=False, nullable=False)
    stocking_type = db.Column(db.Integer, unique=False, nullable=False)
    kit_quantity = db.Column(db.Integer, unique=False, nullable=False)

class Inventory(db.Model):
    item = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    concatenation_description = db.Column(db.String(60), unique=False, nullable=False)
    synapse_quantity_allocable = db.Column(db.Integer, unique=False, nullable=False)
    e1_quantity = db.Column(db.Integer, unique=False, nullable=False)
    status = db.Column(db.String(10), unique=True, nullable=False)
    e1_quantity_hard_commit = db.Column(db.Integer, unique=False, nullable=False) 
    e1_quantity_soft_commit = db.Column(db.Integer, unique=False, nullable=False)
    synapse_quantity = db.Column(db.Integer, unique=False, nullable=False)  
    synapse_quantity_tasked = db.Column(db.Integer, unique=False, nullable=False)
    quantity_consumed = db.Column(db.Integer, unique=False, nullable=False)

class OrderDetail(db.Model):
    sold_to_number = db.Column(db.Integer, unique=False, nullable=False)
    sold_to = db.Column(db.String(60), unique=False, nullable=False)
    Order_Date = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    order_number = db.Column(db.Integer, unique=False, nullable=False)
    Line_Number = db.Column(db.Float, unique=False, nullable=False)
    item = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    stocking_type = db.Column(db.String(10), unique=True, nullable=False)
    concatenation_description = db.Column(db.String(60), unique=False, nullable=False)
    Customer_PO = db.Column(db.String(60), unique=False, nullable=False)
    Unit_Price = db.Column(db.Float, unique=False, nullable=False)
    quantity_shipped = db.Column(db.Integer, unique=False, nullable=False)
    Extended_Price = db.Column(db.Float, unique=False, nullable=False)
    Ship_To_Number = db.Column(db.Integer, unique=False, nullable=False)
    Address_Line_1 = db.Column(db.String(60), unique=False, nullable=False)
    Address_Line_2 = db.Column(db.String(60), unique=False, nullable=False)
    Address_Line_3 = db.Column(db.String(60), unique=False, nullable=False)
    Address_Line_4 = db.Column(db.String(60), unique=False, nullable=False)
    Postal_Code = db.Column(db.String(10), unique=True, nullable=False)
    City = db.Column(db.String(60), unique=False, nullable=False)
    ST = db.Column(db.String(10), unique=True, nullable=False)
    Ctry = db.Column(db.String(10), unique=True, nullable=False)
    hold_orders_code= db.Column(db.String(2), unique=True, nullable=False)
    buildable = db.Column(db.Boolean, unique=True, nullable=False)
    ready_date = db.Column(db.String(20), unique=True, nullable=False)
    late_item = db.Column(db.String(20), unique=True, nullable=False)

class PurchaseOrder(db.Model):
    Year_Payment_Due_Date = db.Column(db.Integer, unique=False, nullable=False)
    Month_Description_Payment_Due_Date = db.Column(db.String(20), unique=True, nullable=False)
    Supplier = db.Column(db.String(60), unique=False, nullable=False)
    Order_Number = db.Column(db.Integer, unique=False, nullable=False)
    Branch_Plant = db.Column(db.Integer, unique=False, nullable=False)
    Order_Co = db.Column(db.Integer, unique=False, nullable=False)
    Supplier_Number = db.Column(db.Integer, unique=False, nullable=False)
    Or_Ty= db.Column(db.String(10), unique=True, nullable=False)
    Line_Number = db.Column(db.Integer, unique=False, nullable=False)
    Supplier_SO = db.Column(db.Integer, unique=False, nullable=False)
    item = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    Concatenation_Description = db.Column(db.String(60), unique=False, nullable=False)
    Order_Quantity = db.Column(db.Integer, unique=False, nullable=False)
    Quantity_Open = db.Column(db.Integer, unique=False, nullable=False)
    Prev_Qty_Vouchered = db.Column(db.Integer, unique=False, nullable=False)
    Unit_Cost = db.Column(db.Float, unique=True, nullable=False)
    Extended_Cost = db.Column(db.Float, unique=True, nullable=False)
    Amount_Open = db.Column(db.Integer, unique=False, nullable=False)
    Amount_Received = db.Column(db.Integer, unique=False, nullable=False)
    Last_Stat = db.Column(db.Integer, unique=False, nullable=False)
    Next_Stat = db.Column(db.Integer, unique=False, nullable=False)
    Order_Date = db.Column(db.String(20), unique=True, nullable=False)
    Promised_Delivery_Date = db.Column(db.String(10), unique=True, nullable=False)
    Receipt_Date = db.Column(db.String(10), unique=True, nullable=False)
    Pymt_Terms= db.Column(db.Integer, unique=False, nullable=False)
    Payment_Terms = db.Column(db.String(60), unique=False, nullable=False)
    Payment_Due_Date = db.Column(db.String(20), unique=True, nullable=False)