"""Main file for spwaning nodes and running experiments"""

import os
import sys
from node import Node
from multiprocessing import Process, Queue


def spawn_process(node_id, is_miner, block_size, queues, timeout):
    node = Node(node_id, queues, is_miner, block_size)
    node.start_operation(timeout)


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

    processes = []
    for node_id in range(num_nodes):
        p = Process(target=spawn_process,
                    args=(node_id, node_id < num_miners, block_size, queues,
                          timeout))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # Completed execution till `timeout` milliseconds
    print('[INFO]: Completed execution till `timeout` milliseconds')