import matplotlib.pyplot as plt
import numpy as np
import serial
from scipy.stats import norm
import seaborn as sns
from IPython.display import clear_output
import bitstring
import networkx as nx
#Basic simulation parameters
#Length of the message packet in bytes
PACKET_LENGTH = 14
PREAMBLE_BYTE = 6
#Spreading Factor of the nodes
SF = 7
#Bandwidth the signal occupies (Hz)
BW = 250 *10**3
#COde rate for SF of 7-10 it is 1-4 respectively
CR = 1
#Header enables if 0 disabled if 1
H = 1
#Gainint the TOA
T_symbol = 2**SF/BW
T_preamble = (PREAMBLE_BYTE+4.25)*T_symbol
L_payload = 8 + ((8*PACKET_LENGTH-4*SF+28+16-H*20)/(4*SF))*(CR+4)
T_payload = L_payload*T_symbol
TOA = T_preamble+T_payload

#Define how many symbols per TOA
amount_symbols = int(1/TOA)

#Define client packet frequency
packet_freq = 1
#Define hallo frequency
hallo_freq = 1

#Sensitivity for SF=7 and BW = 250kHz the following is the floor dBm
sensitivity = -120
#SOme path specifications
#Define mean path loss
PL_d_0 = 127.41
d_0 = 40
#Path loss exponent
n = 2.08
#Standard deviation of noise
sigma_noise = 3.57

#Defining the channel capacity formulae
def channel_cap(SNR):
    return BW*np.log2(1+SNR)
#Defining the noise
def noise(variance,mean):
    return np.random.normal(mean,variance)
#Defining the path loss
def path_loss(d):
    return PL_d_0+10*n*np.log10(d/d_0)+noise(sigma_noise,0)
#Defining the probability of collision
def collision(traffic,ratio):
    return 1- np.e**(-((2*SF+1)/(SF))*((PACKET_LENGTH+PREAMBLE_BYTE)*8)/BW * ratio * traffic)

#Similar data structure than measurements
def is_collide(prob):
    number = np.random.uniform()
    if (number<=prob):
        return True
    else:
        return False

#Store the addresses here
#Address index corresponds to index of the measured node
NODE_index = [100,110,120,130]
#Defines when the Node started within the 1 second gap
NODE_Start = []
#Defines when the node sends Hallo
NODE_Hallo = []
#Defines when Client sends message
CLIENT_tx = []
#Stores the routing table next hop entries for each node for a given destination
DESTINATION_ROUTING_table_next = [[[120]],[[130]],[[130]],[[130]]]
#STores the next hop for the chosen path
DESTINATION_ROUTING_table_path =  [[[120]],[[130]],[[130]],[[130]]]
#STores amount messages sent per second uplink
NEIGH_tx = [[0,0],[0,0,0],[0,0,0],[0,0]]
#STores amount messages received per second downlink
NEIGH_rx = [[0,0],[0,0,0],[0,0,0],[0,0]]
#STores amount hallo received per second downlink
#If this amount is not at least hallo freq then link breaks
HALLO_rx = [[0,0],[0,0,0],[0,0,0],[0,0]]
#On next tick if the index to the right is lower then left then feed forward the message.
MESSAGE_rx = [0,0,0,0]
#Defines when client sent message
MESSAGE_tx = [0]
#Defines when destination received message
DEST_MESSAGE_rx = [0]
#Defines how many messages I actually sent
NODE_tx = [0,0,0,0]
#Defines messages I actually received
NODE_rx = [0,0,0,0]
#Store neighbour addresses here
NEIGH_add = [[110,120],[100,120,130],[100,110,130],[110,120]]
#Stores the distance between the node and it's neighbour (m)
NEIGH_add_distance = [[10,10],[10,10,10],[10,10,10],[10,10]]
#Store the average SNR of received link rememeber this is again unsigned???? makes sure dB
SNR_value = [[10,10],[10,10,10],[10,10,10],[10,10]]
#Hallo time outs
hallo_time_out = 0
#Store destination address here
DEST_add = [130]

#STores client addresses here
CLIENT_add = [100]

#Stores destination to client adds here
DEST_TO_CLIENT_add = []

#Stores cliebnt to dest adds here
CLIENT_TO_DEST_add = []

#Stores node to destination adds
NODE_TO_DEST_add = []

#Stores node to client adds
NODE_TO_CLIENT_add = []

#Data to be stored defined here
#Store the average RSSI of received link rememeber it is signed
RSSI_value = []
#Stores the routing table next hop entries for each node for a given origin
ORIGIN_ROUTING_table_next = []
#STores the next hop for the chosen path
ORIGIN_ROUTING_table_path = []
#Stores the average PING for received messages
Dest_PING_Amount = []
#Stores the amount of messages sent by client to destination per epoch
Client_TX_Amount = []
#STores the PDR for each link between node x and neighbour y
NODE_PDR_value = []
#Stores the ETX for each link between node x and neighbour y
NODE_ETX_value = []


