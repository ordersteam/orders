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
from flask import abort

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

    def _create_orders(self, count):
        """ Factory method to create orders in bulk """
        orders = []
        for _ in range(count):
            test_order = _get_order_factory_with_items(count=1)
            resp = self.app.post(
                "/orders", json=test_order.serialize(), content_type="application/json"
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED, "Could not create test order"
            )
            new_order = resp.get_json()
            test_order.id = new_order["id"]
            order_items = new_order["order_items"]
            for i, item in enumerate(order_items):
                test_order.order_items[i].item_id = item["item_id"]
            orders.append(test_order)
        return orders


######################################################################
#  P L A C E   T E S T   C A S E S   H E R E 
######################################################################

    def test_index(self):
        """ Test index call """
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data['name'], 'Orders REST API Service')


    def test_create_orders(self):
        """ Create an order """
        order_factory = _get_order_factory_with_items(1)
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_orders_wrong_content_type(self):
        """ Create an order with wrong content type """
        resp = self.app.post('/orders',
                             json=_get_order_factory_with_items(1).serialize(),
                             content_type='application/xml')

        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_orders_customer_id_wrong_type(self):
        """ Create an order with invalid customer_id """
        order_factory = _get_order_factory_with_items(1)
        order_factory.customer_id = "customer id is integer!"
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_order(self):
        """ Update an existing order """
        # create a order to update
        test_order = self._create_orders(3)[0]
        order_factory = _get_order_factory_with_items(1)
        resp = self.app.put('/orders/{}'.format(test_order.id), json=order_factory.serialize(),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    #def test_update_order(self):
       # """ Update an existing Order """
        # create an order to update
        #test_order = OrderFactory()
        #resp = self.app.post(
        #    "/orders", json=test_order.serialize(), content_type="application/json"
        #)
        #self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # update the order
        #new_order = resp.get_json()
        #new_order["customer_id"] = 100
        #resp = self.app.put(
        #    "/orders/{}".format(new_order["id"]),
        #    json=new_order,
        #    content_type="application/json",
        #)
        #self.assertEqual(resp.status_code, status.HTTP_200_OK)
        #updated_order = resp.get_json()
        #self.assertEqual(updated_order["customer_id"], 100)

    def test_create_order_items_missing(self):
        """ Create an order missing order_items """
        resp = self.app.post('/orders',
                             json=_get_order_factory_with_items(0).serialize(),
                             content_type='application/json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_url(self):
        """ Try an invalid url  """
        resp = self.app.get(
            "/order", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND, "Not Found")    

    def test_wrong_method(self):
        """ Try a Method not allowed """
        resp = self.app.patch("/orders")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    def test_internal_server_error(self):
        """ Internal Server error from Create Order """
        @app.route('/orders/500Error')
        def internal_server_error():
            abort(500)

        resp = self.app.get('/orders/500Error')
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_delete_order(self):
        """ Test Delete Order API """
        # get the id of an order
        order =  _get_order_factory_with_items(1)
        resp = self.app.delete(
            "/orders/{}".format(order.id), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
    