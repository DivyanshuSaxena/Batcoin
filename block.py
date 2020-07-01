"""Implementation to represent a single block in the custom blockchain"""

import json
from hashlib import sha256

class Block:
    def __init__(self, block_id, transactions, timestamp, prev_hash=""):
        """Block Ctor

        Args:
            block_id (int): Unique ID to identify a block
            transactions (List): Each transaction is of type JSON
            timestamp (str): Timestamp of generating the block.
            prev_hash (str): Hash of the previous block on the blockchain.
        """
        self.id = block_id
        self.transactions = transactions
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.nonce = 0
        self.hash = ''

    @classmethod
    def genesis_block(cls, timestamp):
        """Ctor for creating the genesis block

        Args:
            timestamp (str): time of creating the genesis block

        Returns:
            Block instance
        """
        return cls(0, [], timestamp)

    def set_nonce(self, nonce):
        """Set the nonce of the block after the node completes the Proof of Work

        Args:
            nonce ([type]): [description]
        """
        self.nonce = nonce

    def compute_hash(self):
        """Compute and return the hash of block instance

        Returns:
            String: hash of the current block
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        self.hash = sha256(block_string.encode()).hexdigest()
        return self.hash

    def get_hash(self):
        """Return the saved hash of the current instance

        Returns:
            str
        """
        if len(self.hash) == 0:
            return self.compute_hash()
        return self.hash