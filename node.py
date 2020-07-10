"""Implementation to simulate the working of a node in a Blockchain network"""
import time
import json
import base64
import random
import Crypto
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from datetime import datetime
from block import *
from blockchain import *

debug_level = 'info'


def print_level(dl, node_id, string):
    """Print statements as per debug level
    
    Arguments:
        dl {String} -- Debug Level - basic/info/debug
        node_id {Integer} -- Node id for which statement is to be printed
        string {String} -- Print statement
    """
    global debug_level
    if dl == 'basic':
        print('[NOTE ' + str(node_id) + ']: ' + string)
    if debug_level == 'info' and dl == 'info':
        print('[INFO ' + str(node_id) + ']: ' + string)
    if debug_level == 'debug':
        if dl == 'info':
            print('[INFO ' + str(node_id) + ']: ' + string)
        elif dl == 'debug':
            print('[DEBUG ' + str(node_id) + ']: ' + string)


class Node:
    def __init__(self, node_id, private_key, is_miner, block_size, keys,
                 queues):
        """Node Ctor

        Args:
            node_id (int): Node id with which the node is to be created
            private_key (_RSAObj): RSA Obj for the current node instance
            is_miner (bool): Whether the given node must function as a miner
            block_size (int): Number of transactions in a single block
            keys (multiprocessing.Array[str]): List of public keys for all nodes
            queues (List): List of Queues for each node on the network
        """
        self.id = node_id
        self.private_key = private_key
        self.is_miner = is_miner
        self.keys = keys
        self.queues = queues
        self.bc = Blockchain(block_size, difficulty=2)

    def __get_key(self, node_id):
        """Get the public key associated with node `node_id`

        Args:
            node_id (int)

        Returns:
            str
        """
        key_str = self.keys[node_id].key
        return key_str

    def __node_stub(self, message, payload):
        """Stub process to send broadcast message to all nodes

        Args:
            message (str): 'TRANSACTION/BLOCK'
            payload (str): Hash of the transaction or the block
        """
        obj = {'sender': self.id, 'message': message, 'pl': payload}
        print_level('debug', self.id, 'Broadcasting: ' + payload)
        for q in self.queues:
            q.put(obj)

    def __sign(self, message, pl):
        """Digitally sign the transaction with private key

        Args:
            message (str): TRANSACTION/BLOCK
            pl (dict): Python dict of the payload

        Returns:
            str: JSON dump of digitally signed transaction
        """
        # Perform a two step hashing and signing procedure
        pl_string = json.dumps(pl, sort_keys=True)
        pl_digest = SHA.new(pl_string.encode('utf-8'))

        # Digitally sign the transaction digest with the sender's private key
        signer = PKCS1_v1_5.new(self.private_key)
        signature = signer.sign(pl_digest)

        # Crypto generates Byte-string - convert into unicode string for JSON dump
        signature_string = base64.b64encode(signature).decode('utf-8')

        # Return the combined transaction
        if message == 'TRANSACTION':
            payload = {"tx": pl, "signature": signature_string}
        else:
            payload = {"blk": pl, "signature": signature_string}
        return json.dumps(payload, sort_keys=True)

    def start_operation(self, timeout):
        """Start operation of the blockchain node and end at timeout

        Args:
            timeout (int): Time for which the node runs (in seconds)
        """
        print_level('basic', self.id, 'Operation started')

        start_time = time.time()
        curr_time = time.time()

        # Start with initial balance
        last_transaction = start_time
        transaction = self.transaction_to_self('INIT')
        self.__node_stub('TRANSACTION', transaction)

        while curr_time - start_time < timeout:
            # Read from the queue
            try:
                obj = self.queues[self.id].get(False, timeout=1)
                print_level('debug', self.id,
                            'Received message from node ' + str(obj['sender']))
                if self.authenticate(obj):
                    if obj['message'] == 'TRANSACTION':
                        print_level('debug', self.id, 'Received TRANSACTION')
                        # bc.add_transaction returns if the current blockchain is ready for mining.
                        mine_ready = self.bc.add_transaction(obj['pl'])
                        if mine_ready and self.is_miner:
                            print_level('debug', self.id, 'Ready for mining')
                            next_block = self.mine()
                            self.__node_stub('BLOCK', next_block)
                    else:
                        # Received a mined block from another node.
                        print_level('debug', self.id, 'Received BLOCK')
                        result = self.bc.add_block(obj['pl'])
                        print_level(
                            'debug', self.id, 'Add BLOCK from ' +
                            str(obj['sender']) + ' result: ' + str(result))
            except:
                pass

            # Generate transactions at the rate of 1 per second
            curr_time = time.time()
            if curr_time - last_transaction > 1:
                print_level('debug', self.id,
                            'Ready to send another transaction')
                transaction = self.generate()
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
            str: JSON dump of digitally signed transaction
        """
        if tx_type == 'INIT':
            amount = self.bc.init_amt
        elif tx_type == 'MINE':
            amount = self.bc.reward
        else:
            amount = amt
        receiver_key = self.__get_key(self.id)
        timestamp = datetime.now()
        tx = {
            "type": tx_type,
            "receiver": receiver_key,
            "amount": amount,
            "timestamp": str(timestamp)
        }

        return self.__sign('TRANSACTION', tx)

    def generate(self):
        """Return a newly created transaction
        
        Returns:
            str: JSON dump of digitally signed transaction
        """
        receiver_id = random.randint(0, len(self.keys) - 1)
        receiver_key = self.__get_key(receiver_id)
        amount = random.randint(1, 10)
        timestamp = datetime.now()
        tx = {
            "type": 'MINE',
            "receiver": receiver_key,
            "amount": amount,
            "timestamp": str(timestamp)
        }

        return self.__sign('TRANSACTION', tx)

    def authenticate(self, obj):
        """Authenticate if the transaction/block was actually sent by the receiver

        Args:
            obj (dict): Python dict of object read from queue

        Returns:
            Boolean
        """
        sender_node = obj['sender']
        pl_string = obj['pl']

        sender_key = self.__get_key(sender_node)
        key_obj = RSA.importKey(sender_key)
        payload = json.loads(pl_string)

        if payload['signature']:
            if obj['message'] == 'TRANSACTION' and payload['tx']:
                raw_payload = payload['tx']
            elif obj['message'] == 'BLOCK' and payload['blk']:
                raw_payload = payload['blk']
            else:
                return False

            # Authenticate that the transaction was actually made by the sender
            signature = base64.b64decode(payload['signature'])
            rt_string = json.dumps(raw_payload, sort_keys=True)
            rt_digest = SHA.new(rt_string.encode('utf-8'))

            verifier = PKCS1_v1_5.new(key_obj)
            if verifier.verify(rt_digest, signature):
                print_level('debug', self.id, 'Message authenticated')
                return True

        # Neither is the object an authentic block nor a transaction
        print_level('debug', self.id, 'Message unauthenticated')
        return False

    def mine(self):
        """Mine the transactions accumulated until now. Called by Miner nodes.

        Returns:
            str: JSON dump of digitally signed block
        """
        # Generate a transaction to self as a reward for mining
        reward_tx = self.transaction_to_self('MINE')
        self.bc.add_transaction(reward_tx)

        print_level('info', self.id, 'Starting POW for new block')
        next_block = self.bc.proof_of_work()

        print_level('info', self.id,
                    'Found nonce. Hash: ' + next_block.get_hash())
        block_json = next_block.to_json()
        return self.__sign('BLOCK', block_json)