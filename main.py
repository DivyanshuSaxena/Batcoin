"""Main file for spwaning nodes and running experiments"""
# Arguments:
#
# 1: Number of nodes on the bitcoin network
# 2: Block size to create the block
# 3: Timeout (in seconds) after which nodes stop operation

import os
import sys
import Crypto
from node import Node
from Crypto.PublicKey import RSA
from ctypes import Structure, c_wchar_p
from multiprocessing import Process, Queue, Array


class PublicKey(Structure):
    _fields_ = [('key', c_wchar_p)]


def generate_wallet():
    """Generate a public and private key for the current node, which will act
    as the wallet for the node

    Returns:
        str: public key of the node
    """
    random_gen = Crypto.Random.new().read

    # Create a private-public key pair of 1024 bits each
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()

    return private_key, public_key


def spawn_process(node_id, private_key, is_miner, block_size, keys, queues,
                  timeout):
    """Spawn a new Node process. Arguments same as those required by Node ctor"""
    Crypto.Random.atfork()
    node = Node(node_id, private_key, is_miner, block_size, keys, queues)

    # Start the operation of the node
    node.start_operation(timeout * 1000)


if __name__ == '__main__':
    num_nodes = int(sys.argv[1])
    block_size = int(sys.argv[2])
    timeout = int(sys.argv[3])
    num_miners = 5

    # Attach a queue for each node
    queues = []
    for _ in range(num_nodes):
        q = Queue()
        queues.append(q)

    # Generate the pair of public and private keys for each of the nodes
    keys = []
    for _ in range(num_nodes):
        private_key, public_key = generate_wallet()
        keys.append((private_key, public_key))

    processes = []
    public_keys = Array(PublicKey, [
        PublicKey(keytup[1].exportKey('PEM').decode('utf-8'))
        for keytup in keys
    ])

    for node_id in range(num_nodes):
        p = Process(target=spawn_process,
                    args=(node_id, keys[node_id][0], node_id < num_miners,
                          block_size, public_keys, queues, timeout))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # Completed execution till `timeout` milliseconds
    print('[INFO]: Completed execution till `timeout` milliseconds')