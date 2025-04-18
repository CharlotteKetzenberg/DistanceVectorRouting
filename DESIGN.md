# Distance Vector Routing - Design Document

This document describes the design and implementation details of my Distance Vector Routing (DVR) protocol solution.

## Protocol Overview

I've implemented a distance vector routing protocol that allows nodes to discover optimal paths to all destinations in a network by exchanging routing information with their neighbors. The implementation follows the Bellman-Ford distributed algorithm and includes split horizon with poison reverse to prevent routing loops.

## Data Structures

### Distance Vector
A dictionary that maps destination node IDs to the current best-known cost to reach them:
```python
distance_vector = {
    'A': 0,  # Cost to self is always 0
    'B': 5,  # Cost to reach node B is 5
    'C': 9   # Cost to reach node C is 9
}
```

### Routing Table
A dictionary that maps destination node IDs to the next hop node ID that should be used to forward packets to that destination:
```python
routing_table = {
    'A': 'A',  # Next hop to self is self
    'B': 'B',  # Next hop to B is directly to B
    'C': 'B'   # Next hop to C is through B
}
```

### Neighbors
A dictionary that maps neighbor node IDs to the direct link cost:
```python
neighbors = {
    'B': 5,  # Direct link to B costs 5
    'D': 7   # Direct link to D costs 7
}
```

## Packet Format

### Distance Vector Message
Distance vector messages are formatted as strings and encoded as bytes for transmission. The format is:
```
<sender_node_id>|<dest1>:<cost1>,<dest2>:<cost2>,...
```

For example:
```
A|A:0,B:5,C:9,D:14
```

This indicates that node A can reach:
- Itself (A) with cost 0
- Node B with cost 5
- Node C with cost 9
- Node D with cost 14

### Poison Reverse Implementation
For split horizon with poison reverse, I modify the distance vector before sending to each neighbor. If node A routes to destination C through neighbor B, then when sending updates to B, node A reports an "infinite" cost (999) to C:

```
# Normal vector from A:
A|A:0,B:5,C:9,D:14

# Poisoned vector when sending to B (if routes to C and D go through B):
A|A:0,B:5,C:999,D:999
```

## Protocol Operation

### Initialization
1. Connect to the network simulator
2. Receive node ID and direct neighbor information
3. Initialize distance vector, routing table, and neighbors dictionary
4. Set distance to self as 0
5. Set direct neighbor costs in distance vector and routing table
6. Log initial state

### Main Loop
1. For each neighbor, create a poisoned distance vector and broadcast it
2. Receive incoming distance vectors
3. For each received vector:
   - Parse sender ID and their distance vector
   - Update local tables using the Bellman-Ford equation
   - If any distances changed, log the new state
4. Repeat

## Key Algorithms

### Update Tables (Bellman-Ford Algorithm)
```python
def update_tables(node_id, sender_id, sender_vector, distance_vector, routing_table, neighbors):
    changed = False
    cost_to_sender = neighbors.get(sender_id)
    
    for dest, dest_cost in sender_vector.items():
        # Skip self and "infinity" costs
        if dest == node_id or dest_cost >= 999:
            continue
            
        # Calculate potential new cost
        potential_cost = cost_to_sender + dest_cost
        
        # If the new route is better
        current_cost = distance_vector.get(dest, float('inf'))
        if dest not in distance_vector or potential_cost < current_cost:
            # Update distance vector and routing table
            distance_vector[dest] = potential_cost
            routing_table[dest] = sender_id
            changed = True
    
    return changed
```

### Poison Reverse Implementation
```python
def format_distance_vector_with_poison_reverse(node_id, distance_vector, routing_table, target_neighbor):
    # Create a copy of the distance vector to modify
    poisoned_vector = distance_vector.copy()
    
    # Apply poison reverse
    for dest, next_hop in routing_table.items():
        if next_hop == target_neighbor:
            poisoned_vector[dest] = 999  # Infinity
    
    # Format the vector for transmission
    vector_parts = []
    for dest, cost in poisoned_vector.items():
        vector_parts.append(f"{dest}:{cost}")
    
    formatted_vector = f"{node_id}|{','.join(vector_parts)}"
    return formatted_vector.encode()
```

## Logging

I implemented a logging system that writes to a file named `log_<node_id>.txt`. Each time the distance vector changes, a new line is written to the log in the format:
```
<destination1>:<cost1>:<next_hop1> <destination2>:<cost2>:<next_hop2> ...
```

For example:
```
A:0:A B:5:B C:9:B D:12:B
```

This shows the current routing information for all known destinations, sorted alphabetically.

## Error Handling

I've implemented the following error handling mechanisms:

1. **Socket Timeouts**: Using a non-blocking receive with timeouts to avoid hanging
2. **Graceful Termination**: Properly closing resources (sockets, files) when the program exits
3. **Invalid Message Handling**: Safely parsing received messages and handling invalid formats
4. **Infinity Representation**: Using 999 as a practical representation of "infinity" for poison reverse

## Design Decisions

### Split Horizon with Poison Reverse
I chose to implement split horizon with poison reverse rather than simple split horizon because it provides stronger protection against routing loops and faster convergence after topology changes. While it increases message size slightly, the benefits in preventing count-to-infinity problems outweigh this cost.

### Individual Poisoned Messages
Instead of sending a single distance vector to all neighbors, I create a separate poisoned vector for each neighbor. This ensures that routes are properly poisoned for the specific neighbor receiving the update, preventing routing loops effectively.

### Periodic Updates
I chose to implement periodic updates rather than triggered updates for simplicity. The protocol sends updates to neighbors at regular intervals (every 0.3 seconds after processing), which ensures that routing information propagates through the network without complex state tracking.

### String-Based Message Format
I chose a simple string-based message format for distance vectors rather than a binary format for readability and ease of debugging. While less efficient for large networks, this format is suitable for the scope of this implementation and makes the protocol behavior easier to understand and troubleshoot.

## Limitations and Future Improvements

1. **Efficiency**: The current implementation sends full distance vectors in each update. In a production environment, I would implement incremental updates to reduce bandwidth usage.

2. **Convergence Speed**: The periodic update approach may slow convergence in large networks. A triggered update mechanism would improve responsiveness to topology changes.

3. **Metrics**: The implementation only supports integer cost metrics. Supporting more complex metrics (bandwidth, delay, reliability) would make the protocol more versatile.

4. **Security**: The current implementation has no authentication or integrity checking. In a real-world scenario, these would be essential to prevent routing attacks.

5. **Dynamic Link Cost Updates**: The implementation doesn't support changing link costs after initialization. Adding this capability would make the protocol more robust to changing network conditions.