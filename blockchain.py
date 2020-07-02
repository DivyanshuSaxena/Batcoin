"""Implementation of the blockchain protocol which will be used by all the nodes on the BatCoin network"""
import json
from block import *
from datetime import datetime


class Blockchain:
    def __init__(self, block_size, difficulty):
        self.block_length = block_size
        self.difficulty = difficulty
        self.init_amt = 10
        self.reward = 2
        self.transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        first_block = Block.genesis_block()
        self.last_hash = first_block.get_hash()
        self.chain.append(first_block)

    def validate_block(self, blk):
        """Validate the block JSON

        Args:
            blk (dict): Block object to validate (Format in README)

        Returns:
            Object: None if not valid, otherwise returns the next block
        """
        # Validate the hash
        block_header = ''.join(
            [str(blk['nonce']), blk['prev_hash'], blk['merkle_root']])
        block_hash = SHA.new(block_header.encode('utf-8')).hexdigest()
        if not block_hash.startswith('0' * self.difficulty):
            return None

        # Validate the transactions in the block, by re-constructing the merkle tree
        # Currently, validates that the transactions in the block give the correct merkle root
        # TODO: Also validate if the transactions are valid
        next_block = Block(blk['transactions'], blk['arity'], blk['prev_hash'])
        if next_block.merkle.root.value == blk['merkle_root']:
            next_block.set_nonce(blk['nonce'])
            return next_block

        # Validation failed
        return None

    def validate_transaction(self, tx):
        """Validate the transaction JSON

        Args:
            tx (dict): Transaction object to validate

        Returns:
            boolean: True if legal else False
        """
        if tx['type'] == 'INIT':
            # Validate the initial transaction
            if tx['amount'] != self.init_amt or len(self.chain) > 1:
                return False
            for transaction in self.transactions:
                if transaction['receiver'] == tx['receiver']:
                    return False

        # TODO: Add more checks for non init transactions
        return True

    def add_block(self, block):
        """Validate the block and add it to the chain, if valid

        Args:
            block (string): Digitally signed JSON dump of the transaction
        """
        blk = json.loads(block)['blk']
        next_block = self.validate_block(blk)

        if next_block:
            self.chain.append(next_block)

    def add_transaction(self, transaction):
        """Validate the transaction and add it to the unconfirmed block

        Args:
            transaction (string): Digitally signed JSON dump of the transaction
        
        Returns:
            Block: the newly created block
        """
        # Validate the transaction
        tx = json.loads(transaction)['tx']
        is_legal = self.validate_transaction(tx)

        if is_legal:
            self.transactions.append(tx)
            if len(self.transactions) == self.block_length:
                next_block = self.proof_of_work()
                self.chain.append(next_block)
                return next_block

        # No block to add yet
        return None

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
