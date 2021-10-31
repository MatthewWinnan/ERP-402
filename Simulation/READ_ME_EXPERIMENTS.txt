Experiments setup:
Parameters:
1) Current Load
2) Packets sent (catogorized per neighbour)
3) Packets received (catogorized per neighbour)
4) Packet delivery ratio (catogorized per neighbour)
5) RSSI of link
6) SNR of link
7) Throughput based on packets received at destination
8) Packet Loss based on ratio between messages sent and received
9) Overhead?????????

Packets of data will be sent to computer at a baudrate of 9600 by using the bluetooth models.
The packets will be sent every 2 seconds.
The simulation platform will sample from the serial register every 4 seconds.
This is to ensure the pyserial platform can keep up and that all measurements will be delivered.
 
Packet format routing node:
'ST' denotes the start of measurements.
'LD' denotes the next load measurement starts.
'PS' denotes the measurements following is amount of packets sent.
'ND' denotes next measurement is the destination of the packets.
'RA' denotes that the measurements will repeat again
'PR' denotes amount of packets received
'NS' denotes next measurement is the destination of the packets.
'RI' denotes RSSI measurement is following. This should be signed?????
'SN' denotes the SNR measurement is following. Check the units.
'MR' denotes the amount of messages received from the source
'PI' denotes the ping ie the amount of time it took on average for the packets to arrive.
This is calculated  by appending time sent to the message packet and subtracting time sent from the received time.
Ping is given in terms of the current clock cycles since start time. CLOCKS_PER_SEC   = 100 
'MS' denotes the next measurement is amount of messages sent.
'TE' denotes that a table entry of a path has been observed
'CP' CP denotes that the next hop following is the chosen path
'DA' DA denotes that the destination address is following
'CN' CN denotes that the client node data follows


'\n' the endline denotes the ending of a set of measurements.
Always start next set of measurements with the current node's address.

 '.......' denotes that the measurements listed to the left continues if there are more instances of the measurement.


1) ['S','T','Routing node address','L','D','Current load','\n'],
2) ['Routing node address','N','D','Neighbour destination','P','S','Amount of Packets sent','R','A'........,'\n'],
3) ['Routing node address','N','S','Neighbour source','P','R','Amount of Packets received','R','A'........,'\n'],
4) Gets calculated by using the data of 2 and 3 per link.
5) ['Routing node address','N','S','Neighbour source','R','I','RSSI measurement','R','A'........,'\n'],
6) ['Routing node address','N','S','Neighbour source','S','N','SNR measurement','R','A'........,'\n'],
7) ['Routing node address','D','A','Destination address','C','P', 'Next hop address','T','E','Next hop address','R','A'........, '\n']
----------------------------------------------------------------------------------------------------
Following are additional parameters to be sent by destination node.
8) ['Destination node address','C','N',Client address,'M','R','Amount of messages received','P','I','Ping','R','A',........,'\n']
9) Is calculated by using the data from 8 for both the source and destination
10) Is calculated by using 9's Ping reading

Following are addtional parameters sent by the source node.
8) ['Source node address','D','A','Destination Address','M','S','Amount of messages sent','R','A',..........,'\n']
9) Is calculated by using the data from 8 for both the source and destination 

For the simulator the data is stored as follows:
NODE_index = []
1) 1-D array stores addresses of known nodes for use in neighbour tracking and link tracking
2) index of address corresponds to index of known node for future use

#Store neighbour addresses here
NEIGH_add = []
1) 2-D array stores the known neighbours for each node
2) Each 1-D entry in NEIGH_add is a node. The index of that node corresponds to Node_index
3) Each 1-D entry in NEIGH_add[x] is a known neighbour. The index of that neighbour corresponds to it's index for future use

#Store destination address here
DEST_add = []
1) 1-D array stores addresses of known destinations for use in rx and ping tracking
2) index of address corresponds to index of known node for future use

#STores client addresses here
CLIENT_add = []
1) 1-D array stores addresses of known clients for use in tx tracking
2) index of address corresponds to index of known node for future use

#Stores destination to client adds here
DEST_TO_CLIENT_add = []
1) 2-D array stores the known clients for each destination
2) Each 1-D entry in DEST_TO_CLIENT_add is a destination. The index of that destination corresponds to Dest_add
3) Each 1-D entry in DEST_TO_CLIENT_add[x] is a known client for the destination. The index of that client corresponds to it's index for future use

#Stores cliebnt to dest adds here
CLIENT_TO_DEST_add = []
1) 2-D array stores the known destination for each client
2) Each 1-D entry in CLIENT_TO_DEST_add is a client. The index of that client corresponds to Client_add
3) Each 1-D entry in CLIENT_TO_DEST_add[x] is a known destination for the client. The index of that destinaiton corresponds to it's index for future use

#Stores node to destination adds
NODE_TO_DEST_add = []
1) 2-D array stores the known destinaitons for each node
2) Each 1-D entry in NODE_TO_DEST_add is a node. The index of that node corresponds to Node_index
3) Each 1-D entry in NODE_TO_DEST_add[x] is a known destination for the node. The index of that destination corresponds to it's index for future use

