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
8) ['Source node address','M','S','Amount of messages sent','\n']
9) Is calculated by using the data from 8 for both the source and destination 

For the simulator the data is stored as follows:

NODE_index keeps track of the index of the nodes in their corresponding measurement arrays

LOAD_array stores the time step load for each node.

PACKETS_sent_add keeps track of the index of the nodes sent to in 2)
PACKETS_sent keeps track of amount of packets sent to node 