"""Read the logs and print where a node forked"""
# Arguments:
#
# 1: Number of nodes on the bitcoin network
import sys

num_nodes = int(sys.argv[1])
logs_dir = './logs/'
chains = []
max_length = 0

for node in range(num_nodes):
    node_log_file = logs_dir + 'log_' + str(node) + '.txt'
    with open(node_log_file) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    rev_content = content[::-1]
    rev_index = rev_content.index('Chain:')

    curr_index = len(content) - rev_index
    blk_hash = content[curr_index]
    final_chain = [blk_hash]

    while blk_hash.endswith(','):
        curr_index += 1
        blk_hash = content[curr_index]
        final_chain.append(blk_hash)

    final_chain = final_chain[::-1]
    print('Chain length for node ' + str(node) + ': ' + str(len(final_chain)))
    max_length = max(max_length, len(final_chain))
    chains.append(final_chain)

# Generate the printing chains
print_chains = []
for index in range(max_length):
    print_chains.append([])
    for node in range(num_nodes):
        if (len(chains[node]) > index):
            print_chains[index].append(chains[node][index][:7])
        else:
            print_chains[index].append('')

# Print the forking chains
for index in range(max_length):
    hash_set = set(print_chains[index])
    indices_set = []
    for ele in hash_set:
        indices = [str(i) for i, x in enumerate(print_chains[index]) if x == ele]
        indices_set.append(indices)
    
    print('\t\t'.join([','.join(_indices) for _indices in indices_set]))
    print('\t\t'.join(hash_set))