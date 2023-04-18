"""
This module represents the Producer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
import time

class Producer(Thread):
    """
    Class that represents a producer.
    """

    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        """
        Constructor.

        @type products: List()
        @param products: a list of products that the producer will produce

        @type marketplace: Marketplace
        @param marketplace: a reference to the marketplace

        @type republish_wait_time: Time
        @param republish_wait_time: the number of seconds that a producer must
        wait until the marketplace becomes available

        @type kwargs:
        @param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time

    def run(self):
        # firstly, every producer has to register himself
        producer_id = str(self.marketplace.register_producer())

        # iterate through products that each producer has to publish
        while 1:
            for data in self.products:
                product = data[0]
                amount = data[1]
                wait_time = data[2]

                # for each product, call publish function and depending on its value returned,
                # publish and wait a time until the following publish, or fail and wait a time
                # until an available place appears
                for i in range(amount):
                    if not self.marketplace.publish(producer_id, product):
                        time.sleep(self.republish_wait_time)
                    else:
                        time.sleep(wait_time)
