"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Lock
import unittest
from logging.handlers import RotatingFileHandler
import logging
import time

class TestMarketplaceMethods(unittest.TestCase):
    """
    Class that represents the unittest. It helps us to test the functions
    functionality from Marketplace.
    """

    # creates a markeplace new instance, to avoid the repeating code
    def setUp(self):
        self.marketplace = Marketplace(5)

    def test_register_producer(self):
        self.assertEqual(self.marketplace.register_producer(), 0)
        self.assertNotEqual(self.marketplace.register_producer(), 2)

    def test_publish(self):
        self.assertFalse(self.marketplace.publish(0, 'Tea'))
        self.marketplace.register_producer()
        self.assertTrue(self.marketplace.publish(0, 'Tea'))
        i = 0
        while i < 4:
            self.marketplace.publish(0, 'Tea')
            i += 1
        self.assertFalse(self.marketplace.publish(0, 'Tea'))

    def test_new_cart(self):
        self.assertEqual(self.marketplace.new_cart(), 0)
        self.assertNotEqual(self.marketplace.new_cart(), 2)

    def test_add_to_cart(self):
        self.marketplace.register_producer()
        self.marketplace.new_cart()
        self.marketplace.publish(0, 'Tea')
        self.assertTrue(self.marketplace.add_to_cart(0, 'Tea'))
        self.marketplace.publish(0, 'Tea')
        self.assertFalse(self.marketplace.add_to_cart(1, 'Tea'))
        self.assertFalse(self.marketplace.add_to_cart(0, 'Coffee'))

    def test_remove_to_cart(self):
        self.marketplace.register_producer()
        self.marketplace.new_cart()
        self.marketplace.publish(0, 'Coffee')
        self.marketplace.add_to_cart(0, 'Coffee')
        self.assertFalse(self.marketplace.remove_from_cart(1, 'Coffee'))
        self.assertFalse(self.marketplace.remove_from_cart(0, 'Tea'))
        self.assertTrue(self.marketplace.remove_from_cart(0, 'Coffee'))

    def test_place_order(self):
        self.marketplace.register_producer()
        self.marketplace.new_cart()
        self.marketplace.publish(0, 'Tea')
        self.marketplace.publish(0, 'Coffee')
        self.marketplace.add_to_cart(0, 'Tea')
        self.marketplace.add_to_cart(0, 'Coffee')
        self.assertFalse(self.marketplace.place_order(1))
        self.assertEqual(len(self.marketplace.place_order(0)), 2)

class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer


        :type producers_listed_items: dict
        :param producers_listed_items: the dictionary who keeps all the pairs composed by
                                    producers and their listed products (key->list)

        :type carts: list
        :param carts: the list who keeps for each consumer a list with all the products
            that he reserved for buying and its producer id (carts[cons_id] : [(product, prod_id)])

        :type register_producer_lock: Lock
        :param register_producer_lock: the Lock that ensures the program concurency, protecting
                        the multiple access of the threads in the function of registering a producer

        :type create_new_cart_lock: Lock
        :param create_new_cart_lock: the Lock that ensures the program concurency, protecting the
                            multiple access of the threads in the function of creating a cart

        """

        self.queue_size_per_producer = queue_size_per_producer
        self.producers_listed_items = {}
        self.carts = []
        self.register_producer_lock = Lock()
        self.create_new_cart_lock = Lock()

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        file_handler = RotatingFileHandler('marketplace.log', maxBytes=10000000, backupCount=1)
        file_handler.setFormatter(logging.Formatter("%(asctime)s  -  %(levelname)s  - %(message)s"))
        logger.addHandler(file_handler)
        logging.Formatter.converter = time.gmtime

        self.logger = logger

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """

        # For every new producer, we add a key with his id at the end of the dictionary,which keeps
        # the producers and a list for each with the products that they produced;
        # also,at the start every producer wil have an empty list
        self.register_producer_lock.acquire()
        producer_id = len(self.producers_listed_items)
        self.producers_listed_items[producer_id] = []
        self.register_producer_lock.release()
        self.logger.info('Succesfull registered producer %d', producer_id)
        return producer_id

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace
        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        producer_id_cast = int(producer_id)

        # check if the producer doesn't already exist in the 'marketplace'
        if producer_id_cast not in self.producers_listed_items.keys():
            self.logger.error('Doesnt exist producer nr. %d!', producer_id_cast)
            return False

        # check if the producer exceeded the limit to produce in marketplace
        if len(self.producers_listed_items[producer_id_cast]) >= self.queue_size_per_producer:
            self.logger.error('Limit to publish exceeded by producer nr. %d', producer_id_cast)
            return False

        # add the product in the list of the producer from 'marketplace'
        self.producers_listed_items[producer_id_cast].append(product)
        self.logger.info('Producer nr. %d published product %s', producer_id_cast, str(product))
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        # in the carts list, add always at her final, an empty list, in which
        # the consumer will store his wanted products
        self.create_new_cart_lock.acquire()
        cart_id = len(self.carts)
        self.carts.append([])
        self.create_new_cart_lock.release()

        self.logger.info('New cart created! Cart number: %d', cart_id)
        return cart_id

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """

        # flag to keep if one of the edge case is available
        add_flag = False

        # check if the cart already exists in carts list
        if cart_id >= len(self.carts):
            self.logger.error('Did not add product %s in the cart %d', str(product), cart_id)
            return False

        # search the wanted product in the 'marketplace'
        # search in every producer's list where each keeps what products he had added before
        for item in self.producers_listed_items.items():
            for prod in item[1]:
                if prod == product:
                    # if we find the product, we add it (with product's producer id) to the
                    # specific cart and we remove it from its producer list
                    self.carts[cart_id].append((item[0], product))
                    self.producers_listed_items[item[0]].remove(product)
                    add_flag = True
                    break
            if add_flag is True:
                break

        # if flag is false, it means that the product wanted to be added in cart is not listed
        if add_flag is False:
            self.logger.error('No products available to add in the cart %d', cart_id)
            return False

        self.logger.info('Product %s added to the cart nr. %d', str(product), cart_id)
        return True

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        remove_flag = False
        if cart_id >= len(self.carts):
            self.logger.error('Invalid cart_id nr: %d', cart_id)
            return False

        for item in self.carts[cart_id]:
            if item[1] == product:
                self.producers_listed_items[item[0]].append(product)
                self.carts[cart_id].remove(item)
                remove_flag = True
                break

        if remove_flag is False:
            self.logger.error("Product %s was not removed from cart nr. %d!",
                              str(product), cart_id)
            return False

        self.logger.info('Product %s was removed from cart nr. %d', str(product), cart_id)
        return True


    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """

        # check if the cart already exists in carts list
        if cart_id >= len(self.carts):
            self.logger.error('Cart nr. %d doesnt exist', cart_id)
            return False

        # create a list which willbe returned with all the products that the consumer have
        # in his cart
        cart_products = []
        for product in self.carts[cart_id]:
            cart_products.append(product[1])

        self.logger.info('New order from cart nr. %d', cart_id)
        return cart_products
    