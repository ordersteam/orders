"""
Order Service
Paths:
------
GET /orders - Returns a list all of the orders and order items
GET /orders/{id} - Returns the Order and its items with a given id number
POST /orders - creates a new order record in the database
PUT /orders/{id} - updates a Order record in the database
DELETE /orders/{id} - deletes a order record and associated items in the database
"""

import os
import sys
import logging
from werkzeug.exceptions import NotFound
from flask import Flask, jsonify, request, url_for, make_response, abort, render_template
from flask_api import status  # HTTP Status Codes
from flask_restx import Api, Resource, fields, reqparse, inputs

# For this example we'll use SQLAlchemy, a popular ORM that supports a
# variety of backends including SQLite, MySQL, and PostgreSQL
from flask_sqlalchemy import SQLAlchemy
from service.models import Order, Item,  DataValidationError

# Import Flask application
from . import app


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    app.logger.info("Request for Root URL")
    return app.send_static_file('index.html')



######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(app,
          version='1.0.0',
          title='Order REST API Service',
          description='This is the order service  for ecommerce website',
          default='orders',
          default_label='Orders operations',
          doc='/apidocs'    # default also could use doc='/apidocs/'
          )

# Define the model so that the docs reflect what can be sent
create_item_model = api.model('Item', {
    'product_id': fields.Integer(required=True,
                                 description='Product id of item'),
    'quantity': fields.Integer(required=True,
                               description='Quantity of item'),
    'price': fields.Float(required=True,
                          description='Price of item'),
    'status': fields.String(required=True,
                            description='Status of item')
})

item_model = api.model('Item', {
    'item_id': fields.Integer(readOnly=True,
                              description='The unique item id auto assigned '),
    'product_id': fields.Integer(required=True,
                                 description='Product id of item'),
    'quantity': fields.Integer(required=True,
                               description='Quantity of item'),
    'price': fields.Float(required=True,
                          description='Price of item'),
    'status': fields.String(required=True,
                            description='Status of item'),
    'item_total': fields.Float(readOnly=True,
                              description='Line amount'),
})

create_model = api.model('Order', {
    'customer_id': fields.Integer(required=True,
                                  description='The customer id of Order'),
    'order_items': fields.List(fields.Nested(create_item_model, required=True), required=True,
                               description='The items in Order')
})

order_update_model = api.model('OrderUpdateModel', {
    'customer_id': fields.Integer(required=True,
                                  description='customer id of order')
})

order_model = api.model('Order', {
    'id': fields.Integer(required=True, description='The id for each order autoassigned'),
    'creation_date': fields.DateTime(required=False, description='The date and time at which order was created'),
    'customer_id': fields.Integer(required=True,
                                  description='The customer id of Order'),
    'order_items': fields.List(fields.Nested(item_model, required=True), required=True,
                               description='The items in Order'),
    'order_total': fields.Float(readOnly=True, description='Order total amount (sum of all item totals)')
})

# query string arguments
order_args = reqparse.RequestParser()
order_args.add_argument('customer_id', type=int, required=False, help='List Orders by Customer id')
order_args.add_argument('sort', type=str, required=False, help='List Orders by sort order')
order_args.add_argument('sort_by', type=str, required=False, help='List Orders by the field')


item_args = reqparse.RequestParser()
item_args.add_argument('product_id', type=int, required=False, help='List Orders by product id')

######################################################################
# Error Handlers
######################################################################

@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)


@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST, error="Bad Request", message=message
        ),
        status.HTTP_400_BAD_REQUEST,
    )


@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_404_NOT_FOUND, error="Not Found", message=str(error)
        ),
        status.HTTP_404_NOT_FOUND,
    )


