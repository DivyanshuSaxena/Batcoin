"""Implementation of the blockchain protocol which will be used by all the nodes on the BatCoin network"""
import json
from block import *
from datetime import datetime


class Blockchain:
    def __init__(self, block_size, difficulty):
        self.block_length = block_size
        self.difficulty = difficulty
        self.transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        first_block = Block.genesis_block()
        self.last_hash = first_block.get_hash()
        self.chain.append(first_block)

    def add_transaction(self, transaction):
        """Validate the transaction and add it to the unconfirmed block

        Args:
            transaction (string): Digitally signed JSON dump of the transaction
        """
        # Validate the transaction
        is_legal = True

        if is_legal:
            self.transactions.append(transaction)
            if len(self.transactions) == self.block_length:
                next_block = self.proof_of_work()
                self.chain.append(next_block)

    def proof_of_work(self):
        """Compute the proof of work of the accumulated transactions

        Returns:
            Block: The created block along with POW
        """
        block = Block(self.transactions, self.last_hash)
        
        # Compute the nonce of the block
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return block
