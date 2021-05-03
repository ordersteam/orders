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
    """  This is an utility to create an order with count items """
    items = []
    for _ in range(count):
        items.append(ItemFactory())
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
        """ Factory method to create  more than one order """
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
#  P L A C E   O R D E R  R E L A T E D  T E S T   C A S E S   H E R E 
######################################################################

    def test_index(self):
        """ Test index call """
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_order(self):
        """ Get a single order """
        # get the id of a order
        test_order = self._create_orders(1)[0]
        resp = self.app.get(
            "/orders/{}".format(test_order.id), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], test_order.id)

    def test_get_order_not_found(self):
        """ Get a Order thats not found """
        resp = self.app.get("/orders/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_get_sorted_parameters(self):
        """ Test Get sorted list of orders service by customer id """
        test_order = self._create_orders(2)[0]
        resp = self.app.get('/orders?sort=customer_id&sort_by=asc')
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

    def test_create_order_zero_qty(self):
        """ Create an order with zero quantity """
        order_factory = _get_order_factory_with_items(1)
        order_factory.order_items[0].quantity = 0
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


    def test_update_non_existing_order(self):
        """ Update an non existing order """
        resp = self.app.put('/orders/{}'.format(0),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


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

    def test_delete_order(self):
        """ Test Delete Order API """
        # get the id of an order
        order =  self._create_orders(1)[0]
        resp = self.app.delete(
            "/orders/{}".format(order.id), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)    


    def test_cancel_order(self):
        """ Cancel an order after creating it """
        order = self._create_orders(1)[0]
        resp = self.app.put("/orders/{}/cancel".format(order.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_cancel_order_not_found(self):
        """ Cancel an order which does not exist"""
        resp = self.app.put("/orders/{}/cancel".format(0))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)    

    def test_cancel_order_with_everything_shipped(self):
        """ Cancel an order with all items as shipped/delivered  """
        order_factory = _get_order_factory_with_items(2)
        order_factory.order_items[0].status = "DELIVERED"
        order_factory.order_items[1].status = "SHIPPED"

        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_order_id = resp.get_json()["id"]
        resp = self.app.put("/orders/{}/cancel".format(new_order_id))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_customer_orders(self):
        """ Get orders of  customer """

        test_order = self._create_orders(1)[0]
        resp = self.app.get('/orders?customer_id={}'.format(test_order.customer_id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data[0]["customer_id"], test_order.customer_id)

    def test_get_customer_orders_with_invalid_customer_id(self):
        """ Get orders of customer  with invalid customer id"""
        resp = self.app.get(
            "/orders?customer_id=0", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK) 


######################################################################
#  P L A C E   I T E M  R E L A T E D  T E S T   C A S E S   H E R E 
######################################################################

    def test_create_item(self):
        """ Test create an item insider order service """
        order_factory = _get_order_factory_with_items(1)
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        order_item = ItemFactory()
        resp = self.app.put('/orders/{}/items'.format(resp.get_json()["id"]),
                            json=order_item.serialize(),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


    def test_create_invalid_item(self):
        """ Test create an invalid item """
        order_factory = _get_order_factory_with_items(1)
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        order_item = ItemFactory()
        order_item.quantity = -1
        resp = self.app.put('/orders/{}/items'.format(resp.get_json()["id"]),
                            json=order_item.serialize(),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)    

    
    def test_create_item_order_not_exists(self):
        """ Test create an item insider order which does not exist """
      
        resp = self.app.put('/orders/{}/items'.format(0),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)    
             
    def test_get_order_item(self):
        """ Get an Item inside Order"""
        test_order = self._create_orders(1)[0]
        item_id = test_order.order_items[0].item_id
        order_item = ItemFactory()
        resp = self.app.get('/orders/{}/items/{}'.format(test_order.id, item_id),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_item = resp.get_json()
        self.assertEqual(new_item["product_id"], order_item.product_id)
        self.assertEqual(new_item["quantity"], order_item.quantity)
        self.assertAlmostEqual(new_item["price"], order_item.price)
        self.assertEqual(new_item["status"], order_item.status)  


    def test_get_order_item_order_not_exists(self):
        """ Get an Item inside Order when order does not exist"""
        resp = self.app.get('/orders/{}/items/{}'.format(0, 0),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_order_item_not_exist(self):
        """ Get an Item inside order where the item does not exist"""
   
        test_order = self._create_orders(1)[0]
        item_id = test_order.order_items[0].item_id
        order_item = ItemFactory()
        resp = self.app.get('/orders/{}/items/{}'.format(test_order.id, 0),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)    
       
    def test_update_order_item(self):
        """ Update an Item inside order"""
   
        test_order = self._create_orders(1)[0]
        item_id = test_order.order_items[0].item_id
        order_item = ItemFactory()
        resp = self.app.put('/orders/{}/items/{}'.format(test_order.id, item_id),
                            json=order_item.serialize(),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_item = resp.get_json()["order_items"][0]
        self.assertEqual(new_item["product_id"], order_item.product_id)
        self.assertEqual(new_item["quantity"], order_item.quantity)
        self.assertAlmostEqual(new_item["price"], order_item.price)
        self.assertEqual(new_item["status"], order_item.status)


    def test_update_order_item_not_exist(self):
        """ Update an Item inside order where the item does not exist"""
   
        test_order = self._create_orders(1)[0]
        item_id = test_order.order_items[0].item_id
        order_item = ItemFactory()
        resp = self.app.put('/orders/{}/items/{}'.format(test_order.id, 0),
                            json=order_item.serialize(),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
      
    def test_update_order_item_order_not_exists(self):
        """ 
        Update an Item when order is not present
        """
        resp = self.app.put('/orders/{}/items/{}'.format(0, 0), json="",
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)    


    def test_delete_order_item(self):
        """ Delete an Item inside order"""
   
        test_order = self._create_orders(1)[0]
        item_id = test_order.order_items[0].item_id
        resp = self.app.delete('/orders/{}/items/{}'.format(test_order.id, item_id),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_item_order_not_exists(self):
        """ 
        Delete an Item when order is not present
        """

        resp = self.app.delete('/orders/{}/items/{}'.format(0, 0), json="",
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)    

    def test_delete_item_not_exist(self):
        """ Delete an Item not existed inside order"""
   
        test_order = self._create_orders(1)[0]
        resp = self.app.delete('/orders/{}/items/{}'.format(test_order.id, 0),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_item(self):
        """ Cancel an item in the order after creating it """
        order = self._create_orders(1)[0]
        item_id = order.order_items[0].item_id
        resp = self.app.put("/orders/{}/items/{}/cancel".format(order.id, item_id),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_cancel_Item_order_not_exists(self):
        """ 
        Cancel an Item when order is not present
        """

        resp = self.app.put('/orders/{}/items/{}/cancel'.format(0, 0),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)  

    def test_cancel_item_not_exist(self):
        """ Cancel an Item not existed inside order"""
   
        test_order = self._create_orders(1)[0]
        resp = self.app.put('/orders/{}/items/{}/cancel'.format(test_order.id, 0))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)  

    def test_cancel_shipped_or_delivered_item(self):
        """ Cancel an item which has been shipped/delivered  """
        order_factory = _get_order_factory_with_items(1)
        order_factory.order_items[0].status = "DELIVERED"
       
        resp = self.app.post('/orders',
                             json=order_factory.serialize(),
                             content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_order_id = resp.get_json()["id"]
        item_id = resp.get_json()["order_items"][0]["item_id"]
        resp = self.app.put("/orders/{}/items/{}/cancel".format(new_order_id, item_id),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST) 

    def test_get_order_item_product_id(self):
        """ Get an Item inside based on product id """
        test_order = self._create_orders(1)[0]
        item_id = test_order.order_items[0].item_id
        product_id = test_order.order_items[0].product_id
        order_item = ItemFactory()
        resp = self.app.get('/items?product_id={}'.format(product_id),
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_item = resp.get_json()[0]
        self.assertEqual(new_item["quantity"], order_item.quantity)
        self.assertAlmostEqual(new_item["price"], order_item.price)
        self.assertEqual(new_item["status"], order_item.status)      

    def test_get_order_items(self):
        """ Get list of all items """
        test_order = self._create_orders(2)[0]
        order_item = ItemFactory()
        resp = self.app.get('/items',
                            content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_item = resp.get_json()
        self.assertEqual(len(new_item), 2)
    