@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    """ Handles unexpected server error with 500_SERVER_ERROR """
    message = str(error)
    app.logger.error(message)
    return (
        jsonify(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=message,
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


######################################################################
# CREATE AN ORDER
######################################################################

@api.route('/orders', strict_slashes=False)
class OrderCollection(Resource):

    @api.doc('create_order')
    @api.expect(create_model)
    @api.response(400, 'Posted data was not valid')
    @api.response(201, 'Order created successfully')
    @api.marshal_with(order_model, code=201)
    def  post(self):
        """
        Creates an order based on the JSON object sent 
        """
        app.logger.info("Request to create an order")
        check_content_type("application/json")
        order = Order();
        try:
            order.deserialize(request.get_json())
        except DataValidationError as dataValidationError:
            api.abort(status.HTTP_400_BAD_REQUEST, dataValidationError)

        order.create();
        message = order.serialize()
        location_url = api.url_for(OrderResource, order_id=order.id, _external=True)
        app.logger.info('Created Order with id: {}'.format(order.id))
        return message, status.HTTP_201_CREATED, {"Location": location_url}

######################################################################
# LIST ORDERS
######################################################################

    @api.doc('list_orders')
    @api.expect(order_args, validate=True)
    @api.marshal_with(order_model, code=200)
    def get(self):
        """
        Returns list of all orders
        """
        app.logger.info("Request for order list")
        
        params = request.args
        sort_value = params.get('sort')
        sortby_value = params.get('sort_by')
        customer_id = params.get("customer_id")

        if sort_value is not None:
            orders = Order.sort_by(sort_value,sortby_value)
        else:
            orders = Order.all()
        
        if customer_id:
            orders = Order.find_by_customer_id(customer_id)

        try:
            results = [order.serialize() for order in orders]
        except DataValidationError as dataValidationError:
            api.abort(status.HTTP_400_BAD_REQUEST, dataValidationError)

        app.logger.info("Returning %d orders", len(results))
        return results, status.HTTP_200_OK

######################################################################
# UPDATE AN ORDER
######################################################################
@api.route("/orders/<int:order_id>")
@api.param('order_id', 'The Order identifier')
class OrderResource(Resource):
    
    @api.doc('update_orders')
    @api.response(404, 'Order not found')
    @api.response(400, 'The posted Order data was not valid')
    @api.expect(order_update_model)
    @api.marshal_with(order_model)
    def put(self, order_id):
        """
        Update a Order

        This endpoint will update a Order based the body that is posted
        """
        app.logger.info("Request to update Order with id: %s", order_id)
        check_content_type("application/json")
        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' was not found.".format(order_id))
        order.customer_id = api.payload["customer_id"]
        order.id = order_id
        order.update()

        app.logger.info("Order with ID [%s] updated.", order_id)
        return order.serialize(), status.HTTP_200_OK

    @api.doc('get_orders')
    @api.response(404, 'Order was not found')
    @api.marshal_with(order_model)
    def get(self,order_id):
        """
        Retrieve a single order
        This endpoint will return a order based on its id
        """
        app.logger.info("Request for order with id: %s", order_id)
        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order was not found.")
        return order.serialize(), status.HTTP_200_OK
        

    ######################################################################
    # DELETE AN Order
    ######################################################################
    @api.doc('delete_orders')
    @api.response(404, 'Order not found')
    @api.marshal_with(order_model)
    def delete(self, order_id):
        """
        Delete an Order
        This endpoint will delete an Order based the id specified in the path
        """
        app.logger.info("Request to delete order with id: %s", order_id)
        order = Order.find(order_id)
        if order:
            order.delete()      
        return "", status.HTTP_204_NO_CONTENT

######################################################################
# CANCEL AN Order
######################################################################
@api.route('/orders/<int:order_id>/cancel')
@api.param('order_id', 'The Order identifier')
class CancelOrderResource(Resource):

    @api.doc('cancel_orders')
    @api.response(404, 'Order not found')
    @api.response(400, 'The Order is not valid for cancel')
    @api.marshal_with(order_model)
    def put(self, order_id):
        """
        Cancel an Order
        This endpoint will cancel an Order based the id specified in the path
        """
        app.logger.info("Request to cancel order with id: %s", order_id)
        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order id '{}' was not found.".format(order_id)) 
        
        items_not_cancellable = 0
        try: 
            for item in order.order_items:
                if item.status in ["DELIVERED", "SHIPPED"]:
                    items_not_cancellable +=1 
                # Order status is PLACED or CANCELLED
                elif item.status == "PLACED":
                    item.status = "CANCELLED"
                if items_not_cancellable == len(order.order_items):
                    raise DataValidationError("All items have been shipped/delivered. Cannot cancel the order")  
        except DataValidationError as dataValidationError:
                api.abort(status.HTTP_400_BAD_REQUEST, dataValidationError)
        order.update()    
        return order.serialize(), status.HTTP_200_OK
            


######################################################################
#  Item related APIs below
######################################################################
######################################################################
# LIST ITEMS
######################################################################
@api.route('/items', strict_slashes=False)
class ItemCollection(Resource):

    @api.doc('list_items')
    @api.expect(item_args, validate=True)
    @api.marshal_with(item_model, code=200)
    def get(self):
        """
        Returns list of all items or items based on product id
        """
        app.logger.info("Request for item list")
        
        params = request.args
        product_id = params.get("product_id")
       
        if product_id:
            items = Item.find_by_product_id(product_id)
        else:
            items = Item.all()
        try:
            results = [item.serialize() for item in items]
        except DataValidationError as dataValidationError:
            api.abort(status.HTTP_400_BAD_REQUEST, dataValidationError)

        app.logger.info("Returning %d items", len(results))
        return results, status.HTTP_200_OK


######################################################################
#  Add Item to order
######################################################################
@api.route('/orders/<int:order_id>/items')
@api.param('order_id', 'The Order identifier')
class ItemCollection(Resource):   

    @api.doc('add_orders_items')
    @api.response(404, 'Order not found')
    @api.response(400, 'The posted Item data was not valid')
    @api.expect(item_model)
    @api.marshal_with(order_model)
    def put(self, order_id):
        """
        Adds an item to the order based on the JSON object sent 
        """
        app.logger.info("Request to create an item inside the order")
        check_content_type("application/json")

        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' not found.".format(order_id))

        item = Item();
        try:
            item.deserialize(request.get_json())
        except DataValidationError as dataValidationError:
            api.abort(status.HTTP_400_BAD_REQUEST, dataValidationError)

        order.order_items.append(item)
        order.update();
        return order.serialize(), status.HTTP_200_OK


@api.route('/orders/<int:order_id>/items/<int:item_id>', strict_slashes=False)
@api.param('order_id', 'Order identifier')
@api.param('item_id', 'Item identifier')
class ItemResource(Resource):        
    ######################################################################
    #  GET AN ITEM
    ######################################################################

    @api.doc('get_orders')
    @api.response(404, 'Order not found')
    @api.marshal_with(item_model)
    def get(self, order_id, item_id):
        """
        Retrieve a single item from an order
        This endpoint will return an item's details based on its id
        """
        app.logger.info("Request for order with id: %s and item with id : %s", order_id, item_id)
        check_content_type("application/json")
        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' not found.".format(order_id))
        
        item_found = False
        get_order_item = Item()
        for i in range(len(order.order_items)):
            if order.order_items[i].item_id == item_id:
                item_found = True
                get_order_item = order.order_items[i]
                break
        if not item_found:
            api.abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in order.".format(item_id))   
        return get_order_item.serialize(), status.HTTP_200_OK  

    ######################################################################
    #  UPDATE ITEM
    ######################################################################

    @api.doc('update_order_items')
    @api.response(404, 'Order not found')
    @api.response(400, 'Posted Order data was not valid')
    @api.expect(item_model)
    @api.marshal_with(order_model)
    def put(self, order_id, item_id):
        """
        Update an item inside an order
        """  
        app.logger.info("Request to update order with id :%s and item with id : %s", order_id, item_id)
        check_content_type("application/json")
        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' not found.".format(order_id))
        item_found = False

        updated_order_item = Item()
        updated_order_item.deserialize(request.get_json())
        item_found = find_item(updated_order_item, order, item_id)

        if not item_found:
            api.abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in order.".format(item_id))   
        order.update()
        return order.serialize(), status.HTTP_200_OK     


    ######################################################################
    #  DELETE ITEM
    ######################################################################
   
    @api.doc('delete_order_items')
    @api.response(404, 'Order not found')
    @api.response(400, 'The posted Order data was not valid')
    def delete(self, order_id, item_id):
        """
        delete an item inside an order
        """  
        app.logger.info("Request to delete order with id :%s and item with id : %s", order_id, item_id)
        check_content_type("application/json")
        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' not found.".format(order_id))

        item_found = False
        for item in order.order_items:
            if item.item_id == item_id:
                item_found = True
                item.delete()

        if not item_found:
            api.abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in order.".format(item_id))   
        return '', status.HTTP_204_NO_CONTENT
######################################################################
#  CANCEL ITEM
######################################################################
@api.route('/orders/<int:order_id>/items/<int:item_id>/cancel')
@api.param('order_id', 'Order identifier')
@api.param('item_id', 'Item identifier')
class CancelItemResource(Resource):
    @api.doc('cancel_items')
    @api.response(404, 'Item not found')
    @api.response(400, 'The Item is not valid for cancel')
    @api.marshal_with(order_model)
    def put(self, order_id, item_id):
        """
        Cancel item in Order
        This endpoint will cancel an item in the Order based the item id specified in the path
        """
        app.logger.info("Request to cancel order with id :%s and item with id : %s", order_id, item_id)
        order = Order.find(order_id)
        if not order:
            api.abort(status.HTTP_404_NOT_FOUND, "Order id '{}' was not found.".format(order_id)) 
        
        item_found = False
        item_cancellable = True
        try:
            for item in order.order_items:
                if item.item_id == item_id:
                    item_found = True
                    if item.status in ["DELIVERED", "SHIPPED"]:
                        item_cancellable = False
                    elif item.status == "PLACED":
                        item.status = "CANCELLED"
            if not item_found:
                api.abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in item.".format(item_id))   
            if not item_cancellable: 
                raise DataValidationError("Item not cancellable")
        except DataValidationError as dataValidationError:
                api.abort(status.HTTP_400_BAD_REQUEST, dataValidationError) 
        order.update()        
        return order.serialize(), status.HTTP_200_OK
    
######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def find_item(item, order, item_id):
    item_found = False
    for i in range(len(order.order_items)):
        if order.order_items[i].item_id == item_id:
            item_found = True
            order.order_items[i].product_id =item.product_id
            order.order_items[i].quantity = item.quantity
            order.order_items[i].price = item.price
            order.order_items[i].status = item.status
            order.order_items[i].item_total = item.item_total
            break
    return item_found    


def init_db():
    """ Initialies the SQLAlchemy app """
    global app
    Order.init_db(app)

def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(415, "Content-Type must be {}".format(content_type))