if __name__ == "__main__":
    #Initialize measurement arrays
    #This will keep track of a change in message receive and reply
    MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
    # Store the loads here
    LOAD_array = []
    for i in range(0,len(NODE_index)):
        LOAD_array.append([])
    # Store amount of packets sent here
    PACKETS_sent = []
    for i in range(0,len(NEIGH_tx)):
        holder = []
        for j in range(len(NEIGH_tx[i])):
            holder.append([])
        PACKETS_sent.append(holder)
    # Store amount of packets received here
    PACKETS_received = []
    for i in range(0,len(NEIGH_rx)):
        holder = []
        for j in range(len(NEIGH_rx[i])):
            holder.append([])
        PACKETS_received.append(holder)
    Client_TX_Amount = []
    for i in range(0,len(CLIENT_add)):
        Client_TX_Amount.append([])
    # Stores the amount of message packets received per epoch
    Dest_RX_Amount = []
    for i in range(0,len(DEST_add)):
        Dest_RX_Amount.append([])

    #Define how long the simulation must go on for
    time_length = 60 #seconds
    #Set up the times when the nodes have started
    for i in range(0,len(NODE_index)):
        NODE_Start.append(int(np.random.uniform()*amount_symbols))
    print("#### FINISHED INITIAL VALUES   #########")
    print(NODE_Start)
    #Set up when the hallo messages started
    # Typically the node will send the hallo when it has started but allow for some variance
    for i in range(0,len(NODE_index)):
        number = (int(np.random.uniform()*5+NODE_Start[i])) % amount_symbols
        #Cant have these equal
        while number in NODE_Start:
            number = (int(np.random.uniform()*5 + NODE_Start[i])) % amount_symbols
        NODE_Hallo.append(number)

    print("#### FINISHED HALLO TIMERS   #########")
    print(NODE_Hallo)
    #Now setup when the client sends a message make sure not in the time's of itself
    for i in range(0,len(CLIENT_add)):
        number = int(np.random.uniform() * amount_symbols)
        while (number == NODE_Start[NODE_index.index(CLIENT_add[i])]) or (number == NODE_Start[NODE_index.index(CLIENT_add[i])]):
            number = int(np.random.uniform() * amount_symbols)
        CLIENT_tx.append(number)
    print("#### FINISHED CLIENT TIMERS   #########")
    print(CLIENT_tx)
    #Some assunptions made for now. Now RREQ messages or RREP yet only HALLO and MAIN message for now
    #PATHS have been initialized already thus the client starts sending a message

    for i in range(0,time_length):
        #Initialize the events each second
        if i > 0:
            # Only do this after the first time step
            # First check if no hallo timer has been missed
            #Repeat until flag is down
            flag = True
            for t in range(0, len(HALLO_rx)):
                for g in range(0, len(HALLO_rx[t])):
                    if HALLO_rx[t][g] < hallo_freq:
                        # print(HALLO_rx[t][g])
                        # Remove the neighbour from the neighbour list
                        hallo_time_out+=1


        HALLO_rx = []
        for t in range(0, len(NEIGH_add)):
            holder = []
            for g in range(0, len(NEIGH_add[t])):
                holder.append(0)
            HALLO_rx.append(holder)
        for j in range(0,amount_symbols):
            #Reset the checker
            # STores amount hallo received per second downlink
            # If this amount is not at least hallo freq then link breaks
            #Here we will propagate the sent message with the nodes
            for t in range(0,len(MESSAGE_rx)):
                if ((MESSAGE_rx[t]-MESSAGE_RX_PREV[t]>0) and (NODE_index[t] not in CLIENT_add) and (NODE_index[t] not in DEST_add)):
                    #This means the node received a message previously now forward it
                    #This node then sends a hallo
                    node_index = t
                    #Define who it sends to
                    #Define who it sends to
                    #Local neighbour list
                    local_neigh = NEIGH_add[node_index]
                    tx = NODE_tx[node_index]
                    rx = NODE_rx[node_index]
                    #Sends a hallo to each
                    #COunts as one message
                    #Obtain the current traffic for the node
                    traffic = tx+rx
                    # TODO make this more general
                    #Define the next hop
                    target = DESTINATION_ROUTING_table_path[node_index][0][0]
                    target_index = NODE_index.index(target)
                    # Update my tx
                    NODE_tx[node_index] += 1
                    for p in range(0, len(NEIGH_tx[node_index])):
                        #Because every neigh will get the packet just not repond to it
                        NEIGH_tx[node_index][p] += 1
                    if not (is_collide(collision(traffic * 8, 1))):
                        #CHeck if there is a path
                        if NODE_index[node_index] in NEIGH_add[target_index]:
                            # Message went through
                            MESSAGE_rx[target_index]+=1
                            NODE_rx[target_index] += 1
                            if NODE_index[target_index] in DEST_add:
                                DEST_MESSAGE_rx[DEST_add.index(NODE_index[target_index] )]+=1
                            rx_index = NEIGH_add[target_index].index(NODE_index[node_index])
                            NEIGH_rx[target_index][rx_index] += 1
            #Make a prev copy again
            MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
            #Initializes the amount for smallest possible time step
            if j in NODE_Hallo:
                #This node then sends a hallo
                node_index = NODE_Hallo.index(j)

                #Define who it sends to
                #Local neighbour list
                local_neigh = NEIGH_add[node_index]
                tx = NODE_tx[node_index]
                rx = NODE_rx[node_index]
                #Sends a hallo to each
                #COunts as one message
                #Obtain the current traffic for the node
                traffic = tx+rx
                # Update my tx
                NODE_tx[node_index] += 1
                for k in range(0,len(local_neigh)):
                    # UPdate tx
                    NEIGH_tx[node_index][k] += 1
                    if not (is_collide(collision(traffic*8,1))):
                        #Message went through
                        NODE_rx[NODE_index.index(NEIGH_add[node_index][k])]+=1
                        if (NODE_index[node_index] not in NEIGH_add[NODE_index.index(NEIGH_add[node_index][k])]):
                            #Append me to the neighbour list
                            NEIGH_add[NODE_index.index(NEIGH_add[node_index][k])].append(NODE_index[node_index])
                            HALLO_rx[NODE_index.index(NEIGH_add[node_index][k])].append(NODE_index[node_index])
                        #Update rx
                        node_neigh_index = NODE_index.index(local_neigh[k])
                        rx_index = NEIGH_add[node_neigh_index].index(NODE_index[node_index])
                        NEIGH_rx[node_neigh_index][rx_index]+=1
                        HALLO_rx[node_neigh_index][rx_index]+=1
                #Update timer for hallo
                NODE_Hallo[NODE_Hallo.index(j)] = (NODE_Hallo[NODE_Hallo.index(j)]+ amount_symbols/hallo_freq)%amount_symbols
            if j in CLIENT_tx:
                #This node then sends a hallo
                node_index = NODE_index.index(CLIENT_add[CLIENT_tx.index(j)])
                #Define who it sends to
                #Define who it sends to
                #Local neighbour list
                local_neigh = NEIGH_add[node_index]
                tx = NODE_tx[node_index]
                rx = NODE_rx[node_index]
                #Sends a hallo to each
                #COunts as one message
                #Obtain the current traffic for the node
                traffic = tx+rx
                # TODO make this more general
                #Define the next hop
                target = DESTINATION_ROUTING_table_path[node_index][0][0]
                target_index = NODE_index.index(DESTINATION_ROUTING_table_path[node_index][0][0])
                # Update my tx
                NODE_tx[node_index] += 1
                # UPdate tx
                MESSAGE_tx[node_index] +=1
                for p in range(0, len(NEIGH_tx[node_index])):
                    NEIGH_tx[node_index][p] += 1
                if not (is_collide(collision(traffic * 8, 1))):
                    if (NODE_index[node_index] in NEIGH_add[target_index]):
                        # Message went through
                        MESSAGE_rx[target_index]+=1
                        NODE_rx[target_index] += 1
                        # Update rx
                        rx_index = NEIGH_add[target_index].index(NODE_index[node_index])
                        NEIGH_rx[target_index][rx_index] += 1
                # Update timer for message
                CLIENT_tx[CLIENT_tx.index(j)] = int((CLIENT_tx[CLIENT_tx.index(j)] + amount_symbols / packet_freq) % amount_symbols)
        #After all events have been driven create a time stamp array similar to what is done for the measurement model
        #Save Loads
        for s in range(0,len(NODE_rx)):
            LOAD_array[s].append(NODE_rx[s]+NODE_tx[s])
        #Save packets sent
        for s in range(0,len(NEIGH_tx)):
            for l in range(0,len(NEIGH_tx[s])):
                PACKETS_sent[s][l].append(NEIGH_tx[s][l])
        #Save packets received
        for s in range(0,len(NEIGH_rx)):
            for l in range(0,len(NEIGH_rx[s])):
                PACKETS_received[s][l].append(NEIGH_rx[s][l])
        for s in range(0,len(MESSAGE_tx)):
            Client_TX_Amount[s].append(MESSAGE_tx[s])
        #TODO MAKE THIS MORE DYNAMIC
        Dest_RX_Amount[0].append(DEST_MESSAGE_rx[0])
        #Now clear the trackers
        # STores amount messages sent per second uplink
        NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # STores amount messages received per second downlink
        NEIGH_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # Defines when client sent message
        MESSAGE_tx = [0]
        DEST_MESSAGE_rx = [0]
        # Defines how many messages I actually sent
        NODE_tx = [0, 0, 0, 0]
        # Defines messages I actually received
        NODE_rx = [0, 0, 0, 0]

    print(LOAD_array)
    print(PACKETS_sent)
    print(PACKETS_received)
    print(Dest_RX_Amount)
    print(hallo_time_out)