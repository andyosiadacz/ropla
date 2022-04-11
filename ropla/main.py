from cgi import print_form
import datetime as dt
import pandas as pd
from order import *
import sqlite3, time


REPORT_TIME = dt.datetime.today()
START_TIME = time.time()

def update_database():
    conn = sqlite3.connect('main.db')

    cursor =  conn.cursor()

    # ~~~~ LOAD INVENTORY TO DATABASE ~~~~
    # Load the CSV data into a Pandas DataFrame
    inventory_by_location = pd.read_csv('inventory_by_location.csv')

    # Write the data to a sqlite table
    inventory_by_location.to_sql('inventory_by_location', conn, if_exists='replace', index=False)
    cursor.execute("ALTER TABLE 'inventory_by_location' ADD COLUMN 'quantity consumed' INTEGER default 0")

    # ~~~~ LOAD BOM FILE INTO DATABASE ~~~~
    bom_master = pd.read_csv('bom_master.csv')
    bom_master.to_sql('bom_master', conn, if_exists='replace', index=False)

    # ~~~~~ LOAD ORDER DATA INTO DATABASE ~~~~
    order_detail = pd.read_csv('practice.csv')
    order_detail.to_sql('order_detail_file', conn, if_exists='replace', index=True)
    cursor.execute('ALTER TABLE order_detail_file ADD COLUMN buildable BOOLEAN')
    cursor.execute('ALTER TABLE order_detail_file ADD COLUMN "Ready_Date" TEXT (10)')

    # ~~~~ LOAD PO FILE INTO DATABASE ~~~~~
    po_file = pd.read_csv('po_file.csv')
    po_file.to_sql('po_file', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()



# For item in bom, calc availability based on queue position, quantity available, then purchase_lead_time, then_manufacturing_time
def calculate_leadtime(parent_item: ParentItem):
    global REPORT_TIME

    parent_leadtime = REPORT_TIME
    dt_item_leadtime = REPORT_TIME

    item_leadtime = 0



    conn = sqlite3.connect('main.db')

    # CHECK IF PARENT HAS BOM ENTRY, ELSE CHECK INVENTORY FOR PARENT
    #TODO: INCLUDE STOCKING TYPE OF PARENT AND FLAG UPDATE FOR OUTDATED KITS
    cursor = conn.execute(f'SELECT "Parent Item Number" FROM bom_master WHERE "Parent Item Number" = "{parent_item.item_number}"')
    if cursor.fetchone() != None:
    # CHECK IF PARENT IS BUILDABLE
        for item in parent_item.bom:
            item_no = item['item'].item_number
            item['kit quantity'] *= parent_item.quantity

            # CHECK IF ENOUGH QUANTITY AVAILABLE, ELSE IF SHORT ITEM, SET BUILDABILITY FLAG AND READ PO FILE TO FIND DELIVERY DATE
            if item['item'].check_inventory(conn) - item['kit quantity'] < 0:
                parent_item.buildable = False

                total_on_order = 0

                # LOOP THROUGH OPEN ITEM PO's TO FIND AVAILABLE PO DATE
                cursor = conn.execute(f'SELECT "Quantity Open", "Promised Delivery Date" FROM "po_file" WHERE "2nd Item Number"="{item_no}"')
                for line in cursor.fetchall():
                    total_on_order += line[0]
                    if total_on_order > item['item'].consumption_position:
                        item_leadtime = line[1]
                        item_leadtime = item_leadtime.split("/")
                        # dt_item_leadtime = dt.datetime.strptime(item_leadtime, "%x")
                        dt_item_leadtime = dt.datetime(int(item_leadtime[2]),int(item_leadtime[0]),int(item_leadtime[1]))
                        break
       
                
                # CHECK FOR LATE PO DATES, DEFAULTING TO ITEM MASTER PURCHASE LEADTIME IF PO IS LATE
                # TODO = READ DATA BASE (ITEM MASTER) FOR PURCHASE LEAD TIMES EACH TYPE OF COMPONENT
                if dt_item_leadtime <= REPORT_TIME:
                    dt_item_leadtime = REPORT_TIME + item['item'].purchase_leadtime

                # SET PARENT LEADTIME TO MAXIMUM ITEM LEADTIME
                if dt_item_leadtime > parent_leadtime:
                    parent_leadtime = dt_item_leadtime
    
    else:            
        if parent_item.check_inventory(conn) - parent_item.quantity < 0 and parent_item.stocking_type == "S":
            parent_item.buildable = False
            parent_leadtime = REPORT_TIME + parent_item.purchase_leadtime
        elif parent_item.stocking_type == "K":
            parent_item.buildable = False
            conn.close()
            return "OBSOLETE KIT"

    if parent_leadtime < REPORT_TIME:
        parent_leadtime = "TBD"
    else:
        parent_leadtime = parent_leadtime.strftime("%x")




    #IF ITEM IS BUILDABLE, UPDATE CONSUMPTION
    if parent_item.buildable:
        for item in parent_item.bom:
            item_no = item['item'].item_number

            cursor = conn.execute(f'SELECT "quantity consumed" FROM "inventory_by_location" WHERE "item"="{item_no}"')
            try:
                item['item'].consumption_position = cursor.fetchone()[0] + item['kit quantity']
                conn.execute(f'UPDATE inventory_by_location set "quantity consumed" = "{item["item"].consumption_position}" WHERE item = "{item_no}"')
            except TypeError:
                conn.execute(f'INSERT INTO inventory_by_location (ITEM, "Synapse Allocable Quantity", "quantity consumed") VALUES ("{item_no}", 0, 0)')
                item['item'].consumption_position = cursor.fetchone()[0] + item['kit quantity']
                conn.execute(f'UPDATE inventory_by_location set "quantity consumed" = "{item["item"].consumption_position}" WHERE item = "{item_no}"')

    conn.commit()
    conn.close()

    return parent_leadtime

def update_order_leadtimes():
    



    conn = sqlite3.connect('main.db')
    cursor = conn.execute(f'SELECT "index", "2nd Item Number", "Quantity Shipped", "Stocking Type - STKT" FROM order_detail_file')



    orders = cursor.fetchall()
    
    conn.close()

    records = len(orders)
    record_number = 1

    updates = []


    for order_line in orders:
        index = order_line[0]
        parent_item = ParentItem(order_line[1])
        parent_item.quantity = order_line[2]
        parent_item.stocking_type = order_line[3]
        parent_item.ready_time = calculate_leadtime(parent_item)
        updates.append((index, parent_item.ready_time, parent_item.buildable))
        record_number += 1
        if record_number % 500 == 0:
            print(f"{record_number / records*100}% complete.")

    # ---- UPDATE ORDER DETAIL FILE WITH BUILDABLE AND READY DATE
    conn = sqlite3.connect('main.db')
    print("Updating records...")
    for update in updates:
        index = update[0]
        ready_time = update[1]

        if update[2]:
            conn.execute(f'UPDATE order_detail_file set buildable = TRUE WHERE "index" = {index}')
        else:
            conn.execute(f'UPDATE order_detail_file set buildable = FALSE WHERE "index" = {index}')

        conn.execute(f'UPDATE order_detail_file set "Ready_Date" = "{ready_time}" WHERE "index" = {index}')    
    conn.commit()
    conn.close()
    print("Update Successful.")
    END_TIME = time.time()

    print(f"Process Time: {str(END_TIME - START_TIME)[:5]} seconds")



def generate_OOR():

    conn = sqlite3.connect('main.db')

    df = pd.read_sql('SELECT * FROM order_detail_file', conn)

    conn.close()

    report_generated = False

    while not report_generated:
        try:
            df.to_excel(f'NINER OOR {REPORT_TIME.date()}.xlsx', index=False)
            print(f"NINER OOR {REPORT_TIME.date()}.xlsx succesfully generated.")
            report_generated = True
        except PermissionError:
            abort = input(f"Permission error. Please close NINER OOR {REPORT_TIME.date()}.xlsx and hit enter. Input 'x' to abort.").lower()
            if abort == "x":
                report_generated = True
                print("Report generation aborted.")


def generate_build_today():

    conn = sqlite3.connect('main.db')

    df = pd.read_sql('SELECT * FROM order_detail_file WHERE buildable = TRUE', conn)

    conn.close()

    report_generated = False

    while not report_generated:
        try:
            df.to_excel(f'NINER BUILDABLE {REPORT_TIME.date()}.xlsx', index=False)
            print(f"NINER BUILDABLE {REPORT_TIME.date()}.xlsx succesfully generated.")
            report_generated = True
        except PermissionError:
            abort = input(f"Permission error. Please close NINER BUILDABLE {REPORT_TIME.date()}.xlsx and hit enter. Input 'x' to abort.").lower()
            if abort == "x":
                report_generated = True
                print("Report generation aborted.")




# ~~~~ FUNCTION CALLS ~~~~
running = True

logo = """
  _____             _          
 |  __ \           | |       
 | |__) |___  _ __ | | __ _ 
 |  _  // _ \| '_ \| |/ _` |
 | | \ \ (_) | |_) | | (_| |
 |_|  \_\___/| .__/|_|\__,_| 
             | |                        
             |_|                        
Version 1.0
Copyright 2022 Andy Osiadacz 
"""

print(logo)

while running:
    print("\n---- MENU ----")
    print("1. Update Order Availability")
    print("2. Generate Open Order Report")
    print("3. Generate What Can I Build Today Report")
    print("4. Update database.")
    print("Pick from a selection abotve, or enter Q to quit.")
    menu_selection = input("What can I help you with? ")

    if menu_selection == "1":
        update_order_leadtimes()
    
    elif menu_selection == "2":
        generate_OOR()

    elif menu_selection == "3":
        generate_build_today()

    elif menu_selection == "4":
        update_database()

    else:
        running = False
        print("Goodbye!")


