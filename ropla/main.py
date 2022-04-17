import datetime as dt
import pandas as pd
import sqlite3, time
from order import *
import reports


REPORT_TIME = dt.datetime.today()
START_TIME = time.time()

def update_database():
    running  = True

    while running:
        print("\n---- UPDATE DATABASE ----")
        print("What table would you like to update?")
        print("1. Inventory")
        print("2. Bill of Materials")
        print("3. Order Detail")
        print("4. Purchase Order")

        menu_selection = input("Input selection, or press any other key to return to main menu.")

        conn = sqlite3.connect('main.db')

        cursor =  conn.cursor() 

        if menu_selection == "1":
            # ~~~~ LOAD INVENTORY TO DATABASE ~~~~
            # Load the CSV data into a Pandas DataFrame
            inventory_by_location = pd.read_csv('inventory_by_location.csv')

            inventory_by_location.to_sql('inventory_by_location', conn, if_exists='replace', index=False)
            cursor.execute("ALTER TABLE 'inventory_by_location' ADD COLUMN 'quantity consumed' INTEGER default 0")
            print("\n'Inventory' table sucessfully updated.")

        elif menu_selection == "2":
            # ~~~~ LOAD BOM FILE INTO DATABASE ~~~~
            bom_master = pd.read_csv('bom_master.csv')
            bom_master.to_sql('bom_master', conn, if_exists='replace', index=False)
            print("\n'Bill of Materials' table sucessfully updated.")

        elif menu_selection == "3":
            # ~~~~~ LOAD ORDER DATA INTO DATABASE ~~~~
            order_detail = pd.read_csv('practice.csv')
            order_detail.to_sql('order_detail_file', conn, if_exists='replace', index=True)
            cursor.execute('ALTER TABLE order_detail_file ADD COLUMN buildable BOOLEAN')
            cursor.execute('ALTER TABLE order_detail_file ADD COLUMN "Ready Date" TEXT (10)')
            cursor.execute('ALTER TABLE order_detail_file ADD COLUMN "Late Item" TEXT (12)')
            print("\n'Order Detail' table sucessfully updated.")

        elif menu_selection == "4":
            # ~~~~ LOAD PO FILE INTO DATABASE ~~~~~
            po_file = pd.read_csv('po_file.csv')
            po_file.to_sql('po_file', conn, if_exists='replace', index=False)
            print("\n'PO File' table sucessfully updated.")

        else:
            running = False

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
    # cursor = conn.execute(f'SELECT "Parent Item Number" FROM bom_master WHERE "Parent Item Number" = "{parent_item.item_number}"')
    # if cursor.fetchone() != None:
    # CHECK IF PARENT IS BUILDABLE
    if parent_item.bom != []:
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
                    parent_item.late_item = item_no
                    
    
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

    x = 0
    z = 0.00
    for order_line in orders:
        index = order_line[0]

        parent_item = ParentItem(order_line[1])
        parent_item.quantity = order_line[2]
        parent_item.stocking_type = order_line[3]
        parent_item.ready_time = calculate_leadtime(parent_item)
        updates.append((index, parent_item.ready_time, parent_item.buildable, parent_item.late_item))
        record_number += 1
        if record_number / records > z:
            y = 20 - x
            a = "#" * x + " " * y 
            print("Processing records 0%|"+ a + "|100%", end="\r")
            x += 1
            z += 0.05

    # ---- UPDATE ORDER DETAIL FILE WITH BUILDABLE AND READY DATE
    conn = sqlite3.connect('main.db')
    print("\nUpdating records...")
    for update in updates:
        index = update[0]
        ready_time = update[1]

        conn.execute(f'UPDATE order_detail_file set buildable = {update[2]} WHERE "index" = {index}')
        conn.execute(f'UPDATE order_detail_file set "Ready Date" = "{ready_time}" WHERE "index" = {index}')
        conn.execute(f'UPDATE order_detail_file set "Late Item" = "{update[3]}" WHERE "index" = {index}')

    conn.commit()
    conn.close()
    print("Update Successful.")
    END_TIME = time.time()

    print(f"Process Time: {str(END_TIME - START_TIME)[:5]} seconds")


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
    print("\n---- MAIN MENU ----")
    print("1. Update Order Availability (~1.5-2 minute runtime)")
    print("2. Generate Open Order Report")
    print("3. Generate What Can I Build Today Report")
    print("4. Update database.")
    print("Pick from a selection above, or press any other key to exit.")
    menu_selection = input("What can I help you with? ")
    print("\n")

    if menu_selection == "1":
        update_order_leadtimes()
    
    elif menu_selection == "2":
        reports.generate_OOR()

    elif menu_selection == "3":
        reports.generate_build_today()

    elif menu_selection == "4":
        update_database()

    else:
        running = False
        print("Goodbye!")
