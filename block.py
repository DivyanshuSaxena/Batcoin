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
        if arity != 0:
            self.merkle.construct_tree(self.transactions)
        self.compute_hash()

    @classmethod
    def genesis_block(cls):
        """Ctor for creating the genesis block

        Returns:
            Block instance
        """
        return cls([], 0)

    def to_json(self):
        """Return a json dump of the block to send out to other nodes

        Returns:
            str
        """
        blk_dict = {
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle.root.value,
            "arity": self.merkle.arity,
            "transactions": self.transactions
        }
        return blk_dict

    def set_nonce(self, nonce):
        """Used when the nonce has been calculated by some other node

        Args:
            nonce (int)
        """
        self.nonce = nonce
        # Re-compute hash since the nonce has changed
        self.compute_hash()

    def compute_hash(self):
        """Compute and return the hash of block instance

        Returns:
            String: hash of the current block header
        """
        block_header = ''.join(
            [str(self.nonce), self.prev_hash, self.merkle.root.value])
        self.hash = SHA.new(block_header.encode('utf-8')).hexdigest()
        return self.hash

    def get_hash(self):
        """Return the saved hash of the current instance

        Returns:
            str
        """
        if not self.hash:
            return self.compute_hash()
        return self.hash