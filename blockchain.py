"""Implementation of the blockchain protocol which will be used by all the nodes on the BatCoin network"""
import json
from block import *
from datetime import datetime


class Blockchain:
    def __init__(self, block_size):
        self.block_length = block_size
        self.transactions = []
        self.chain = []
        self.create_genesis_block()
        self.last_hash = self.chain[-1].get_hash()

    def create_genesis_block(self):
        first_block = Block.genesis_block(str(datetime.now()))
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
        block = Block(0, self.transactions, str(datetime.now()), self.last_hash)
        # Compute the nonce of the block
        nonce = 0
        block.set_nonce(nonce)
        return block
