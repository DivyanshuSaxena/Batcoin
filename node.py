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

    def generate_wallet(self):
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
                # Received a mined block from another node. Validate it
                self.validate(obj['pl'])

            # Generate transactions at the rate of 1 per second
            curr_time = time.time()
            if curr_time - last_transaction > 1000:
                transaction = generate()
                last_transaction = curr_time

                # Broadcast transaction
                self.__node_stub('TRANSACTION', transaction)

            curr_time = time.time()
        print('[INFO]: Completed execution for ' + str(self.id))

    def generate(self):
        """Return a newly created transaction

        Returns:
            str: Digitally signed transaction
        """
        receiver = random.randint(0, len(self.keys) - 1)
        receiver_key = self.keys[receiver]
        amount = random.randint(1, 10)
        timestamp = datetime.now()
        transaction = {
            "receiver": receiver_key,
            "amount": amount,
            "timestamp": str(timestamp)
        }

        # Perform a two step hashing and signing procedure
        t_string = json.dumps(transaction, sort_keys=True)
        t_digest = SHA.new(t_string.encode('utf-8'))

        # Digitally sign the transaction digest with the sender's private key
        signer = PKCS1_v1_5.new(self.private_key)
        signature = signer.sign(t_digest)

        # Return the combined transaction
        transaction['signature'] = signature
        return json.dumps(transaction, sort_keys=True)

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

        raw_transaction = {}
        if transaction['sender']:
            raw_transaction['sender'] = transaction['sender']
        else:
            return False

        if transaction['amount']:
            raw_transaction['amount'] = transaction['amount']
        else:
            return False
        
        if transaction['timestamp']:
            raw_transaction['timestamp'] = transaction['timestamp']
        else:
            return False

        # Authenticate that the transaction was actually made by the sender
        rt_string = json.dumps(raw_transaction, sort_keys=True)
        rt_digest = SHA.new(rt_string.encode('utf-8'))

        verifier = PKCS1_v1_5.new(sender_key)
        if verifier.verify(rt_digest, transaction['signature']):
            return True
        return False