"""
Test factory to create test cases 
"""
import random
import factory
from factory.fuzzy import FuzzyChoice
from flask_sqlalchemy import SQLAlchemy
from service.models import Order, Item

db = SQLAlchemy()


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    """ Base Factory for SQLAlchemy """
    class Meta:
        """ Meta Class """
        abstract = True
        sqlalchemy_session = db.session


class OrderFactory(BaseFactory):
    """ Creates fake orders """

    class Meta:
        """ Meta class for Order Factory """
        model = Order

    id = factory.Sequence(lambda n: n)
    customer_id = random.randint(1, 100000)
    order_items = []

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        """ Method to add items to Order Factory """
        if not create:
            return

        if extracted:
            self.order_items = extracted


class ItemFactory(BaseFactory):
    """ Creates fake order items """

    class Meta:
        """ Meta class for Order Item Factory """
        model = Item

    item_id = factory.Sequence(lambda n: n)
    product_id = random.randint(1, 100)
    quantity = random.randint(1, 10)
    price = random.uniform(1, 1000)
    order_id = factory.SubFactory(OrderFactory)


if __name__ == "__main__":
    for _ in range(5):
        item1 = ItemFactory()
        item2 = ItemFactory()
        item3 = ItemFactory()
        order = OrderFactory(items=[item1, item2, item3])
        print(order.serialize())