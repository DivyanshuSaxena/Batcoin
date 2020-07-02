"""Implementation to simulate the working of a node in a Blockchain network"""
import time
import json
import random
import Crypto
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from datetime import datetime
from block import *
from blockchain import *


class Node:
    def __init__(self, node_id, is_miner, block_size, keys, queues):
        """Node Ctor

        Args:
            node_id (int): Node id with which the node is to be created
            is_miner (bool): Whether the given node must function as a miner
            block_size (int): Number of transactions in a single block
            keys (Array): List of public keys for all nodes
            queues (List): List of Queues for each node on the network
        """
        self.id = node_id
        self.is_miner = is_miner
        self.keys = keys
        self.queues = queues
        self.bc = Blockchain(block_size)

    def __node_stub(self, message, payload):
        """Stub process to send broadcast message to all nodes

        Args:
            message (str): 'TRANSACTION/BLOCK'
            payload (str): Hash of the transaction or the block
        """
        obj = {'sender': self.id, 'message': message, 'pl': payload}
        for q in self.queues:
            q.put(obj)

    def __sign(self, tx):
        """Digitally sign the transaction with private key

        Args:
            tx (dict): Python dict of transaction

        Returns:
            str: JSON dump of digitally signed transaction
        """
        # Perform a two step hashing and signing procedure
        t_string = json.dumps(tx, sort_keys=True)
        t_digest = SHA.new(t_string.encode('utf-8'))

        # Digitally sign the transaction digest with the sender's private key
        signer = PKCS1_v1_5.new(self.private_key)
        signature = signer.sign(t_digest)

        # Return the combined transaction
        transaction = {"tx": tx, "signature": signature}
        return json.dumps(transaction, sort_keys=True)

    def generate_wallet(self, init_amt):
        """Generate a public and private key for the current node, which will act
        as the wallet for the node

        Returns:
            str: public key of the node
        """
        random_gen = Crypto.Random.new().read

        # Create a private-public key pair of 1024 bits each
        private_key = RSA.generate(1024, random_gen)
        public_key = private_key.publickey()

        # Save the private key and add the public key to the shared arary
        self.private_key = private_key

        # Generate first transaction to self
        self.transaction_to_self('INIT')
        return public_key

    def start_operation(self, timeout):
        """Start operation of the blockchain node and end at timeout

        Args:
            timeout (int): Time for which the node runs (in ms)
        """
        start_time = time.time()
        curr_time = time.time()
        last_transaction = start_time

        while curr_time - start_time > timeout:
            # Read from the queue
            obj = self.queues[self.id].get()
            if obj['message'] == 'TRANSACTION':
                if self.authenticate_transaction(obj['sender'], obj['pl']):
                    self.bc.add_transaction(obj['pl'])
            else:
                # Received a mined block from another node. TODO: Validate it
                self.validate_block(obj['pl'])

            # Generate transactions at the rate of 1 per second
            curr_time = time.time()
            if curr_time - last_transaction > 1000:
                transaction = generate()
                last_transaction = curr_time

                # Broadcast transaction
                self.__node_stub('TRANSACTION', transaction)

            curr_time = time.time()
        print('[INFO]: Completed execution for ' + str(self.id))

    def transaction_to_self(self, tx_type, amt=0):
        """Create a digitally signed transaction to self. Required for initial
        wallet amount, reward for mining and change to self (future UTXO impl)

        Args:
            tx_type (str): INIT/TRANSFER/MINE
            amt (int, optional): Amount. Defaults to 0.

        Returns:
            str: JSON dump of digitally signed transaction to self
        """
        if tx_type == 'INIT':
            amount = self.bc.init_amt
        elif tx_type == 'MINE':
            amount = self.bc.reward
        else:
            amount = amt
        receiver_key = self.keys[self.id]
        timestamp = datetime.now()
        tx = {
            "type": tx_type,
            "receiver": receiver_key,
            "amount": amount,
            "timestamp": str(timestamp)
        }

        return self.__sign(tx)

    def generate(self):
        """Return a newly created transaction
        
        Returns:
            str: JSON dump of digitally signed transaction
        """
        receiver_id = random.randint(0, len(self.keys) - 1)
        receiver_key = self.keys[receiver_id]
        amount = random.randint(1, 10)
        timestamp = datetime.now()
        tx = {
            "type": 'MINE',
            "receiver": receiver_key,
            "amount": amount,
            "timestamp": str(timestamp)
        }

        return self.__sign(tx)

    def authenticate_transaction(self, sender_node, t_string):
        """Authenticate if the transaction was actually sent by the receiver

        Args:
            sender_node (int): Node id of the sender
            t_string (str): Digitally signed string of the transaction

        Returns:
            Boolean
        """
        sender_key = self.keys[sender_node]
        transaction = json.loads(t_string)

        if transaction['tx'] and transaction['signature']:
            raw_transaction = transaction['tx']

            # Authenticate that the transaction was actually made by the sender
            rt_string = json.dumps(raw_transaction, sort_keys=True)
            rt_digest = SHA.new(rt_string.encode('utf-8'))

            verifier = PKCS1_v1_5.new(sender_key)
            if verifier.verify(rt_digest, transaction['signature']):
                return True

        return False