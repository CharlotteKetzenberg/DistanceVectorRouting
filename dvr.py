""""
Columbia University - CSEE 4119 Computer Network
Assignment 3 - Distance Vector Routing

dvr.py - the Distance Vector Routing (DVR) program announces its distance vector to its neighbors and 
updates its routing table based on the received routing vectors from its neighbors
"""
import sys
import socket
import time

class NetworkInterface():
    """
    DO NOT EDIT.
    
    Provided interface to the network. In addition to typical send/recv methods,
    it also provides a method to receive an initial message from the network, which
    contains the costs to neighbors. 
    """
    def __init__(self, network_port, network_ip):
        """
        Constructor for the NetworkInterface class.

        Parameters:
            network_port : int
                The port the network is listening on.
            network_ip : str
                The IP address of the network.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((network_ip, network_port))
        self.init_msg = self.sock.recv(4096).decode() # receive the initial message from the network
        # Set a reasonable timeout for non-blocking receives
        self.sock.settimeout(0.5)
        
    def initial_costs(self): 
        """
        Return the initial message received from the network in following format:
        <node_id>. <neighbor_1>:<cost_1>,...,<neighbor_n>:<cost_n>

        node_id is the unique identifier for this node, i.e., dvr.py instance. 
        Neighbor_i is the unique identifier for direct neighbor nodes. All identifiers
        and costs are specified in the topology file.
        """
        return self.init_msg
    
    def send(self, message):
        """
        Send a message to all direct neigbors.

        Parameters:
            message : bytes
                The message to send.
        
        Returns:
            None
        """
        message_len = len(message)
        packet = message_len.to_bytes(4, byteorder='big') + message
        self.sock.sendall(packet)
    
    def recv(self, length):
        """
        Receive a message from neighbors. Behaves exactly like socket.recv()

        Parameters:
            length : int
                The length of the message to receive.
        
        Returns:
            bytes
                The received message.
        """
        return self.sock.recv(length)
    
    def close(self):
        """
        Close the socket connection with the network.
        """
        self.sock.close()

def format_distance_vector(node_id, distance_vector):
    """
    Format the distance vector for broadcasting to neighbors.
    
    Parameters:
        node_id: str
            The ID of this node
        distance_vector: dict
            Dictionary mapping destination node_id to cost
            
    Returns:
        bytes
            The formatted distance vector as bytes
    """
    # Format: "<your_node_id>|dest1:cost1,dest2:cost2,..."
    vector_parts = []
    for dest, cost in distance_vector.items():
        vector_parts.append(f"{dest}:{cost}")
    
    formatted_vector = f"{node_id}|{','.join(vector_parts)}"
    return formatted_vector.encode()

def format_distance_vector_with_poison_reverse(node_id, distance_vector, routing_table, target_neighbor):
    """
    Format the distance vector with poison reverse for a specific neighbor.
    
    Parameters:
        node_id: str
            The ID of this node
        distance_vector: dict
            Dictionary mapping destination node_id to cost
        routing_table: dict
            Dictionary mapping destination node_id to next hop
        target_neighbor: str
            The neighbor this vector will be sent to
            
    Returns:
        bytes
            The formatted distance vector as bytes with poison reverse applied
    """
    # Create a copy of the distance vector to modify
    poisoned_vector = distance_vector.copy()
    
    # Apply poison reverse: if we route to a destination through this neighbor,
    # tell the neighbor that our distance to that destination is infinity (999)
    for dest, next_hop in routing_table.items():
        if next_hop == target_neighbor:
            poisoned_vector[dest] = 999  # Infinity (for practical purposes)
    
    # Format: "<your_node_id>|dest1:cost1,dest2:cost2,..."
    vector_parts = []
    for dest, cost in poisoned_vector.items():
        vector_parts.append(f"{dest}:{cost}")
    
    formatted_vector = f"{node_id}|{','.join(vector_parts)}"
    return formatted_vector.encode()

def parse_received_vector(message):
    """
    Parse a received distance vector message.
    
    Parameters:
        message: bytes
            The received message
            
    Returns:
        tuple (str, dict)
            The sender node_id and their distance vector
    """
    # Expected format: "sender_id|dest1:cost1,dest2:cost2,..."
    try:
        message_str = message.decode()
        
        # Split the message to get sender ID and vector parts
        if '|' not in message_str:
            return None, {}  # Invalid format
            
        sender_id, vector_part = message_str.split('|', 1)
        
        # Parse the distance vector
        sender_vector = {}
        if vector_part:
            for pair in vector_part.split(','):
                if ':' in pair:
                    dest, cost_str = pair.split(':')
                    # Validate that cost is a number
                    try:
                        cost = int(cost_str)
                        sender_vector[dest] = cost
                    except ValueError:
                        # Skip invalid cost values
                        pass
        
        return sender_id, sender_vector
    except Exception:
        # Return empty results for any parsing error
        return None, {}

def update_tables(node_id, sender_id, sender_vector, distance_vector, routing_table, neighbors):
    """
    Update distance vector and routing table based on received vector.
    Implements the Bellman-Ford algorithm.
    
    Parameters:
        node_id: str
            This node's ID
        sender_id: str
            The sender node's ID
        sender_vector: dict
            The sender's distance vector
        distance_vector: dict
            This node's current distance vector
        routing_table: dict
            This node's current routing table
        neighbors: dict
            Dictionary of direct neighbors and their costs
            
    Returns:
        bool
            True if any distances changed, False otherwise
    """
    changed = False
    
    # Cost to reach the sender node
    cost_to_sender = neighbors.get(sender_id)
    if cost_to_sender is None:
        return False  # Sender is not a direct neighbor
    
    # For each destination in sender's vector
    for dest, dest_cost in sender_vector.items():
        # Skip if destination is this node itself
        if dest == node_id:
            continue
            
        # Skip if the cost is infinity (999 in our implementation)
        if dest_cost >= 999:
            continue
            
        # Calculate potential new cost = cost to sender + sender's cost to destination
        potential_cost = cost_to_sender + dest_cost
        
        # If we don't know this destination yet, or the new route is better
        current_cost = distance_vector.get(dest, float('inf'))
        if dest not in distance_vector or potential_cost < current_cost:
            # Update distance vector
            distance_vector[dest] = potential_cost
            # Update routing table with sender as next hop
            routing_table[dest] = sender_id
            changed = True
    
    return changed

def log_state(node_id, distance_vector, routing_table, log_file):
    """
    Log the current state of the distance vector and routing table.
    
    Parameters:
        node_id: str
            This node's ID
        distance_vector: dict
            This node's current distance vector
        routing_table: dict
            This node's current routing table
        log_file: file
            The log file to write to
    """
    # Format: "<node_1>:<cost_1>:<next_hop_1> ... <node_n>:<cost_n>:<next_hop_n>"
    log_entries = []
    
    # Sort the destinations for consistent output
    for dest in sorted(distance_vector.keys()):
        cost = distance_vector[dest]
        next_hop = routing_table.get(dest, "unknown")
        log_entries.append(f"{dest}:{cost}:{next_hop}")
    
    log_line = " ".join(log_entries)
    log_file.write(log_line + "\n")
    log_file.flush()  # IMPORTANT: ensures content is written immediately

if __name__ == '__main__':
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 dvr.py <network_ip> <network_port>")
        sys.exit(1)
        
    network_ip = sys.argv[1]  # the IP address of the network
    try:
        network_port = int(sys.argv[2])  # the port the network is listening on
    except ValueError:
        print("Error: network_port must be an integer")
        sys.exit(1)
 
    # Initialize network interface and parse initial data
    net_interface = NetworkInterface(network_port, network_ip)
    init_costs = net_interface.initial_costs() 
    print(f"Initial costs: {init_costs}")

    # Parse node_id and neighbor information from initial costs
    parts = init_costs.split('. ')
    node_id = parts[0]  # Extract your node ID (everything before the period)
    neighbors_info = parts[1] if len(parts) > 1 else ""  # Extract neighbor information

    # Initialize data structures
    distance_vector = {}  # Maps destination node_id -> cost
    routing_table = {}    # Maps destination node_id -> next_hop node_id
    neighbors = {}        # Maps neighbor_id -> direct cost

    # Set distance to self as 0
    distance_vector[node_id] = 0
    routing_table[node_id] = node_id  # Next hop to self is self

    # Parse and initialize information for direct neighbors
    if neighbors_info:
        neighbor_pairs = neighbors_info.split(',')
        for pair in neighbor_pairs:
            if ':' in pair:
                neighbor_id, cost = pair.split(':')
                cost = int(cost)
                
                # Update neighbors dictionary
                neighbors[neighbor_id] = cost
                
                # Update distance vector with direct neighbor costs
                distance_vector[neighbor_id] = cost
                
                # Update routing table - next hop to a direct neighbor is the neighbor itself
                routing_table[neighbor_id] = neighbor_id

    # Create log file named with the node's ID
    log_file = open(f"log_{node_id}.txt", "w")
    
    # Log the initial state
    log_state(node_id, distance_vector, routing_table, log_file)
    
    # Main DVR loop
    try:
        while True:
            # Broadcast distance vector to all neighbors
            # Use poison reverse for each neighbor separately
            for neighbor_id in neighbors:
                poisoned_message = format_distance_vector_with_poison_reverse(
                    node_id, distance_vector, routing_table, neighbor_id
                )
                net_interface.send(poisoned_message)
            
            # Receive and process incoming distance vectors
            try:
                message = net_interface.recv(4096)
                
                if message:
                    # Parse the received vector
                    sender_id, sender_vector = parse_received_vector(message)
                    
                    if sender_id and sender_id in neighbors:
                        # Update tables based on received vector
                        changed = update_tables(
                            node_id, sender_id, sender_vector, 
                            distance_vector, routing_table, neighbors
                        )
                        
                        # If tables changed, log the new state
                        if changed:
                            log_state(node_id, distance_vector, routing_table, log_file)
            
            except socket.timeout:
                # No message received within timeout period, continue with the loop
                pass
            
            # Brief sleep to control update rate
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        # Handle graceful termination when Ctrl+C is pressed
        print(f"Node {node_id} shutting down...")
        
    finally:
        # Make sure resources are properly closed
        net_interface.close()
        if log_file:
            log_file.close()
        print(f"Node {node_id} terminated")