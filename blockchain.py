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

        # Chain format - (block, prev_id_block)
        self.chain = []
        self.main = -1
        # Orphans format - (block)
        self.orphans = []
        self.create_genesis_block()

    def __str__(self):
        chain = 'Chain: \n'
        main_chain = []
        curr_index = self.main
        while (curr_index != -1):
            main_chain.append(self.chain[curr_index][0])
            curr_index = self.chain[curr_index][1]
        blockchain = ',\n'.join([block.get_hash() for block in main_chain])
        return chain + blockchain

    def __last_hash(self):
        return self.chain[self.main][0].get_hash()

    def __get_chain_length(self, index):
        """Get length of chain traversing back from index

        Args:
            index (int)

        Returns:
            int: Length
        """
        curr_index = index
        length = 0
        while (curr_index != -1):
            curr_index = self.chain[curr_index][1]
            length += 1
        return length

    def __append_to_chain(self, block):
        """Either append block to chain or add in orphans

        Args:
            block (Block)
        """
        # Special clause for first block addition
        if self.main == -1:
            print('Adding first block')
            self.chain.append((block, -1))
            self.main += 1
        else:
            found_parent = False
            for index in range(len(self.chain)):
                p_index = len(self.chain) - index - 1
                parent = self.chain[p_index][0]
                if parent.get_hash() == block.prev_hash:
                    self.chain.append((block, p_index))
                    if p_index == self.main:
                        self.main += 1
                    else:
                        # Check if the length of new branch is more, swap branch
                        if self.__get_chain_length(
                                self.main) < self.__get_chain_length(
                                    len(self.chain) - 1):
                            self.main = len(self.chain) - 1
                    found_parent = True
                    break
            if not found_parent:
                # Add in orphan pool
                self.orphans.append(block)
            else:
                # Check if some block in orphan pool is a child
                for orphan in self.orphans:
                    if block.get_hash() == orphan.get_hash():
                        self.__append_to_chain(orphan)
                        break

    def create_genesis_block(self):
        first_block = Block.genesis_block()
        self.__append_to_chain(first_block)

    def validate_block(self, blk):
        """Validate the block JSON

        Args:
            blk (dict): Block object to validate (Format in README)

        Returns:
            Object: None if not valid, otherwise returns the next block
        """
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
            self.__append_to_chain(next_block)
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

    def proof_of_work(self, reward_tx):
        """Compute the proof of work of the accumulated transactions

        Args:
            reward_tx (string): Digitally signed JSON of the reward transaction

        Returns:
            Block: The created block along with POW
        """
        transactions = self.transactions[:self.block_length]
        self.transactions = self.transactions[self.block_length:]
        transactions.append(reward_tx)
        block = Block(transactions, 2, self.__last_hash())

        max_nonce = 2**32
        target = 2**(160 - self.difficulty)

        # Compute the nonce of the block
        computed_hash = block.compute_hash()
        while int(computed_hash, 16) > target:
            block.nonce += 1
            computed_hash = block.compute_hash()

        return block
