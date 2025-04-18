# Distance Vector Routing Implementation

This project implements a distributed Distance Vector Routing (DVR) protocol that allows network nodes to discover optimal paths to all other nodes in a network.

## Project Overview

The Distance Vector Routing protocol works by having each node maintain:
- A distance vector: the cost to reach each known destination
- A routing table: the next hop to use when forwarding packets to each destination

Nodes periodically exchange their distance vectors with neighbors, allowing the entire network to gradually discover optimal routes to all destinations.

## Files

- `network.py`: Network simulator that manages connections between nodes and forwards messages
- `dvr.py`: Implementation of the Distance Vector Routing protocol
- `log_*.txt`: Output files showing the routing tables at each node

## Requirements

- Python 3.x
- Socket library (standard in Python)

## How to Run

### 1. Start the Network Simulator

```bash
python3 network.py <network_port> <topology_file>
```

Parameters:
- `network_port`: Port number for the network simulator (between 1024-65535)
- `topology_file`: Path to a file describing the network topology

Example:
```bash
python3 network.py 5000 topology.dat
```

### 2. Start the DVR Nodes

For each node in your topology, open a new terminal and run:

```bash
python3 dvr.py <network_ip> <network_port>
```

Parameters:
- `network_ip`: IP address of the network simulator (use 'localhost' or '127.0.0.1' for local testing)
- `network_port`: The same port number used for the network simulator

Example:
```bash
python3 dvr.py localhost 5000
```

You must run exactly the same number of `dvr.py` instances as there are unique nodes in your topology file.

## Topology File Format

The topology file specifies the network structure, with each line defining a link between two nodes and its cost:

```
<node_id_1> <node_id_2> <cost>
```

Example:
```
A B 5
B C 4
C D 3
```

This creates a network with 4 nodes (A, B, C, D) connected in a line topology.

## Implementation Features

- **Split Horizon with Poison Reverse**: To prevent routing loops, when a node routes through a neighbor to reach a destination, it reports an "infinite" distance (999) to that destination when sending updates to that neighbor.
- **Bellman-Ford Algorithm**: The algorithm continuously relaxes paths, updating distance vectors whenever a shorter path is discovered.
- **Dynamic Topology Discovery**: Nodes initially only know about their immediate neighbors but learn about other nodes in the network as routing information propagates.

## Log Files

Each node creates a log file named `log_<node_id>.txt` containing its routing table after each update. The format is:

```
<destination_1>:<cost_1>:<next_hop_1> <destination_2>:<cost_2>:<next_hop_2> ...
```

## Error Handling

- The program gracefully handles connection issues and timeouts
- Clean shutdown with CTRL+C
- Protection against invalid topology files

## Protocol Design

The DVR protocol uses:
- Initial neighbor discovery via the network simulator
- Periodic broadcast of distance vectors to neighbors
- Split horizon with poison reverse to prevent count-to-infinity problems
- Bellman-Ford algorithm for route calculation

## Testing

You can test different network topologies by creating different topology files and observing how the routes converge. Example topologies include:
- Line networks
- Ring networks
- Star topologies
- Networks with asymmetric costs
- Networks with link failures (by removing links from the topology)