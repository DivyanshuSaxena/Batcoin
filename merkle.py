"""Implement Merkle Trees to be used for blockchain protocol"""
import json
from Crypto.Hash import SHA


class MerkleNode:
    """A single node in a Merkle tree of given arity"""
    def __init__(self, arity):
        """MerkleNode Ctor

        Args:
            arity (int): Arity of the Merkle Tree
        """
        self.value = ''
        self.parent = None
        self.children = [None] * arity

    def set_value(self, value):
        self.value = value

    def set_parent(self, parent):
        self.parent = parent

    def set_child(self, index, child):
        self.children[index] = child

    def compute_value(self):
        """Compute and set the hash of the current instance"""
        combined = ''.join([child.value for child in self.children])
        c_digest = SHA.new(combined.encode('utf-8')).hexdigest()
        self.value = c_digest


class MerkleTree:
    def __init__(self, arity):
        """MerkleTree Ctor

        Args:
            arity (int): Arity of the Merkle Tree
        """
        self.arity = arity
        self.root = None

    def construct_tree(self, transactions):
        """Construct the non-leaf nodes and set the root

        Args:
            transactions (List): List of JSON dumps of transactions in Merkle Tree
        """
        curr_level = []

        for t in transactions:
            node = MerkleNode(self.arity)
            t_string = json.dumps(transactions, sort_keys=True)
            t_digest = SHA.new(t_string.encode('utf-8')).hexdigest()
            node.set_value(t_digest)
            curr_level.append(node)

        # Create non-leaf nodes
        while len(curr_level) != 1:
            next_level = []

            index = 0
            while index < len(curr_level):
                new_node = MerkleNode(self.arity)
                for _in in range(self.arity):
                    # Duplicate last node if a child doesn't exist
                    if index + _in >= len(curr_level):
                        new_node.set_child(_in, curr_level[-1])
                    else:
                        new_node.set_child(_in, curr_level[index + _in])
                        curr_level[index + _in].set_parent(new_node)
                new_node.compute_value()

                next_level.append(new_node)
                index += self.arity

            curr_level = next_level

        # Set the Merkle Root
        self.root = curr_level[0]