#Stores node to client adds
NODE_TO_CLIENT_add = []
1) 2-D array stores the known clients for each node
2) Each 1-D entry in NODE_TO_CLIENT_add is a node. The index of that node corresponds to Node_index
3) Each 1-D entry in NODE_TO_CLIENT_add[x] is a known client for the node. The index of that client corresponds to it's index for future use

#Data to be stored defined here
#Store the loads here
LOAD_array = []
1) 2-D array stores the current load for every node
2) Index of node in LOAD_array corresponds to index of node in Node_index
3) LOAD_array[x] is the time series of the load for the corresponding node

#Store amount of packets sent here
PACKETS_sent = []
1) 3-D array stores the current uplink for every node to neighbour
2) Index of node in PACKETS_sent corresponds to index of node in Node_index
3) Index in PACKETS_sent[x] corresponds to the neighbour index in NEIGH_add
4) PACKETS_sentp[x][y] is the time series of uplink packets for the link between node and neighbour

#Store amount of packets received here
PACKETS_received = []
1) 3-D array stores the current downlink for every node to neighbour
2) Index of node in PACKETS_received corresponds to index of node in Node_index
3) Index in PACKETS_received[x] corresponds to the neighbour index in NEIGH_add
4) PACKETS_received[x][y] is the time series of donwlink packets for the link between node and neighbour

#Store the average RSSI of received link rememeber it is signed
RSSI_value = []
1) 3-D array stores the current RSSI for every node to neighbour
2) Index of node in RSSI_value corresponds to index of node in Node_index
3) Index in RSSI_value[x] corresponds to the neighbour index in NEIGH_add
4) RSSI_value[x][y] is the time series of the RSSI for the link between node and neighbour

#Store the average SNR of received link rememeber this is again unsigned???? makes sure
SNR_value = []
1) 3-D array stores the current SNR for every node to neighbour
2) Index of node in SNR_value corresponds to index of node in Node_index
3) Index in SNR_value[x] corresponds to the neighbour index in NEIGH_add
4) SNR_value[x][y] is the time series of the SNR for the link between node and neighbour

#Stores the routing table next hop entries for each node for a given destination
ROUTING_table_next = []
1) 3-D array stores the current available next hop paths from a node to a known destination
2) Index of node in ROUTING_table_next corresponds to index of node in Node_index
3) Index in ROUTING_table_next[x] corresponds to the destination index in NODE_TO_DEST_add[x]
4) ROUTING_table_next[x][y] is the array of known next hops to destination

#STores the next hop for the chosen path
ROUTING_table_path = []
1) 3-D array stores the current chosen path from a node to a known destination
2) Index of node in ROUTING_table_path corresponds to index of node in Node_index
3) Index in ROUTING_table_path[x] corresponds to the destination index in NODE_TO_DEST_add[x]
4) ROUTING_table_path[x][y] is the next hop entry

#Stores the amount of messages packets received per epoch
Dest_RX_Amount = []
1) 3-D array stores the current RX packets from known client to a destination
2) Index of node in Dest_RX_Amount corresponds to index of node in Dest_Add
3) Index in Dest_RX_Amount[x] corresponds to the destination index in DEST_TO_CLIENT_add[x]
4) Dest_RX_Amount[x][y] is the time series for the RX of packets

#Stores the average PING for received messages
Dest_PING_Amount = []
1) 3-D array stores the current PING from known client to a destination
2) Index of node in Dest_PING_Amount corresponds to index of node in Dest_Add
3) Index in Dest_PING_Amount[x] corresponds to the destination index in DEST_TO_CLIENT_add[x]
4) Dest_PING_Amount[x][y] is the time series for the PING of packets

#Stores the amount of messages sent by client to destination per epoch
Client_TX_Amount = []
1) 3-D array stores the current TX from known client to a destination
2) Index of node in Client_TX_Amount corresponds to index of node in CLient_Add
3) Index in Client_TX_Amount[x] corresponds to the destination index in CLIENT_TO_DEST_add[x]
4) Client_TX_Amount[x][y] is the time series for the TX of packets


#STores the PDR for each link between node x and neighbour y
NODE_PDR_value = []
1) 3-D array stores the pdr of the link between node x and neighbour y
2) Index of node in NODE_PDR_value corresponds to index of node in Node_index
3) Index in NODE_PDR_value[x] corresponds to the neighbour index in PACKETS_received[x]
4) NODE_PDR_value[x][y] is the time series of the pdr for the link

#Stores the ETX for each link between node x and neighbour y
NODE_ETX_value = []
1) 3-D array stores the etx of the link between node x and neighbour y
2) Index of node in NODE_ETX_value corresponds to index of node in Node_index
3) Index in NODE_ETX_value[x] corresponds to the neighbour index in PACKETS_received[x]
4) NODE_ETX_value[x][y] is the time series of the etx for the link