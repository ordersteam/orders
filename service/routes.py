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
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes

# For this example we'll use SQLAlchemy, a popular ORM that supports a
# variety of backends including SQLite, MySQL, and PostgreSQL
from flask_sqlalchemy import SQLAlchemy
from service.models import Order, Item,  DataValidationError

# Import Flask application
from . import app


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
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(status=status.HTTP_404_NOT_FOUND, error="Not Found", message=message),
        status.HTTP_404_NOT_FOUND,
    )


@app.errorhandler(status.HTTP_405_METHOD_NOT_ALLOWED)
def method_not_supported(error):
    """ Handles unsuppoted HTTP methods with 405_METHOD_NOT_SUPPORTED """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
            error="Method not Allowed",
            message=message,
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )


@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error="Unsupported media type",
            message=message,
        ),
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
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
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    app.logger.info("Request for Root URL")
    return(
        jsonify(
            name="Orders REST API Service",
            version="1.0",
            paths=url_for("list_orders", _external=True),
        ),
        status.HTTP_200_OK,
    )


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_orders(order_id):
    """
    Retrieve a single order
    This endpoint will return a order based on its id
    """
    app.logger.info("Request for order with id: %s", order_id)
    order = Order.find(order_id)
    if not order:
        raise NotFound("Order with id '{}' was not found.".format(order_id))
    return make_response(jsonify(order.serialize()), status.HTTP_200_OK)


@app.route("/orders/customer/<int:customer_id>", methods=["GET"]) 
def get_customer_orders(customer_id):
    """
    Get the orders of particular customer
    This endpoint will return the orders for a customer id specified
    """
    app.logger.info("Request for order with cust id: %s", customer_id)
    orders = Order.find_by_customer_id(customer_id)
    results = [order.serialize() for order in orders]
    app.logger.info("Returning %d orders", len(results))
    return   make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# CREATE AN ORDER
######################################################################

@app.route("/orders", methods=["POST"])
def  create_order():
    """
    Creates an order based on the JSON object sent 
    """
    app.logger.info("Request to create an order")
    check_content_type("application/json")
    order = Order();
    try:
        order.deserialize(request.get_json())
    except DataValidationError as dataValidationError:
        abort(status.HTTP_400_BAD_REQUEST, dataValidationError)

    order.create();
    message = order.serialize()
    location_url = url_for("get_orders", order_id=order.id, _external=True)
    app.logger.info('Created Order with id: {}'.format(order.id))
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ORDERS
######################################################################

@app.route("/orders", methods = ["GET"])
def list_orders():
    """
    Returns list of all orders
    """
    app.logger.info("Request for order list")
    
    params = request.args
    sort_value = params.get('sort')
    sortby_value = params.get('sort_by')

    if sort_value is not None:
        orders = Order.sort_by(sort_value,sortby_value)
    else:
        orders = Order.all()
    
    try:
        results = [order.serialize() for order in orders]
    except DataValidationError as dataValidationError:
        abort(status.HTTP_400_BAD_REQUEST, dataValidationError)

    app.logger.info("Returning %d orders", len(results))
    return make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# UPDATE AN ORDER
######################################################################

