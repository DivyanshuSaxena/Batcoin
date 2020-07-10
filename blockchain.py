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
        # Verify if the block can be added on top of chain
        if self.last_hash != blk['prev_hash']:
            return None

        # Verify if POW done on the block
        block_header = ''.join(
            [str(blk['nonce']), blk['prev_hash'], blk['merkle_root']])
        block_hash = SHA.new(block_header.encode('utf-8')).hexdigest()

        target = 2**(160 - self.difficulty)
        if int(block_hash, 16) > target:
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
        
        Returns:
            boolean: True if block could be added.
        """
        blk = json.loads(block)['blk']
        next_block = self.validate_block(blk)

        if next_block:
            # Add block and update last hash
            self.last_hash = next_block.get_hash()
            self.chain.append(next_block)
            return True

        return False

    def add_transaction(self, transaction):
        """Validate the transaction and add it to the unconfirmed block

        Args:
            transaction (string): Digitally signed JSON dump of the transaction
        
        Returns:
            boolean: whether the Blockchain is ready for mining
        """
        # Validate the transaction
        tx = json.loads(transaction)['tx']
        is_legal = self.validate_transaction(tx)

        if is_legal:
            self.transactions.append(tx)
            if len(self.transactions) == self.block_length:
                return True

        # No block to add yet
        return False

    def proof_of_work(self):
        """Compute the proof of work of the accumulated transactions

        Returns:
            Block: The created block along with POW
        """
        block = Block(self.transactions[:self.block_length], 2, self.last_hash)
        self.transactions = self.transactions[self.block_length:]

        max_nonce = 2**32
        target = 2**(160 - self.difficulty)

        # Compute the nonce of the block
        computed_hash = block.compute_hash()
        while int(computed_hash, 16) > target:
            block.nonce += 1
            computed_hash = block.compute_hash()

        return block
