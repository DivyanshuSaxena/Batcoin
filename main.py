"""Main file for spwaning nodes and running experiments"""
# Arguments:
#
# 1: Number of nodes on the bitcoin network
# 2: Block size to create the block
# 3: Timeout (in seconds) after which nodes stop operation
# 4: Number of miners in the blockchain system
# 5: Number of dishonest nodes in the blockchain system
# 6: Arity of Merkel Tree
# 7: Difficulty of POW

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
                  is_dishonest, dishonest_master, arity, difficulty, timeout):
    """Spawn a new Node process. Arguments same as those required by Node ctor"""
    Crypto.Random.atfork()
    if is_dishonest:
        node = Node(node_id, private_key, is_miner, block_size, keys, queues,
                    arity, difficulty, is_dishonest, dishonest_master)
    else:
        node = Node(node_id, private_key, is_miner, block_size, keys, queues,
                    arity, difficulty)

    # Start the operation of the node
    node.start_operation(timeout)


if __name__ == '__main__':
    num_nodes = int(sys.argv[1])
    block_size = int(sys.argv[2])
    timeout = int(sys.argv[3])
    num_miners = int(sys.argv[4])
    num_dishonest = int(sys.argv[5])
    arity = int(sys.argv[6])
    difficulty = int(sys.argv[7])
    dishonest_master = 0 if num_dishonest > 0 else -1

    # Check if input is valid:
    if num_miners + num_dishonest > num_nodes:
        print('Incorrect params: num_miners + num_dishonest <= num_nodes')

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
        is_miner = node_id < num_miners
        is_dishonest = (num_dishonest > 0 and node_id == 0) or (
            node_id >= num_miners and node_id - num_miners + 1 < num_dishonest)
        p = Process(target=spawn_process,
                    args=(node_id, keys[node_id][0], is_miner, block_size,
                          public_keys, queues, is_dishonest, dishonest_master,
                          arity, difficulty, timeout))
        processes.append(p)
        p.start()

    # for p in processes:
    #     p.join()

    # Completed execution till `timeout` milliseconds
    print('[INFO]: Completed execution till `timeout` milliseconds')