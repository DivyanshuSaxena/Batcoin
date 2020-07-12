"""Implementation to simulate the working of a node in a Blockchain network"""
import os
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

debug_level = 'basic'


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


class IllegalBlockException(Exception):
    pass


class Node:
    def __init__(self,
                 node_id,
                 private_key,
                 is_miner,
                 block_size,
                 keys,
                 queues,
                 is_dishonest=False,
                 dishonest_master=-1):
        """Node Ctor

        Args:
            node_id (int): Node id with which the node is to be created
            private_key (_RSAObj): RSA Obj for the current node instance
            is_miner (bool): Whether the given node must function as a miner
            block_size (int): Number of transactions in a single block
            keys (multiprocessing.Array[str]): List of public keys for all nodes
            queues (List): List of Queues for each node on the network
            is_dishonest (bool, optional): If the node colludes with the dishonest master. Defaults to False.
            dishonest_master (int, optional): Node Id of the dishonest master. Defaults to -1.
        """
        self.id = node_id
        self.private_key = private_key
        self.is_miner = is_miner
        self.is_dishonest = is_dishonest
        self.dishonest_master = dishonest_master
        self.keys = keys
        self.queues = queues
        self.next_block = None  # Latest mined block
        self.bc = Blockchain(block_size, difficulty=16)
        print_level('basic', self.id, 'Dishonest: ' + str(self.is_dishonest))

        # Initialize log file
        log_dir = './logs/'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = log_dir + 'log_' + str(self.id) + '.txt'
        self.logfile = open(log_file, 'w')

        # Log Initial state
        self.__log('STATE', message='Initial State:')

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
            payload (str): JSON dump of the transaction or the block
        """
        obj = {'sender': self.id, 'message': message, 'pl': payload}
        print_level('debug', self.id, 'Broadcasting: ' + payload)
        if message == 'TRANSACTION':
            # Log the generated transaction
            self.__log('TRANSACTION', 'Broadcasting transaction:', payload)

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

    def __log(self, log_type, message='', payload=''):
        """Write message `log` onto logs of this node

        Args:
            log_type (str): STATE/TRANSACTION
            message (str, optional): Message to print before log. Defaults to ''.
            payload (str, optional): Transaction to log. Defaults to ''.
        """
        if log_type == 'STATE':
            # Print the state of the node
            self.logfile.write(message + '\nSTATE:\n' + str(self.bc) + '\n\n')
        else:
            self.logfile.write(
                message + '\nTRANSACTION:\n' +
                json.dumps(json.loads(payload), indent=2, sort_keys=True) +
                '\n\n')

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
                            # Make the block ready for transmission
                            self.next_block = self.mine()
                    elif (not self.is_dishonest) or (
                            self.is_dishonest
                            and obj['sender'] == self.dishonest_master):
                        # Received a mined block from another node.
                        print_level('debug', self.id, 'Received BLOCK')
                        result = self.bc.add_block(obj['pl'])
                        print_level(
                            'debug', self.id, 'Add BLOCK from ' +
                            str(obj['sender']) + ' result: ' + str(result))

                        # Log if any changes to blockchain state
                        if result:
                            self.next_block = None
                            self.__log(
                                'STATE',
                                'Status after block added to blockchain')
                        else:
                            raise IllegalBlockException
            except:
                if self.next_block:
                    print_level('info', self.id, 'Sending self-mined block')
                    self.__node_stub('BLOCK', self.next_block)
                    # Reset next_block once sent
                    self.next_block = None

            # Generate transactions at the rate of 1 per second
            curr_time = time.time()
            if curr_time - last_transaction > 0.2:
                print_level('debug', self.id,
                            'Ready to send another transaction')
                transaction = self.generate()
                last_transaction = curr_time

                # Broadcast transaction
                if transaction is not None:
                    self.__node_stub('TRANSACTION', transaction)

            curr_time = time.time()
        while not self.queues[self.id].empty():
            try:
                self.queues[self.id].get(timeout=0.001)
            except:
                pass
        self.queues[self.id].close()
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
            "sender": self.id,
            "receiver": receiver_key,
            "amount": amount,
            "timestamp": str(timestamp),
            "receiver_id": self.id,
            "change": 0,
            "inputs": []
        }

        return self.__sign('TRANSACTION', tx)

    def generate(self):
        """Return a newly created transaction
        
        Returns:
            str: JSON dump of digitally signed transaction
        """
        receiver_id = random.randint(0, len(self.keys) - 1)
        receiver_key = self.__get_key(receiver_id)
        unspentSelfTransactions, walletAmount = self.getUnspentSelfTransactions()
        if walletAmount==0:
            return None
        amount = random.randint(1, walletAmount)
        transactionsDigests, change= self.select_outputs_greedy(unspentSelfTransactions, amount)
        inputs = [x.tx_hash for x in transactionsDigests]
        timestamp = datetime.now()
        tx = {
            "type": 'TRANSFER',
            "sender": self.id,
            "receiver": receiver_key,
            "amount": amount,
            "timestamp": str(timestamp),
            "receiver_id": receiver_id,
            "change": change,
            "inputs": inputs
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
        tx_json = json.loads(self.transaction_to_self('MINE'))['tx']

        print_level('basic', self.id, 'Starting POW for new block')
        next_block = self.bc.proof_of_work(tx_json)

        print_level('basic', self.id,
                    'Found nonce. Hash: ' + next_block.get_hash())
        block_json = next_block.to_json()
        return self.__sign('BLOCK', block_json)

    def getUnspentSelfTransactions(self):
        answer = []
        sumAmount = 0
        for transactionHash in self.bc.transactionsDict:
            transactionReceiversData = self.bc.transactionsDict[transactionHash]["receiverData"]
            for transactionReceiverData in transactionReceiversData:
                receiver_id = transactionReceiverData[0]
                amount = transactionReceiverData[1]
                isSpent = transactionReceiverData[2]
                isConfirmed = transactionReceiverData[3]

                if receiver_id==self.id and amount!=0 and isConfirmed and (not isSpent):
                    output_info = OutputInfo(transactionHash, amount)
                    answer.append(output_info)
                    sumAmount += amount
        return answer, sumAmount

    def select_outputs_greedy(self, unspent, min_value):
        # Taken from https://www.oreilly.com/library/view/mastering-bitcoin/9781491902639/ch05.html
        # Fail if empty.
        if not unspent:
            return None
        # Partition into 2 lists.
        lessers = [utxo for utxo in unspent if utxo.value < min_value]
        greaters = [utxo for utxo in unspent if utxo.value >= min_value]
        key_func = lambda utxo: utxo.value
        if greaters:
            # Not-empty. Find the smallest greater.
            min_greater = min(greaters)
            change = min_greater.value - min_value
            return [min_greater], change
        # Not found in greaters. Try several lessers instead.
        # Rearrange them from biggest to smallest. We want to use the least
        # amount of inputs as possible.
        lessers.sort(key=key_func, reverse=True)
        result = []
        accum = 0
        for utxo in lessers:
            result.append(utxo)
            accum += utxo.value
            if accum >= min_value:
                change = accum - min_value
                return result, "Change: %d Satoshis" % change
        # No results found.
        return None, 0


class OutputInfo:

    def __init__(self, tx_hash, value):
        self.tx_hash = tx_hash
        self.value = value

    def __repr__(self):
        return "<%s: with %s Satoshis>" % (self.tx_hash,
                                             self.value)