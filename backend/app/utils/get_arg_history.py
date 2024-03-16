from app.logger import logger

def get_discourse_history(arguments, target_node, attackable_nodes, depth:int=3):
    '''
    Retrieves discourse history for a given node
    '''
    logger.debug(f"target_node in get_discourse_history : {target_node} =============================")
    nodes = arguments['nodes']
    edges = arguments['edges']
    logger.debug(f"attackable_nodes in get_discourse_history : {attackable_nodes} =============================")

    target_node_id = target_node['node_id']
    # Initialize a list to hold the IDs of connected nodes
    connected_node_ids = set()
    
    # Look for edges that are connected to the target node
    for edge in edges:
        if edge['from'] == target_node_id or edge['to'] == target_node_id:
            # If the target node is at the 'from', we add the 'to' and vice versa
            connected_node_id = edge['to'] if edge['from'] == target_node_id else edge['from']
            # Remove leading "-" if present (indicating an attack)
            connected_node_ids.add(connected_node_id.strip("-"))
        if len(connected_node_ids) >= depth:
            break  # Stop if we have found 3 or more connected nodes

    # Find the actual node details from the nodes list 
    nearest_nodes = [node for node in nodes if node['node_id'] in connected_node_ids][:depth] #For safety
    # Add defeated status to the nodes that are not in the attackable_nodes
    nearest_nodes_updated = [
                {**node, 'status': 'accepted' if node['node_id'] in attackable_nodes else 'defeated'} for node in nearest_nodes
            ]
    
    discourse_history = "\n".join([f"({node['node_type']}): {node['text']} [{node['status']}]" for node in nearest_nodes_updated])

    return discourse_history  # Return up to 3 nearest nodes 