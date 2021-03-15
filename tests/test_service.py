"""
Order API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch
from flask_api import status  # HTTP Status Codes
from urllib.parse import quote_plus
from service.models import db
from service.routes import app, init_db
from .order_factory import OrderFactory, ItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)


def _get_order_factory_with_items(count):
    items = []
    for _ in range(count):
        items.append(   ItemFactory())
    return OrderFactory(items=items)

######################################################################
#  T E S T   C A S E S
######################################################################
class TestOrderService(TestCase):
    """ REST API Server Tests for Order """

    @classmethod
    def setUpClass(cls):
        """ This runs once before the entire test suite """
        app.debug = False
        app.testing = True
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI

    @classmethod
    def tearDownClass(cls):
        """ This runs once after the entire test suite """
        pass

    def setUp(self):
        """ This runs before each test """
        init_db()
        db.drop_all()
        db.create_all()
        self.app = app.test_client()

    def tearDown(self):
        """ This runs after each test """
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


######################################################################
#  P L A C E   T E S T   C A S E S   H E R E 
######################################################################

    def test_index(self):
        """ Test index call """
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_orders(self):
        """ Test create an order service """
        order_factory = _get_order_factory_with_items(1)
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        
    def test_get_orders(self):
        """ Test Get list of orders service """
        resp = self.app.get('/orders')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_order_negative_qty(self):
        """ Create an order with negative quantity """
        order_factory = _get_order_factory_with_items(1)
        order_factory.order_items[0].quantity = -2
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_negative_price(self):
        """ Create an order with negative price """
        order_factory = _get_order_factory_with_items(1)
        order_factory.order_items[0].price = -5
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_zero_qty(self):
        """ Create an order with zero quantity """
        order_factory = _get_order_factory_with_items(1)
        order_factory.order_items[0].quantity = 0
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)