from django.test import TestCase
from datetime import date, datetime, timedelta

# Create your tests here.

from dishes.models import EstablishmentDish
from establishments.models import DinnerWagon, BranchHall
from orders.models import Order, OrdersCartRow


class OrderTest(TestCase):
    def test_order_expire_date(self):
        order_test = Order(client_phone=8432424,
                           type=Order.TYPE_DINNER_WAGON,
                           state=Order.STATE_DONE,
                           order_date=date(2014, 12, 12),
                           execute_datetime=datetime(2014, 12, 12, 18))
        self.assertEqual(order_test.expire_date, datetime(2015, 1, 11, 18).date(), "expire_date is not equal")

    def test_order_make(self):
        order_test = Order(client_phone=8432424,
                           type=Order.TYPE_DINNER_WAGON,
                           state=Order.STATE_DONE,
                           order_date=date(2014, 12, 12),
                           execute_datetime=datetime(2014, 12, 12, 18))
        order_test.make()
        self.assertEqual(order_test.state.__str__(), '4', 'State of order is not equal')
        self.assertEqual(order_test.type, Order.TYPE_DINNER_WAGON)

    def test_order_accept(self):
        order_test = Order(client_phone=8432424,
                           type=Order.TYPE_DINNER_WAGON,
                           state=Order.STATE_DONE,
                           order_date=date(2014, 12, 12),
                           execute_datetime=datetime(2014, 12, 12, 18))
        order_test.accept()
        self.assertEqual(order_test.state, Order.STATE_IN_PROGRESS)

    def test_order_decline(self):
        order_test = Order(client_phone=8432424,
                           type=Order.TYPE_DINNER_WAGON,
                           state=Order.STATE_DONE,
                           order_date=date(2014, 12, 12),
                           execute_datetime=datetime(2014, 12, 12, 18),
                           dinner_wagon=DinnerWagon(is_reserved=1, seats=2))
        order_test.decline()
        self.assertEqual(order_test.state, Order.STATE_CANCELED)
        self.assertEqual(order_test.dinner_wagon.is_reserved, False)

    def test_order_perform(self):
        order_test = Order(client_phone=8432424,
                           type=Order.TYPE_DINNER_WAGON,
                           state=Order.STATE_DONE,
                           order_date=date(2014, 12, 12),
                           execute_datetime=datetime(2014, 12, 12, 18),
                           dinner_wagon=DinnerWagon(is_reserved=1, seats=2))
        order_test.perform()
        self.assertEqual(order_test.state, Order.STATE_DONE)
        self.assertEqual(order_test.dinner_wagon.is_reserved, False)


class OrdersCartRowTest(TestCase):
    def test_increment(self):
        order_test = Order(client_phone=8432424,
                           type=Order.TYPE_DINNER_WAGON,
                           state=Order.STATE_DONE,
                           order_date=date(2014, 12, 12),
                           execute_datetime=datetime(2014, 12, 12, 18),
                           dinner_wagon=DinnerWagon(is_reserved=1, seats=2))
        establishment_dish_test = EstablishmentDish()
        order_card_row_test = OrdersCartRow(dishes_count=1, establishment_dish=establishment_dish_test,
                                            order=order_test)
        order_card_row_test.increment()
        self.assertEqual(order_card_row_test.dishes_count, 2, "Numbers of dishes in cart is not equal")

    def test_decrement(self):
        order_test = Order(client_phone=8432424,
                           type=Order.TYPE_DINNER_WAGON,
                           state=Order.STATE_DONE,
                           order_date=date(2014, 12, 12),
                           execute_datetime=datetime(2014, 12, 12, 18),
                           dinner_wagon=DinnerWagon(is_reserved=1, seats=2))
        establishment_dish_test = EstablishmentDish()
        order_card_row_test = OrdersCartRow(dishes_count=3, establishment_dish=establishment_dish_test,
                                            order=order_test)
        order_card_row_test.decrement()
        self.assertEqual(order_card_row_test.dishes_count, 2, "Numbers of dishes in cart is not equal")
