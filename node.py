"""Implementation to simulate the working of a node in a Blockchain network"""
from block import *
from blockchain import *

class Node:
    def __init__(self, node_id, is_miner, block_size):
        """Node Ctor

        Args:
            node_id (int): Node id with which the node is to be created
            is_miner (bool): Whether the given node must function as a miner
            block_size (int): Number of transactions in a single block
        """
        self.id = node_id
        self.is_miner = is_miner
        self.blockchain = Blockchain(block_size)