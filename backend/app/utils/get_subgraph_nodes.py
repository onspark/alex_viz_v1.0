from collections import deque

def get_subgraph_nodes(edges, target_node_id):
    # Convert edge list to a dictionary for faster lookups
    graph = {}
    for edge in edges:
        if edge['from'] in graph:
            graph[edge['from']].append(edge['to'])
        else:
            graph[edge['from']] = [edge['to']]
    
    # Initialize a queue with the to node and a set to track visited nodes
    queue = deque([target_node_id])
    visited = set([target_node_id])
    
    # Perform BFS
    while queue:
        current_node = queue.popleft()
        for neighbor in graph.get(current_node, []): 
            if neighbor not in visited:
                visited.add(neighbor) # Add unvisited connected nodes to the queue
                queue.append(neighbor)
    
    # Return the visited nodes as the subgraph under the to node
    return list(visited)

if __name__ == "__main__":
    # Example usage
    edges = [
        {'from': 'node1', 'to': 'node2'},
        {'from': 'node1', 'to': 'node3'},
        {'from': 'node2', 'to': 'node4'},
        {'from': 'node3', 'to': 'node5'},
        {'from': 'node4', 'to': 'node6'},
        {'from': 'node5', 'to': 'node7'},
        # Add more edges as needed
    ]
    
    target_node_id = 'node1'

    subgraph_nodes = get_subgraph_nodes(edges, target_node_id)
    print(subgraph_nodes)
