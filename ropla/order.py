import sqlite3
from datetime import timedelta

class Order:
    """Order class must be initialized with an order number."""

    def __init__(self, order_num: int):
        self.order_num = order_num
        self.sold_to_name = ""
        self.sold_to_num = ""
        self.sold_to_address = {
            "Name": self.sold_to_name,
            "Address Line 1": "",
            "Address Line 2": "",
            "City": "",
            "State": "",
            "Postal Code": "",
            "Country": "",
        }
        self.ship_to_address = {
            "Name": self.sold_to_name,
            "Address Line 1": "",
            "Address Line 2": "",
            "City": "",
            "State": "",
            "Postal Code": "",
            "Country": "",
        }
        self.po_num = None
        self.order_date = ""
        self.build_date = ""
        self.ship_date = ""

        self.orderlines = []
    
    def load_order(self):
        pass

class Item:
    def __init__(self,item_number: str) -> None:
        self.item_number = item_number
        self.item_description = ""
        self.item_coo = ""
        self.item_hts_code = ""
        self.item_price = ""
        self.quantity = ""
        self.net_weight = ""
        self.gross_weight = ""
        self.cbm = ""
        self.purchase_leadtime: timedelta = timedelta(days=105)
        self.queue_position: int = None
        self.consumption_position: int = None
        self.available_quantity: int = None

    def check_inventory(self, conn):

            # FETCH ITEM AVAILABLE QUANTITY FROM DATA BASE, GENERATING NEW DATABASE LINE IF NOT FOUND
        cursor = conn.execute(f'SELECT "Synapse Allocable Quantity" FROM inventory_by_location WHERE ITEM="{self.item_number}"')
        try:
            self.available_quantity = cursor.fetchone()[0]
        except TypeError:
            conn.execute(f'INSERT INTO inventory_by_location (ITEM, "Synapse Allocable Quantity", "quantity consumed") VALUES ("{self.item_number}", 0, 0)')
            conn.commit()
            self.available_quantity = 0

        # FETCH ITEM CONSUMPTION QUANTITY FROM DATA BASE,  GENERATING NEW DATABASE LINE IF NOT FOUND
        cursor = conn.execute(f'SELECT "quantity consumed" FROM "inventory_by_location" WHERE "ITEM"="{self.item_number}"')
        try:
            self.consumption_position = cursor.fetchone()[0]
        except TypeError:
            conn.execute(f'INSERT INTO inventory_by_location (ITEM, "Synapse Allocable Quantity", "quantity consumed") VALUES ("{self.item_number}", 0, 0)')
            conn.commit()
            self.consumption_position = 0
        
        return self.available_quantity - self.consumption_position
            




class ParentItem(Item):
    def __init__(self, item_number: str) -> None:
        super().__init__(item_number)
        self.item_number = item_number
        self.bom = []
        self.buildable: bool = True
        self.ready_time: str = ""
        self.manu_time: int = 0

        self.load_BOM()

    #Load BOM
    def load_BOM(self):
        conn = sqlite3.connect('main.db')
        
        parent_cursor = conn.execute(f'SELECT "Component Item Number","Stocking Type - STKT", "Kit Quantity" FROM bom_master WHERE "Parent Item Number" = "{self.item_number}"')
        
        for line in parent_cursor.fetchall():
            if line[1] == 'S':
                item = Item(line[0])
                self.bom.append({"item": item,
                    'kit quantity': line[2]})
            else:
                kit_cursor = conn.execute(f'SELECT "Component Item Number","Stocking Type - STKT", "Kit Quantity" FROM bom_master WHERE "Parent Item Number" = "{line[0]}"')
                for kit_line in kit_cursor.fetchall():
                    item = Item(kit_line[0])
                    self.bom.append({"item": item,
                        'kit quantity': kit_line[2]})
        conn.close()

