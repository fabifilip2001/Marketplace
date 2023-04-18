"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread, currentThread
import time

class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time

    def run(self):
        # firstly, every consumer has to create himself a cart
        cart_id = self.marketplace.new_cart()

        # iterate through operations list
        for orders in self.carts:
            for order in orders:
                command = order["type"]
                product = order["product"]
                amount = order["quantity"]

                # check the input command and act properly for each
                # for 'add', call add_to_cart function from marketplace 'amount' times
                if command == "add":
                    while amount > 0:
                        if self.marketplace.add_to_cart(cart_id, product):
                            amount -= 1
                        else:
                            time.sleep(self.retry_wait_time)
                # for 'remove', call remove_from_cart function from marketplace 'amount' times
                elif command == "remove":
                    while amount > 0:
                        self.marketplace.remove_from_cart(cart_id, product)
                        amount -= 1
        
        # finally, place the order iterating the list returned by the place_order function 
        # and print the specific message to output
        for cart_products in self.marketplace.place_order(cart_id):
            print("{} bought {}".format(currentThread().getName(), cart_products))