@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_orders(order_id):
    """
    Update a Order

    This endpoint will update a Order based the body that is posted
    """
    app.logger.info("Request to update Order with id: %s", order_id)
    check_content_type("application/json")
    order = Order.find(order_id)
    if not order:
        raise NotFound("order with id '{}' was not found.".format(order_id))
    order.deserialize(request.get_json())
    order.id = order_id
    order.update()

    app.logger.info("Order with ID [%s] updated.", order_id)
    return make_response(jsonify(order.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE AN Order
######################################################################
@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    """
    Delete an Order
    This endpoint will delete an Order based the id specified in the path
    """
    app.logger.info("Request to delete order with id: %s", order_id)
    order = Order.find(order_id)
    if order:
        order.delete()      
    return make_response("", status.HTTP_204_NO_CONTENT)

######################################################################
# CANCEL AN Order
######################################################################

@app.route("/orders/<int:order_id>/cancel", methods=["PUT"])
def cancel_order(order_id):
    """
    Cancel an Order
    This endpoint will cancel an Order based the id specified in the path
    """
    app.logger.info("Request to cancel order with id: %s", order_id)
    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, "Order id '{}' was not found.".format(order_id)) 
    
    items_not_cancellable = 0
    try: 
       for item in order.order_items:
            if item.status in ["DELIVERED", "SHIPPED"]:
                items_not_cancellable +=1 
            # Order status is PLACED or CANCELLED
            elif item.status == "PLACED":
              item.status = "CANCELLED"
            if items_not_cancellable == len(order.order_items):
                    raise DataValidationError("All items have been shipped/delivered. Cannot the order")  
    except DataValidationError as dataValidationError:
            abort(status.HTTP_400_BAD_REQUEST, dataValidationError)
    order.update()    
    return order.serialize(), status.HTTP_200_OK
           


######################################################################
#  Item related APIs below
######################################################################

######################################################################
#  GET AN ITEM
######################################################################

@app.route("/orders/<int:order_id>/items/<int:item_id>", methods=["GET"])
def get_item(order_id, item_id):
    """
    Retrieve a single item from an order
    This endpoint will return an item's details based on its id
    """
    app.logger.info("Request for order with id: %s and item with id : %s", order_id, item_id)
    check_content_type("application/json")
    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' not found.".format(order_id))
    
    item_found = False
    get_order_item = Item()
    get_order_item.deserialize(request.get_json())
    item_found = find_item(get_order_item, order, item_id)

    if not item_found:
        abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in order.".format(item_id))   
    
    return get_order_item.serialize(), status.HTTP_200_OK  

######################################################################
#  UPDATE ITEM
######################################################################
@app.route("/orders/<int:order_id>/items/<int:item_id>", methods=["PUT"])
def update_item(order_id, item_id):
    """
    Update an item inside an order
    """  
    app.logger.info("Request to update order with id :%s and item with id : %s", order_id, item_id)
    check_content_type("application/json")
    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' not found.".format(order_id))
    item_found = False

    updated_order_item = Item()
    updated_order_item.deserialize(request.get_json())
    item_found = find_item(updated_order_item, order, item_id)

    if not item_found:
        abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in order.".format(item_id))   
    order.update()
    return order.serialize(), status.HTTP_200_OK     

######################################################################
#  DELETE ITEM
######################################################################

@app.route("/orders/<int:order_id>/items/<int:item_id>", methods=["DELETE"])
def delete_item(order_id, item_id):
    """
    delete an item inside an order
    """  
    app.logger.info("Request to delete order with id :%s and item with id : %s", order_id, item_id)
    check_content_type("application/json")
    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' not found.".format(order_id))
    

    item_found = False
    for item in order.order_items:
       if item.item_id == item_id:
            item_found = True
            item.delete()

    if not item_found:
        abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in order.".format(item_id))   
    return make_response("", status.HTTP_204_NO_CONTENT)  

######################################################################
#  CANCEL ITEM
######################################################################
@app.route("/orders/<int:order_id>/items/<int:item_id>/cancel", methods=["PUT"])
def cancel_item(order_id, item_id):
    """
    Cancel item in Order
    This endpoint will cancel an item in the Order based the item id specified in the path
    """
    app.logger.info("Request to cancel order with id :%s and item with id : %s", order_id, item_id)
    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, "Order id '{}' was not found.".format(order_id)) 
    
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
            abort(status.HTTP_404_NOT_FOUND, "Item with id '{}'  not found in item.".format(item_id))   
        if not item_cancellable: 
            raise DataValidationError("Item not cancellable")
    except DataValidationError as dataValidationError:
            abort(status.HTTP_400_BAD_REQUEST, dataValidationError) 
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
