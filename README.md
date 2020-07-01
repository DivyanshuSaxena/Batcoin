# Batcoin

Custom cryptocurrency implementation using Python

## Nodes

The nodes of the blockchain are simulated using the Python Multiprocessing module.

## Transactions

The transactions for Batcoin are stored as JSON objects. Transactions also hold the cryptographic digests The format is as follows:

```json
{
  "amount" : "amount",
  "receiver" : "receiver_key",
  "timestamp" : "timestamp",
  "signature" : "signature of the remaining json object"
}
```

### Confirmation of transactions

Any newly generated transaction is added to the unconfirmed pool of transactions at each of the nodes. Any subsequent transactions which might be invalid because of this transaction are then dropped. A transaction gets confirmed once it gets added to the blockchain, in the form of a block.

### Validating transactions

Each transaction sends a certain node from one wallet to another. Each node, independently keeps a list of wallets and their balances, and verifies the transaction based on that list.

## Network Messages

The Batcoin nodes communicate with each other using network messages which carry the necessary information. These communications work in a broadcast format currently, for the sake of simplicity. The format of these Network messages is as follows:

```json
{
  "sender": "sender_node",
  "message": "TRANSACTION/BLOCK",
  "pl": "payload"
}
```
