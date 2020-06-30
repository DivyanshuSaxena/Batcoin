"""Implementation to simulate the working of a node in a Blockchain network"""
import time
from block import *
from blockchain import *


class Node:
    def __init__(self, node_id, is_miner, block_size, queues):
        """Node Ctor

        Args:
            node_id (int): Node id with which the node is to be created
            is_miner (bool): Whether the given node must function as a miner
            block_size (int): Number of transactions in a single block
            queues (List): List of Queues for each node on the network
        """
        self.id = node_id
        self.is_miner = is_miner
        self.queues = queues
        self.bc = Blockchain(block_size)

    def __node_stub(self, message, payload):
        obj = {'sender': self.id, 'message': message, 'pl': payload}
        for q in self.queues:
            q.put(obj)

    def start_operation(self, timeout):
        """Start operation of the blockchain node and end at timeout

        Args:
            timeout (int): Time for which the node runs (in ms)
        """
        start_time = time.time()
        curr_time = time.time()
        last_transaction = start_time

        while curr_time - start_time > timeout:
            # Read from the queue
            obj = self.queues[self.id].get()
            if obj['message'] == 'TRANSACTION':
                self.bc.add_transaction(obj['pl'])
            else:
                # Received a mined block from another node. Validate it
                self.validate(obj['pl'])

            # Generate transactions at the rate of 1 per second
            curr_time = time.time()
            if curr_time - last_transaction > 1000:
                transaction = generate()
                last_transaction = curr_time
                
                # Broadcast transaction
                self.__node_stub('TRANSACTION', transaction)

            curr_time = time.time()
        print('[INFO]: Completed execution for ' + str(self.id))

    def generate(self):
        """Return a newly created transaction

        Returns:
            str: Digitally signed transaction
        """
        transaction = ''
        return transaction