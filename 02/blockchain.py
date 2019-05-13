import hashlib
import  json
import requests
from time import time

from flask import Flask, jsonify, request
from uuid import uuid4

from urllib.parse import urlparse

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash = '1', proof = 100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new block in blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of the previous block
        :return: <dict> New block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.pending_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):

        # Adds a new transaction to the list of transactions
        """
        Creates a new transaction to go into the next mined block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """

        self.pending_transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount
        })

        return self.last_block['index'] + 1

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. E.g. 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(last_block)
            print(block)
            print("\n-----------------\n")

            # Check that the hash of the previous block is correct
            if block["previous_hash"] != self.hash(last_block):
                print("previous hash does not match")
                return False

            if not self.valid_proof(block):
                print("Block proof of work is invalid")
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflict(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network
        :return: True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains Longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = request.get(f'http://{node}/chain')
            if response.status_code == 200 :
                length = response.json()['length']
                chain = response.json()['chain']
                # Check if the Length is Longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we're discovered a new, valid chain, Longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False;

    @staticmethod
    def hash(block):

        # Hashes a block
        """
        Creates a SHA-256 hash of a block
        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is ordered, or we will have inconsistent hashes
        block_string = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(block_string).hexdigest()


    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]

    @staticmethod
    def proof_of_work(block):
        """
        Proof-of-Work algorithm.
        Iterate the "proof" field until the conditions are satisfied.
        :param block: <dict>\
        """

        while not Blockchain.valid_proof(block):
            block["proof"] += 1

    @staticmethod
    def valid_proof(block):
        """
        The Proof-of-Work conditions.
        Check if the hash of the block startes with 4 zeroes.
        Higher difficulty == more zeroes, lower difficulty == loss
        :param block: <dict>
        """
        # 채굴한 것이 빨리 로딩 된다면 난이도가 쉽다는 뜻이니 0갯수를 늘려서 난이도를 조절한다.
        return Blockchain.hash(block)[:4] == "0000"

# Instance our node
app = Flask(__name__)

# Generate a globally unique address for this node
node_idetifier = str(uuid4()).replace('-', '')

# Instance the blockchain
blockchain = Blockchain()

@app.route('/mine', methods = ['GET'])
def mine():
    # Add our mining reward
    # Sender "0" means new coin.
    blockchain.new_transaction(
        sender = "0",
        recipient = node_idetifier,
        amount = 1
    )

    # Make the new block and mine it
    block = blockchain.new_block(0)
    blockchain.proof_of_work(block)

    response = {
        "message": "New block mined",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"]
    }

    return jsonify(response), 200

@app.route('/transactions/new', methods = ['POST'])
def new_transaction():
    values = request.get_json()

    if not values:
        return "Missing body", 400

    required = ["sender", "recipient", "amount"]

    if not all(k in values for k in required):
        return "Missing values", 400

    index = blockchain.new_transaction(values["sender"], values["recipient"], values["amount"])

    response = {"message": f"Transaction will be added to block {index}"}
    return jsonify(response), 201

@app.route('/chain', methods = ['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods = ['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods = ['GET'])
def consensus():
    replaced = blockchain.resolve_conflict()

    if replaced:
        response = {
            'message': "Our chain was replaced",
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': "Our chain is authoritative",
            'chain': blockchain.chain
        }

    return jsonify(response), 200

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help="port to listen on")
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)

