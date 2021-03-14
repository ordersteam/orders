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

BASE_URL = '/orders'
CONTENT_TYPE_JSON = "application/json"


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
        """ Create an order """
        order_factory = _get_order_factory_with_items(1)
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    
    def test_update_order(self):
        """ Update an existing order """
        # create a order to update
        test_order = _get_order_factory_with_items(1)
        resp = self.app.post(
            BASE_URL, json=test_order.serialize(), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # update the order
        new_order = resp.get_json()
        new_order["category"] = "unknown"
        resp = self.app.put(
            "{0}/{1}".format(BASE_URL, new_order["id"]),
            json=new_order,
            content_type=CONTENT_TYPE_JSON,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)