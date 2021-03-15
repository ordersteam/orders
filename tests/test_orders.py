"""
Test cases for Order Model

"""
import logging
import unittest
import os
from werkzeug.exceptions import NotFound
from service.models import Order,Item, DataValidationError, db
from service import app 
from datetime import datetime

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)

######################################################################
#  Order   M O D E L   T E S T   C A S E S
######################################################################
class TestOrderModel(unittest.TestCase):
    """ Test Cases for Order Model """

    @classmethod
    def setUpClass(cls):
        """ Run once before all tests """
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Order.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """ This runs once after the entire test suite """
        pass

    def setUp(self):
        """ Runs before each test """
        db.drop_all()  # clean up the last tests
        db.create_all()  # create new tables
        self.app = app.test_client()

    def tearDown(self):
        """ This runs after each test """
        db.session.remove()
        db.drop_all()

######################################################################
#  P L A C E  ORDER RELATED T E S T   C A S E S   H E R E 
######################################################################
    
    def test_init_order(self):
        """ Initialize an order and  check if it exists """
        order_items = [Item(product_id=6, quantity=4, price=10)]
        order = Order(customer_id=1, order_items=order_items)
        self.assertTrue(order is not None)
        self.assertEqual(order.id, None)
        self.assertEqual(order.customer_id, 1)
        self.assertEqual(len(order.order_items), 1)

    def test_create_order(self):
        """ Create an order with a single item in the database to test """
        order_item = Item(product_id=2, quantity=3, price=3)
        order_items = [order_item]
        order = Order(customer_id=34, order_items=order_items)
        self.assertTrue(order is not None)
        self.assertEqual(order.id, None)
        self.assertEqual(len(order.order_items), 1)
        self.assertEqual(order.order_items[0].item_id, None)
        order.create()
        self.assertEqual(order.id, 1)
        self.assertEqual(order.customer_id, 34)
        self.assertEqual(len(order.order_items), 1)
        self.assertEqual(order.order_items[0].item_id, 1)
        self.assertEqual(order.order_items[0].order_id, 1)

    def test_update_an_order(self):
        """ Update an existing Order """
        order_item1 = Item(product_id=3, quantity=2, price=5)
        order_items = [order_item1]
        order = Order(customer_id=123, order_items=order_items)
        order.create()
        self.assertTrue(order.id is not None)
        #change order and update
        order_item2 = Item(product_id=7, quantity=1, price=3)
        order.order_items.append(order_item2)
        order.update()
        self.assertEqual(order.id, 1)
        self.assertEqual(len(order.order_items), 2)
        #make sure ID didn't change but data did
        orders = Order.all()
        order = orders[0]
        self.assertEqual(len(orders), 1)
        self.assertEqual(order.id, 1)
        self.assertEqual(len(order.order_items), 2)

    def test_update_an_order_not_exists(self):
        """ Update a non-existing Order """
        order_item1 = Item(product_id=3, quantity=2, price=5)
        order_items = [order_item1]
        order = Order(id=1234567, customer_id=123, order_items=order_items)
        order.update()
        self.assertRaises(DataValidationError)

    def test_update_order_with_no_id(self):
        """ Update an order with no id """
        order_item = Item(product_id=3, quantity=2, price=5)
        order_items = [order_item]
        order = Order(customer_id=123, order_items=order_items)
        self.assertRaises(DataValidationError, order.update)

    def test_update_order_with_no_customer_id(self):
        """ Update an order with no customer id """
        order_item = Item(product_id=3, quantity=2, price=5)
        order_items = [order_item]
        order = Order(id=1, order_items=order_items)
        self.assertRaises(DataValidationError, order.update)

    def test_update_order_with_no_order_items(self):
        """ Update an order with no order items"""
        order = Order(id=1, customer_id=123)
        self.assertRaises(DataValidationError, order.update)

    #def test_update_order_with_wrong_id(self):
     #   """ Update an order with the wrong order id"""
      #  order_item = Item(product_id=3, quantity=2, price=5)
       # order_items = [order_item]
       # order = Order(id=42, customer_id=123, order_items=order_items)
       # self.assertRaises(DataValidationError, order.update)


    def test_repr(self):
        """ Create an order and check its representation """
        order = Order(id=42, customer_id=1)
        self.assertEqual(order.__repr__(), "<Order 42>")

    def test_repr_with_no_item_id(self):
        """ Create an order and test it's repr with no item id """
        order = Order(customer_id=123)
        self.assertEqual(order.__repr__(), "<Order None>")    

    def test_create_order_with_no_cust_id(self):
        """ Create an order with no customer id """
        order_item = Item(product_id=10, quantity=10, price=5)
        order_items = [order_item]
        order = Order(order_items=order_items)
        self.assertRaises(DataValidationError, order.create)
    
    def test_create_order_with_no_item(self):
        """ Create an order with no items in the database """
        order_items = []
        order = Order(customer_id=1, order_items=order_items)
        self.assertRaises(DataValidationError, order.create)

    
    def test_serialize_an_order(self):
        """ Serialization of an Order """
        date = datetime.now
        order_item = Item(product_id=1, quantity=1, price=5)
        order_items =[order_item]
        order = Order(customer_id=12, creation_date=date, order_items=order_items)
        data = order.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], None)
        self.assertIn("customer_id", data)
        self.assertEqual(data["customer_id"], 12)
        self.assertIn("creation_date", data)
        self.assertEqual(data["creation_date"], date)
        self.assertIn("order_items", data)
        self.assertEqual(data["order_items"], [order_item.serialize()])
    

    def test_deserialize_bad_data_with_keys_missing(self):
        """ Deserialization of bad order data with few keys missing """
        data = {"order_items": [{
            "product_id": 10,
            "quantity": 16,
            "price": 50
        }]}
        order = Order()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_order_data(self):
        """ Deserialization of bad data in Order """
        data = "this is not a dictionary"
        order = Order()
        self.assertRaises(DataValidationError, order.deserialize, data)
    
    
    def test_delete_an_order(self):
        """ Delete two Orders """
        item1 = Item(product_id=1, quantity=1, price=5.0)
        item2 = Item(product_id=2, quantity=3, price=5.0)
        order1 = Order(customer_id=121, order_items= [item1])
        order2 = Order(customer_id=111, order_items= [item2])
        order1.create()
        order2.create()
        self.assertEqual(len(Order.all()), 2)
        # delete the order and make sure it isn't in the database
        order1.delete()
        self.assertEqual(len(Order.all()), 1)
        order2.delete()
        self.assertEqual(len(Order.all()), 0)

