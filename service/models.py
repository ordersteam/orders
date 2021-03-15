"""
Models for Order

All of the models are stored in this module
"""
import logging
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()

class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """
    pass


class Item(db.Model):
    """
    Class that represents an item inside an order... For eg if a person orders 3 oranges and 4 apples as 
    part of a single order, this Item class represents the 3 oranges. 
    """

    app = None

    # Order Item Table Schema
    item_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable = False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    # TODO:  Add status
    # The order id has to be stored in another table as the different items have the same order id
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

    def __repr__(self):
        return "<Item %r>" % (self.item_id)

    def serialize(self):
        """ Serializes an item  into a dictionary """
        return {
            "item_id": self.item_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price
        }

    def deserialize(self, data):
        """
        Deserializes an Item  from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.product_id   = data["product_id"]
            self.quantity =  data["quantity"]
            self.price = data["price"]
            price_aux = float(self.price)
            quantity_aux = float(self.quantity)

            #checks product id is an int
            if self.product_id is None or not isinstance(self.product_id, int):
                raise DataValidationError("Invalid order: check product id")
            
            #checks quantity is int and greater than 0
            if self.quantity is None or not isinstance(self.quantity, int) or quantity_aux <= 0:
                raise DataValidationError("Invalid Item: check quantity")
            
            #checks price is int/float and not less than 0
            if self.price is None or price_aux <= 0 or \
                    (not isinstance(self.price, float) and not isinstance(self.price, int)):
                raise DataValidationError("Invalid Item: check price")

        except KeyError as error:
            raise DataValidationError("Invalid Item: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid Item: body of request contained" "bad or no data"
            )
        return self

    
class Order(db.Model):
    """ Class that represents an Order """
    logger = logging.getLogger(__name__)
    app = None

    ##################################################
    # Order Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    creation_date = db.Column(db.DateTime(), default=datetime.now)
    # List of items in the order 
    order_items = db.relationship('Item', backref='order', cascade="all, delete")

    def __repr__(self):
        return "<Order %r>" % self.id


    def create(self):
        """
        Creates an order in the DB
        """
        if self.customer_id is None:
            raise DataValidationError("Invalid Order : Customer Id  empty")

        if len(self.order_items) == 0:
            raise DataValidationError("Invalid Order : Order Items  empty")
    
        db.session.add(self)
        db.session.commit()


    def update(self):
        """
        Updates an Order to the database
        """
        if not self.id or not isinstance(self.id, int):
            raise DataValidationError("Update called with invalid id field")
        if self.customer_id is None or not isinstance(self.customer_id, int):
            raise DataValidationError("Customer Id is not valid")
        if len(self.order_items) == 0:
            raise DataValidationError("Order Items can't be empty")
        db.session.commit()

    def delete(self):
        """
        Removes an Order from the Database
        """
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """ Serializes an order into a dictionary """
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "creation_date": self.creation_date,
            "order_items": [order_item.serialize() for order_item in self.order_items]
        }

    def deserialize(self, data: dict):
        """
        Deserializes an Order from a dictionary
        :param data: a dictionary of attributes
        :type data: dict
        :return: a reference to self
        :rtype: Order
        """
        try:
            self.customer_id = data["customer_id"]
            # check if customer_id is integer
            if self.customer_id is None or not isinstance(self.customer_id, int):
                raise DataValidationError("Invalid Order: Customer Id must be integer")

            items = data["order_items"]
            if items is None or len(items) == 0:
                raise DataValidationError("Order Items can't be empty")
            for data_item in items:
                item = Item()
                item.deserialize(data_item)
                self.order_items.append(item)
        except KeyError as error:
            raise DataValidationError("Invalid order: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid order: body of request contained bad or no data"
            )
        return self


    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all() 

    @classmethod
    def all(cls):
        """ Returns all of the Orders in the database """
        logger.info("Processing all Orders")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """ Finds a Order by it's ID """
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_or_404(cls, by_id):
        """ Find an Order by it's id """
        logger.info("Processing lookup or 404 for id %s ...", by_id)
        return cls.query.get_or_404(by_id)

    @classmethod
    def find_by_customer_id(cls, customer_id: int):
        """Returns all of the orders with customer_id: customer_id """
        cls.logger.info("Processing customer_id query for %s ...", customer_id)
        return cls.query.filter(cls.customer_id == customer_id)