"""Implementation to represent a single block in the custom blockchain"""
import json
from Crypto.Hash import SHA
from merkle import MerkleTree


class Block:
    def __init__(self, transactions, arity, prev_hash=''):
        """Block Ctor

        Args:
            transactions (List): Each transaction is of type JSON
            arity (int): Arity of the Merkle Tree to hold the block
            prev_hash (str): Hash of the previous block on the blockchain.
        """
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.nonce = 0
        self.merkle = MerkleTree(arity)

        # Contruct tree and compute hash
        self.merkle.construct_tree(self.transactions)
        self.compute_hash()

    @classmethod
    def genesis_block(cls):
        """Ctor for creating the genesis block

        Returns:
            Block instance
        """
        return cls([], 0)

    def set_nonce(self, nonce):
        """Set the nonce of the block after the node completes the Proof of Work

        Args:
            nonce ([type]): [description]
        """
        self.nonce = nonce

    def compute_hash(self):
        """Compute and return the hash of block instance

        Returns:
            String: hash of the current block header
        """
        block_header = ''.join(
            [self.prev_hash, str(self.nonce), self.merkle.root])
        self.hash = SHA.new(block_header.encode('utf-8')).hexdigest()

    def get_hash(self):
        """Return the saved hash of the current instance

        Returns:
            str
        """
        if not self.hash:
            self.compute_hash()
        return self.hash