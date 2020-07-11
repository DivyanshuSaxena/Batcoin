# Batcoin

Custom cryptocurrency implementation using Python

## Usage

Use the `main.py` file to spawn nodes, generate wallet key-pairs, share public keys, and initial transactions.

```console
>>> python main.py <num-nodes> <block-size> <timeout-in-seconds> <num-miners> <num-dishonest-nodes>
```

Sample Usage:

```console
>>> python main.py 4 4 10 2 1
```

### Dishonest Nodes

The number of dishonest nodes can be set using Command Line Interface. The dishonest nodes, collude to agree upon the history mined by a single master.
By default, node 0 is labelled as the Dishonest Master Node. Only one node among all miners can be set as dishonest, in the current implementation. There can be as many dishonest, non-miner nodes however.

### Debugging

The project utilizes function `print_level()` for printing at three different logging levels: basic/info/debug.

## Nodes

The nodes of the blockchain are simulated using the Python Multiprocessing module.

### Network Messages

The Batcoin nodes communicate with each other using network messages which carry the necessary information. These communications work in a broadcast format currently, for the sake of simplicity. The format of these Network messages is as follows:

```json
{
  "sender": "sender_node",
  "message": "TRANSACTION/BLOCK",
  "pl": "payload"
}
```

## Transactions

The transactions for Batcoin are stored as JSON objects. Transactions also hold the cryptographic digests The format is as follows:

```json
{
  "tx": {
    "type" : "INIT/TRANSFER/MINE",
    "amount" : "amount",
    "receiver" : "receiver_key",
    "sender" : "sender_id",
    "timestamp" : "timestamp"
  },
  "signature" : "signature of the remaining json object"
}
```

### Confirmation of transactions

Any newly generated transaction is added to the unconfirmed pool of transactions at each of the nodes. Any subsequent transactions which might be invalid because of this transaction are then dropped. A transaction gets confirmed once it gets added to the blockchain, in the form of a block.

### Validating transactions

Each transaction sends a certain node from one wallet to another. Each node, independently keeps a list of wallets and their balances, and verifies the transaction based on that list.

## Blocks

The blocks for Batcoin follow the following message format:

```json
{
  "blk": {
    "prev_hash" : "prev_hash",
    "nonce" : "nonce",
    "merkle_root" : "merkle_root",
    "arity" : "arity",
    "transactions" : [
      // Transactions
    ],
  },
  "signature": "signature",
}
```

## Initialization

At the initialization of the blockchain protocol, each node generates a genesis block. Since the contents of the genesis block are same, irrespective of the node, genesis blocks with the exact same hashes are generated in all of the nodes.

Further, each node gets to generate a transaction providing itself `initial_amount` of coins at the start for doing transactions.

## Todo

- [X] Proof of work implementation for Nodes
- [X] Create and broadcast blocks over network
- [X] Validation of blocks
- [ ] Implementation of UTXO transactions needed for validating transactions
- [X] Dishonest nodes
- [ ] Smart Contracts
- [ ] Experiments
