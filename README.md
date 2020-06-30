# Batcoin

Custom cryptocurrency implementation using Python

## Nodes

The nodes of the blockchain are simulated using the Python Multiprocessing module.

## Transactions

The transactions for Batcoin are stored as JSON files. The format is as follows:

```json
{
  "amount" : "amount",
  "sender" : "sender_id",
  "receiver" : "receiver_id",
  "timestamp" : "timestamp"
}
```

## Network Messages

The Batcoin nodes communicate with each other using network messages which carry the necessary information. These communications work in a broadcast format currently, for the sake of simplicity. The format of these Network messages is as follows:

```json
{
  "sender": sender_node,
  "message": transaction_or_block,
  "pl": payload
}
```
