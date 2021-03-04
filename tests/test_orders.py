"""
Test cases for Order Model

"""
import logging
import unittest
import os
from werkzeug.exceptions import NotFound
from service.models import Order,Item, DataValidationError, db
from service import app

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
#  P L A C E   T E S T   C A S E S   H E R E 
######################################################################

    def test_init_order(self):
        """ Initialize an order and assert that it exists """
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




######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