######################################################################
#   PLACE ITEM RELATED TEST CASES HERE 
######################################################################
    def test_repr(self):
            """ Create an Item and test it's repr """
            order_item = Item(item_id=10, product_id=2, quantity=1,
                                price=15, order_id=7)
            self.assertEqual(order_item.__repr__(), "<Item 10>")

    def test_init_item(self):
        """ Create an order item and assert that it exists """
        order_item = Item(product_id=1, quantity=2, price=10, order_id=19)
        self.assertTrue(order_item is not None)
        self.assertEqual(order_item.item_id, None)
        self.assertEqual(order_item.product_id, 1)
        self.assertEqual(order_item.price, 10)
        self.assertEqual(order_item.order_id, 19)

    def test_deserialize_bad_data_with_wrong_product_id(self):
        """ Deserialization of bad order item data with product_id None """
        data = {"product_id": None, "quantity": 3, "price": 10}
        order = Item()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_data_with_wrong_quantity(self):
        """ Deserialization of bad order item data with quantity not right """
        data = {"product_id": 18, "quantity": "3", "price": 10}
        order = Item()
        self.assertRaises(DataValidationError, order.deserialize, data)
        
    def test_deserialize_bad_data_with_wrong_price(self):
        """ Deserialization of bad order item data with price not given right """
        data = {"product_id": 18, "quantity": 3, "price": "10"}
        order = Item()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_item_data(self):
        """ Deserialization of bad item data """
        data = "this is not a dictionary"
        order = Item()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_data_with_item_id_missing(self):
        """ Deserialization of bad order item data with few keys missing """
        data = {"product_id": 1}
        order = Item()
        self.assertRaises(DataValidationError, order.deserialize, data)

######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
