import matplotlib.pyplot as plt
import numpy as np
import serial
from scipy.stats import norm
import seaborn as sns
from IPython.display import clear_output
import bitstring
import networkx as nx
from PIL import Image

#Define what needs to be tested
AODV = False
AOMDV = False
AOMDV_LB = False
GRAPH = True

#Basic simulation parameters
#Length of the message packet in bytes
PACKET_LENGTH = int((13+11+10+14)/4)
PREAMBLE_BYTE = 8
#Spreading Factor of the nodes
SF = 7
#Bandwidth the signal occupies (Hz)
BW = 250 *10**3
#Code rate for SF of 7-10 it is 1-4 respectively
CR = 1
#Header enables if 0 disabled if 1
H = 1
#Gaining the TOA
T_symbol = 2**SF/BW
T_preamble = (PREAMBLE_BYTE+4.25)*T_symbol
L_payload = 8 + ((8*PACKET_LENGTH-4*SF+28+16-H*20)/(4*SF))*(CR+4)
T_payload = L_payload*T_symbol
TOA = T_preamble+T_payload

#Define how many symbols per TOA
amount_symbols = int(1/TOA)

#Define client packet frequency
packet_freq = 5
#Define hallo frequency
hallo_freq = 2

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
    return 1- np.e**(-((2*SF+1)/(SF))*(8 )/BW * ratio * traffic)

def calc_collision(traffic,sf):
    return 1- np.e**(-((2*sf+1)/(sf))*((PACKET_LENGTH+PREAMBLE_BYTE)*8)/BW * 1 * traffic)

def TOA_calc(sf,bytes):
    T_symbol = 2 ** sf / BW
    T_preamble = (PREAMBLE_BYTE + 4.25) * T_symbol
    L_payload = 8 + ((8 * bytes - 4 * SF + 28 + 16 - H * 20) / (4 * sf)) * (CR + 4)
    T_payload = L_payload * T_symbol
    TOA = T_preamble + T_payload
    return TOA

def BIT_Rate_Calc(sf,bw):
    return sf*(4/5)/(2**sf/bw)
#Similar data structure than measurements
def is_collide(prob):
    number = np.random.uniform()
    if (number<=prob):
        return True
    else:
        return False

def Update_Destination_Graph(NEIGH_add):
    #Updates the visualization for the path towards a destination
    # Initialize Graph
    G = nx.DiGraph()
    # Initialize legend array
    legend = []
    for i in range(0, len(NODE_index)):
        if (NODE_index[i] in CLIENT_add):
            # Adding Client nodes
            G.add_node(NODE_index[i], color=Node_Color[0], size=Node_Size[1], shape=Node_Shape[0])
            legend.append("Client Node " + str(NODE_index[i]))
        elif (NODE_index[i] in DEST_add):
            # Adding Dest nodes
            G.add_node(NODE_index[i], color=Node_Color[1], size=Node_Size[2], shape=Node_Shape[1])
            legend.append("Destination Node " + str(NODE_index[i]))
        else:
            # Adding routing nodes
            G.add_node(NODE_index[i], color=Node_Color[2], size=Node_Size[0], shape=Node_Shape[2])
            legend.append("Routing Node " + str(NODE_index[i]))
        for j in range(0, len(NEIGH_add[i])):
            # Adding edges
            b_flag = False  # This flag says was the edge a path to the destination
            for k in range(0, len(DEST_add)):
                # We need to check if this edge is a path to the destination
                if (NEIGH_add[i][j] in DESTINATION_ROUTING_table_next[i][k]):
                    # It is a path
                    b_flag = True
                    if (NEIGH_add[i][j] in DESTINATION_ROUTING_table_path[i][k]):
                        # Now check if it is the chosen path if it is treat according
                        G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[2], width=Edge_Size[2])
                    else:
                        # Only an available path thus treat according
                        G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[1], width=Edge_Size[1])
            if (not b_flag):
                # The edge is not a path as such treat according
                G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[0], width=Edge_Size[0])
    return G

def Display_Destination_Graph (G):
    plt.close()
    # Now graph it
    pos = nx.spring_layout(G)
    labels_edge = nx.get_edge_attributes(G, 'color')
    colors_edge = nx.get_edge_attributes(G, 'color').values()
    width_edge = nx.get_edge_attributes(G, 'width').values()
    colors_node = nx.get_node_attributes(G, 'color').values()
    size_nodes = list(nx.get_node_attributes(G, 'size').values())
    shapes_nodes = list(nx.get_node_attributes(G, 'shape').values())
    nx.draw_networkx(G, pos, with_labels=True, font_weight='bold', node_color=colors_node, node_size=size_nodes,
                     node_shape='D', edge_color=colors_edge, width=list(width_edge))
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_edge)
    plt.savefig(test_array[current_test] +measurement_array[8]+ "_result_network.pdf")
    plt.show()  # display


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
    # Define how long the simulation must go on for
    time_length = 60  # seconds
    repititions = 1
    NUM_SAMPLES = time_length
    SAMPLING_FREQ = 1
    X_axis = np.linspace(0, (NUM_SAMPLES - 1) / SAMPLING_FREQ, NUM_SAMPLES)
    #Define the test name
    # Define the test strings
    test_array = ["Test_1","Test_2","Test_3"]
    # Libraries used for graphing
    # Defining what colors the nodes should be
    # r = clients
    # b = destination
    # g = routing nodes
    Node_Color = ["r", "b", "g"]
    # Defining what color the edges should be
    # k = merely neighbours
    # y = valid path to destination/origin
    # m = chosen path to destination
    Edge_Color = ['k', 'y', 'm']
    # Defining what sizes the nodes should be
    # 2 = clients
    # 3 = destination
    # 1 = routing nodes
    Node_Size = [600, 900, 1200]
    # Defining what thickness the edges should be
    # 1 = merely neighbours
    # 2 = valid path to destination/origin
    # 3 = chosen path to destination
    Edge_Size = [1, 2, 3]
    # Defining the shapes of the nodes
    # "v" = clients
    # "^" = destination
    # "o" = routing nodes
    Node_Shape = ['v', '^', 'o']
    # Libraries for graphing
    DATATYPE_LIST = ['Load (packets/s)', 'Packet Delivery Ratio', 'ETX value for link',
                     'RSSI for link (dBm)', 'SNR for link (dBm)', 'Throughput (packets/s)', 'Packet Delay (ms)',
                     'Message Delivery Ratio', 'Destination Route Visualize', 'Origin Route Visualize']
    LINE_COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    # Measurements taken
    measurement_array = ["_load_per_node", "_pdr_per_node", "_etx_per_node", "_rssi_per_node", "_snr_per_node",
                         "_throughput_per_dest", "_ping_per_dest", "_mdr_per_dest", "_dest_route_visual",
                         "_origin_route_visual"]


    if AODV:
        # What test are we doing????
        current_test = 0
        # STores the PDR for each link between node x and neighbour y
        NODE_PDR_value = []
        print("#### Starting AODV Simulations ########")
        # Defines the amount of missed hallo
        HALLO_TIMEOUT = 4
        # Store the addresses here
        # Address index corresponds to index of the measured node
        NODE_index = [100, 110, 120, 130]
        #NODE_index = [100, 110, 120, 130]
        # Defines when the Node started within the 1 second gap
        NODE_Start = []
        # Defines when the node sends Hallo
        NODE_Hallo = []
        # Defines when Client sends message
        CLIENT_tx = []
        # Stores the routing table next hop entries for each node for a given destination
        # DESTINATION_ROUTING_table_next = [[[120, 110]], [[130, 120]], [[130, 110]], [[130]]]
        DESTINATION_ROUTING_table_next = [[[]], [[]], [[]], [[]]]
        # STores the next hop for the chosen path
        # DESTINATION_ROUTING_table_path = [[[120]], [[130]], [[130]], [[130]]]
        DESTINATION_ROUTING_table_path = [[[]], [[]], [[]], [[]]]
        # STores amount messages sent per second uplink
        # NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        NEIGH_tx = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        # STores amount messages received per second downlink
        # NEIGH_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        NEIGH_rx = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        # STores amount hallo received per second downlink
        # If this amount is not at least hallo freq then link breaks
        # HALLO_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        HALLO_rx = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        # STores the timeout ticks missed
        HALLO_counter = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]

        # HALLO_counter = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # HALLO_counter = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        # On next tick if the index to the right is lower then left then feed forward the message.
        #MESSAGE_rx = [0, 0, 0, 0]
        MESSAGE_rx = []
        # Defines when client sent message
        #MESSAGE_tx = [0]
        MESSAGE_tx = []
        # Defines when destination received message
        # DEST_MESSAGE_rx = [0]
        DEST_MESSAGE_rx = []
        # Defines how many messages I actually sent
        # NODE_tx = [0, 0, 0, 0]
        NODE_tx = [0, 0, 0, 0]
        # Defines messages I actually received
        # NODE_rx = [0, 0, 0, 0]
        NODE_rx = [0, 0, 0, 0]
        # Store neighbour addresses here
        # Define two, one for what the node actually knows and one for what neighbours can receive any message
        # This is what the node knows
        # NEIGH_add_tx = [[110, 120], [100, 120, 130], [100, 110, 130], [110, 120]]
        NEIGH_add_tx = [[110, 120, 130], [100, 120, 130], [100, 110, 130], [100, 110, 120]]
        # This is what the modal knows
        NEIGH_add_rx = [[110, 120, 130], [100, 120, 130], [100, 110, 130], [100, 110, 120]]
        # NEIGH_add_rx = [[110, 120], [100, 120, 130], [100, 110, 130], [110, 120]]
        # Stores the distance between the node and it's neighbour (m)
        NEIGH_add_distance = [[10, 10], [10, 10, 10], [10, 10, 10], [10, 10]]
        # Store the average SNR of received link rememeber this is again unsigned???? makes sure dB
        SNR_value = [[10, 10], [10, 10, 10], [10, 10, 10], [10, 10]]
        # Hallo time outs
        hallo_time_out = 0
        # Store destination address here
        # DEST_add = [130]
        DEST_add = []

        # STores client addresses here
        # CLIENT_add = [100]
        CLIENT_add = []
        # Initialize measurement arrays
        # This will keep track of a change in message receive and reply
        MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
        # Store the loads here
        LOAD_array = []
        for i in range(0, len(NODE_index)):
            LOAD_array.append([])

        # Store the averaging amount
        LOAD_array_average = []
        for i in range(0, len(NODE_index)):
            holder = []
            for j in range(0, time_length):
                holder.append(0)
        LOAD_array_average.append(holder)
        LOAD_array_average = np.array(LOAD_array_average)

        # Store average for amount of packets
        PACKETS_sent_average = []
        for i in range(0, len(NEIGH_tx)):
            holder = []
            for j in range(0, len(NEIGH_tx[i])):
                holder_two = []
                for k in range(0, time_length):
                    holder_two.append(0)
                holder.append(holder_two)
            PACKETS_sent_average.append(holder)
        PACKETS_sent_average = PACKETS_sent_average

        # Store amount of packets sent here
        PACKETS_sent = []
        for i in range(0, len(NEIGH_tx)):
            holder = []
            for j in range(len(NEIGH_tx[i])):
                holder.append([])
            PACKETS_sent.append(holder)

        # Store average amount of packets received
        PACKETS_receive_average = []
        for i in range(0, len(NEIGH_rx)):
            holder = []
            for j in range(0, len(NEIGH_rx[i])):
                holder_two = []
                for k in range(0, time_length):
                    holder_two.append(0)
                holder.append(holder_two)
            PACKETS_receive_average.append(holder)
        PACKETS_receive_average = PACKETS_receive_average

        # Store amount of packets received here
        PACKETS_received = []
        for i in range(0, len(NEIGH_rx)):
            holder = []
            for j in range(len(NEIGH_rx[i])):
                holder.append([])
            PACKETS_received.append(holder)

        # Storing client tx average amount
        Client_TX_Amount_average = []
        for i in range(0, len(CLIENT_add)):
            holder = []
            for j in range(0, time_length):
                holder.append(0)
            Client_TX_Amount_average.append(holder)
        Client_TX_Amount_average = np.array(Client_TX_Amount_average)

        Client_TX_Amount = []
        for i in range(0, len(CLIENT_add)):
            Client_TX_Amount.append([])

        # Storing dest rx average amount
        Dest_RX_Amount_average = []
        for i in range(0, len(DEST_add)):
            holder = []
            for j in range(0, time_length):
                holder.append(0)
            Dest_RX_Amount_average.append(holder)
        Dest_RX_Amount_average = np.array(Dest_RX_Amount_average)

        # Stores the amount of message packets received per epoch
        Dest_RX_Amount = []
        for i in range(0, len(DEST_add)):
            Dest_RX_Amount.append([])

        # Set up the times when the nodes have started
        for i in range(0, len(NODE_index)):
            NODE_Start.append(int(np.random.uniform() * amount_symbols))
        print("#### FINISHED INITIAL VALUES   #########")
        print(NODE_Start)

        # Set up when the hallo messages started
        # Typically the node will send the hallo when it has started but allow for some variance
        for i in range(0, len(NODE_index)):
            number = (int(np.random.uniform() * 5 + NODE_Start[i])) % amount_symbols
            # Cant have these equal
            while number in NODE_Start:
                number = (int(np.random.uniform() * 5 + NODE_Start[i])) % amount_symbols
            NODE_Hallo.append(number)

        print("#### FINISHED HALLO TIMERS   #########")
        print(NODE_Hallo)
        # Now setup when the client sends a message make sure not in the time's of itself
        for i in range(0, len(CLIENT_add)):
            number = int(np.random.uniform() * amount_symbols)
            while (number == NODE_Start[NODE_index.index(CLIENT_add[i])]) or (
                    number == NODE_Start[NODE_index.index(CLIENT_add[i])]):
                number = int(np.random.uniform() * amount_symbols)
            CLIENT_tx.append(number)
        print("#### FINISHED CLIENT TIMERS   #########")
        print(CLIENT_tx)
        # Some assunptions made for now. Now RREQ messages or RREP yet only HALLO and MAIN message for now
        # PATHS have been initialized already thus the client starts sending a message
        #Add a averaging term
        for b in range(0,repititions):
            for i in range(0, time_length):
                # Initialize the events each second
                if i > 0:
                    # Only do this after the first time step
                    # First check if no hallo timer has been missed
                    # Repeat until flag is down
                    flag = True
                    removal_neigh = []
                    for t in range(0, len(HALLO_rx)):
                        removal_neigh_holder = []
                        for g in range(0, len(HALLO_rx[t])):
                            if HALLO_rx[t][g] < hallo_freq / 2:
                                #Add a counter to HALLO counter
                                HALLO_counter[t][g]+=1
                            # if HALLO_rx[t][g] < 0:
                                # print(HALLO_rx[t][g])
                                if (HALLO_counter[t][g]==HALLO_TIMEOUT):
                                    # Remove the neighbour from the neighbour list
                                    hallo_time_out += 1
                                    removal_neigh_holder.append(NEIGH_add_rx[t][g])
                                    #Reset counter
                                    HALLO_counter[t][g] = 0
                        removal_neigh.append(removal_neigh_holder)
                    # After all nodes been obtained that needs deletion start removing
                    for t in range(0, len(removal_neigh)):
                        for g in range(0, len(removal_neigh[t])):
                            if removal_neigh[t][g] in NEIGH_add_tx[t]:
                                NEIGH_add_tx[t].remove(removal_neigh[t][g])
                HALLO_rx = []
                for t in range(0, len(NEIGH_add_rx)):
                    holder = []
                    for g in range(0, len(NEIGH_add_rx[t])):
                        holder.append(0)
                    HALLO_rx.append(holder)
                for j in range(0, amount_symbols):
                    # Reset the checker
                    # STores amount hallo received per second downlink
                    # If this amount is not at least hallo freq then link breaks
                    # Here we will propagate the sent message with the nodes
                    for t in range(0, len(MESSAGE_rx)):
                        if ((MESSAGE_rx[t] - MESSAGE_RX_PREV[t] > 0) and (NODE_index[t] not in CLIENT_add) and (
                                NODE_index[t] not in DEST_add)):
                            # This means the node received a message previously now forward it
                            # This node then sends a hallo
                            node_index = t
                            # Define who it sends to
                            # Define who it sends to
                            # Local neighbour list
                            local_neigh = NEIGH_add_tx[node_index]
                            tx = NODE_tx[node_index]
                            rx = NODE_rx[node_index]
                            # Sends a hallo to each
                            # COunts as one message
                            # Obtain the current traffic for the node
                            traffic = tx + rx
                            # TODO make this more general
                            # Define the next hop
                            target = DESTINATION_ROUTING_table_path[node_index][0][0]
                            target_index = NODE_index.index(target)
                            # Update my tx
                            NODE_tx[node_index] += 1
                            if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[target_index])
                                NEIGH_tx[node_index][neigh_target_index] += 1
                            traffic = NODE_tx[target_index] + NODE_rx[target_index]
                            if not (is_collide(collision(traffic * (PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                # CHeck if there is a path
                                if NODE_index[node_index] in NEIGH_add_tx[target_index]:
                                    # Message went through
                                    MESSAGE_rx[target_index] += 1
                                    NODE_rx[target_index] += 1
                                    if NODE_index[target_index] in DEST_add:
                                        DEST_MESSAGE_rx[DEST_add.index(NODE_index[target_index])] += 1
                                    rx_index = NEIGH_add_rx[target_index].index(NODE_index[node_index])
                                    NEIGH_rx[target_index][rx_index] += 1
                    # Make a prev copy again
                    MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
                    # Initializes the amount for smallest possible time step
                    if j in NODE_Hallo:
                        # This node then sends a hallo
                        node_index = NODE_Hallo.index(j)

                        # Define who it sends to
                        # Local neighbour list
                        local_neigh = NEIGH_add_tx[node_index]
                        tx = NODE_tx[node_index]
                        rx = NODE_rx[node_index]
                        # Sends a hallo to each
                        # COunts as one message
                        # Obtain the current traffic for the node
                        traffic = tx + rx
                        # Update my tx
                        NODE_tx[node_index] += 1
                        for k in range(0, len(local_neigh)):
                            # UPdate tx
                            NEIGH_tx[node_index][k] += 1
                            temp_index = NODE_index.index(local_neigh[k])
                            traffic = NODE_rx[temp_index] + NODE_rx[temp_index]
                            if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                # Message went through
                                NODE_rx[NODE_index.index(NEIGH_add_rx[node_index][k])] += 1
                                if (NODE_index[node_index] not in NEIGH_add_tx[NODE_index.index(NEIGH_add_rx[node_index][k])]):
                                    # Append me to the neighbour list
                                    NEIGH_add_tx[NODE_index.index(NEIGH_add_rx[node_index][k])].append(NODE_index[node_index])
                                    #HALLO_rx[NODE_index.index(NEIGH_add_rx[node_index][k])].append(NODE_index[node_index])
                                # Update rx
                                node_neigh_index = NODE_index.index(local_neigh[k])
                                rx_index = NEIGH_add_rx[node_neigh_index].index(NODE_index[node_index])
                                NEIGH_rx[node_neigh_index][rx_index] += 1
                                HALLO_rx[node_neigh_index][rx_index] += 1
                                #Reset the hallo counter
                                HALLO_counter[node_neigh_index][rx_index] = 0
                        # Update timer for hallo
                        NODE_Hallo[NODE_Hallo.index(j)] = int(
                            (NODE_Hallo[NODE_Hallo.index(j)] + amount_symbols / hallo_freq) % amount_symbols)
                    if j in CLIENT_tx:
                        # This node then sends a hallo
                        node_index = NODE_index.index(CLIENT_add[CLIENT_tx.index(j)])
                        # Define who it sends to
                        # Define who it sends to
                        # Local neighbour list
                        local_neigh = NEIGH_add_tx[node_index]
                        tx = NODE_tx[node_index]
                        rx = NODE_rx[node_index]
                        # Sends a hallo to each
                        # COunts as one message
                        # Obtain the current traffic for the node
                        traffic = tx + rx
                        # TODO make this more general
                        # Define the next hop
                        target = DESTINATION_ROUTING_table_path[node_index][0][0]
                        target_index = NODE_index.index(DESTINATION_ROUTING_table_path[node_index][0][0])
                        # Update my tx
                        NODE_tx[node_index] += 1
                        # UPdate tx
                        MESSAGE_tx[node_index] += 1
                        if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                            neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[target_index])
                            NEIGH_tx[node_index][neigh_target_index] += 1
                        traffic = NODE_tx[target_index] + NODE_rx[target_index]
                        if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                            if (NODE_index[node_index] in NEIGH_add_tx[target_index]):
                                # Message went through
                                MESSAGE_rx[target_index] += 1
                                NODE_rx[target_index] += 1
                                # Update rx
                                rx_index = NEIGH_add_rx[target_index].index(NODE_index[node_index])
                                NEIGH_rx[target_index][rx_index] += 1
                        # Update timer for message
                        CLIENT_tx[CLIENT_tx.index(j)] = int(
                            (CLIENT_tx[CLIENT_tx.index(j)] + amount_symbols / packet_freq) % amount_symbols)
                # After all events have been driven create a time stamp array similar to what is done for the measurement model
                # Save Loads
                for s in range(0, len(NODE_rx)):
                    LOAD_array[s].append(NODE_rx[s] + NODE_tx[s])
                # Save packets sent
                for s in range(0, len(NEIGH_tx)):
                    for l in range(0, len(NEIGH_tx[s])):
                        PACKETS_sent[s][l].append(NEIGH_tx[s][l])
                # Save packets received
                for s in range(0, len(NEIGH_rx)):
                    for l in range(0, len(NEIGH_rx[s])):
                        PACKETS_received[s][l].append(NEIGH_rx[s][l])
                for s in range(0, len(MESSAGE_tx)):
                    Client_TX_Amount[s].append(MESSAGE_tx[s])
                # # TODO MAKE THIS MORE DYNAMIC
                # Dest_RX_Amount[0].append(DEST_MESSAGE_rx[0])
                # Now clear the trackers
                # STores amount messages sent per second uplink
                NEIGH_tx = []
                for h in range(0,len(NEIGH_add_rx)):
                    NEIGH_tx_holder = []
                    for y in range(0,len(NEIGH_add_rx[h])):
                        NEIGH_tx_holder.append(0)
                    NEIGH_tx.append(NEIGH_tx_holder)
                # STores amount messages received per second downlink
                NEIGH_rx = []
                for h in range(0,len(NEIGH_add_rx)):
                    NEIGH_rx_holder = []
                    for y in range(0,len(NEIGH_add_rx[h])):
                        NEIGH_rx_holder.append(0)
                    NEIGH_rx.append(NEIGH_rx_holder)
                # Defines when client sent message
                MESSAGE_tx = []
                for h in range(0,len(CLIENT_add)):
                    MESSAGE_tx.append(0)
                #Defines when destination received a message
                DEST_MESSAGE_rx = []
                for h in range(0,len(DEST_add)):
                    DEST_MESSAGE_rx.append(0)
                # Defines how many messages I actually sent
                NODE_tx = []
                for h in range(0,len(NODE_index)):
                    NODE_tx.append(0)
                # Defines messages I actually received
                NODE_rx = []
                for h in range(0, len(NODE_index)):
                    NODE_rx.append(0)
            LOAD_array_average = LOAD_array_average + np.array(LOAD_array)
            for q in range(0,len(PACKETS_sent_average)):
                for e in range(0,len(PACKETS_sent_average[q])):
                    for a in range(len(PACKETS_sent_average[q][e])):
                        PACKETS_sent_average[q][e][a] = PACKETS_sent_average[q][e][a] + PACKETS_sent[q][e][a]
            for q in range(0,len(PACKETS_receive_average)):
                for e in range(0,len(PACKETS_receive_average[q])):
                    for a in range(len(PACKETS_receive_average[q][e])):
                        PACKETS_receive_average[q][e][a] = PACKETS_receive_average[q][e][a] + PACKETS_received[q][e][a]
            Dest_RX_Amount_average = Dest_RX_Amount_average + np.array(Dest_RX_Amount)
            Client_TX_Amount_average = Client_TX_Amount_average + np.array(Client_TX_Amount)
            #Reset all normal trackers
            # Store the loads here
            LOAD_array = []
            for i in range(0, len(NODE_index)):
                LOAD_array.append([])
            # Store amount of packets sent here
            PACKETS_sent = []
            for i in range(0, len(NEIGH_tx)):
                holder = []
                for j in range(len(NEIGH_tx[i])):
                    holder.append([])
                PACKETS_sent.append(holder)
            # Store amount of packets received here
            PACKETS_received = []
            for i in range(0, len(NEIGH_rx)):
                holder = []
                for j in range(len(NEIGH_rx[i])):
                    holder.append([])
                PACKETS_received.append(holder)
            # SToring client tx amount
            Client_TX_Amount = []
            for i in range(0, len(CLIENT_add)):
                Client_TX_Amount.append([])
            # Stores the amount of message packets received per epoch
            Dest_RX_Amount = []
            for i in range(0, len(DEST_add)):
                Dest_RX_Amount.append([])
                # STores amount messages sent per second uplink
                # NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # STores amount messages sent per second uplink
            # NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            NEIGH_tx = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
            # STores amount messages received per second downlink
            # NEIGH_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            NEIGH_rx = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
            # STores amount hallo received per second downlink
            # If this amount is not at least hallo freq then link breaks
            # HALLO_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            HALLO_rx = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
            # STores the timeout ticks missed
            HALLO_counter = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]

            # HALLO_counter = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # HALLO_counter = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
            # On next tick if the index to the right is lower then left then feed forward the message.
            # MESSAGE_rx = [0, 0, 0, 0]
            MESSAGE_rx = []
            # Defines when client sent message
            # MESSAGE_tx = [0]
            MESSAGE_tx = []
            # Defines when destination received message
            # DEST_MESSAGE_rx = [0]
            DEST_MESSAGE_rx = []
            # Defines how many messages I actually sent
            # NODE_tx = [0, 0, 0, 0]
            NODE_tx = [0, 0, 0, 0]
            # Defines messages I actually received
            # NODE_rx = [0, 0, 0, 0]
            NODE_rx = [0, 0, 0, 0]

        #Now average out the arrays
        LOAD_array_average = 1/repititions * LOAD_array_average
        for q in range(0, len(PACKETS_sent_average)):
            for e in range(0, len(PACKETS_sent_average[q])):
                for a in range(len(PACKETS_sent_average[q][e])):
                    PACKETS_sent_average[q][e][a] = PACKETS_sent_average[q][e][a] * 1/repititions
        for q in range(0, len(PACKETS_receive_average)):
            for e in range(0, len(PACKETS_receive_average[q])):
                for a in range(len(PACKETS_receive_average[q][e])):
                    PACKETS_receive_average[q][e][a] = PACKETS_receive_average[q][e][a] *1/repititions
        Dest_RX_Amount_average = 1/repititions * Dest_RX_Amount_average
        Client_TX_Amount_average = 1/repititions * Client_TX_Amount_average

        print(LOAD_array_average)
        print(PACKETS_sent_average)
        print(PACKETS_receive_average)
        print(Dest_RX_Amount_average)
        print(hallo_time_out)
        print("########### Starting Plotting Data ###########")
        #Print the load data
        print("########### Plotting "+DATATYPE_LIST[0]+" ###########")
        plt.ylabel(DATATYPE_LIST[0])
        plt.xlabel("Time (s)")
        # fig.tight_layout()
        plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
        plt.grid(True)
        #Obtaining the legend array
        legend = []
        for i in range (0,len(NODE_index)):
            legend.append("Node "+str(NODE_index[i]))
        for i in range(0,len(LOAD_array_average)):
            plt.plot(X_axis,LOAD_array_average[i],LINE_COLORS[i])
        plt.legend(legend)
        plt.savefig(test_array[current_test]+measurement_array[0]+".pdf")
        plt.show()
        plt.close()
        #Print the load data
        print("########### Plotting " + DATATYPE_LIST[1] + " ###########")
        #Now plotting the PDR data
        for i in range(0,len(PACKETS_receive_average)):
            plt.ylabel(DATATYPE_LIST[1])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0,len(PACKETS_receive_average[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                neigh_add = NEIGH_add_rx[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(PACKETS_receive_average[i][j])):
                    #Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add_rx[node_index].index(NODE_index[i])
                    #As such the corresponding data received was sent by node_index to my_index
                    if (PACKETS_sent_average[node_index][my_index][k]!=0):
                        PDR_data.append(PACKETS_receive_average[i][j][k]/PACKETS_sent_average[node_index][my_index][k])
                    else:
                        PDR_data.append(0)
                    #CETX_data.append(1/(PACKETS_received[i][j][k]*PACKETS_sent[node_index][my_index][k]))
                plt.plot(X_axis, PDR_data, LINE_COLORS[j])
                holder.append(PDR_data)
            NODE_PDR_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[1] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[2] + " ###########")
        #Now plotting the ETX data
        for i in range(0,len(NODE_PDR_value)):
            plt.ylabel(DATATYPE_LIST[2])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0,len(NODE_PDR_value[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                neigh_add = NEIGH_add_rx[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(NODE_PDR_value[i][j])):
                    #Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add_rx[node_index].index(NODE_index[i])
                    #As such the corresponding data received was sent by node_index to my_index
                    #PDR_data.append(PACKETS_received[i][j][k]/PACKETS_sent[node_index][my_index][k])
                    if (NODE_PDR_value[node_index][my_index][k] and NODE_PDR_value[i][j][k]):
                        CETX_data.append(1/(NODE_PDR_value[i][j][k]*NODE_PDR_value[node_index][my_index][k]))
                    else:
                        CETX_data.append(0)
                plt.plot(X_axis, CETX_data, LINE_COLORS[j])
                holder.append(CETX_data)
            NODE_ETX_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[2] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[5] + " ###########")
        #Now plotting the Throughput data
        for i in range(0,len(Dest_RX_Amount_average)):
            plt.ylabel(DATATYPE_LIST[5])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            client_add = 100
            # Define the RX holder
            RX_holder = []
            legend.append("Client " + str(client_add))
            for j in range(0,len(Dest_RX_Amount_average[i])):
                # for k in range(0,len(Dest_RX_Amount[i][j])):
                RX_holder.append(Dest_RX_Amount_average[i][j])
            plt.plot(X_axis, RX_holder, LINE_COLORS[i])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[5] + "_for_destination_"+str(DEST_add[i])+".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[7] + " ###########")
        #Now plotting the MDR data
        for i in range(0,len(Client_TX_Amount_average)):
            plt.ylabel(DATATYPE_LIST[7])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            dest_add = 130
            # Define the mdr holder
            MDR_holder = []
            legend.append("Client " + str(client_add))
            for j in range(0,len(Client_TX_Amount_average[i])):
                #Obtain index of the current client the measurements were received from
                dest_index = DEST_add.index(dest_add)
                # Obtain index of the current destination in the client's destination index
                my_index = 0
                #As such the corresponding data received was received by dest_index from my_index
                if (Client_TX_Amount_average[i][j]!=0):
                    MDR_holder.append(Dest_RX_Amount_average[dest_index][my_index]/Client_TX_Amount_average[i][j])
                else:
                    MDR_holder.append(0)
            plt.plot(X_axis, MDR_holder, LINE_COLORS[i])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[7] + "_for_client_"+str(CLIENT_add[i])+".pdf")
            plt.show()
            plt.close()


        print("########### Plotting " + DATATYPE_LIST[8] + " ###########")
        DST_Network = nx.DiGraph()
        G = Update_Destination_Graph(NEIGH_add_rx)
        DST_Network.update(G)
        Display_Destination_Graph(DST_Network)





    if AOMDV:
        # STores the PDR for each link between node x and neighbour y
        NODE_PDR_value = []
        # What test are we doing????
        current_test = 1
        print("#### Starting AOMDV Simulations ########")
        #Defines the amount of missed hallo
        HALLO_TIMEOUT = 4
        # Store the addresses here
        # Address index corresponds to index of the measured node
        NODE_index = [100, 110, 120, 130]
        # Defines when the Node started within the 1 second gap
        NODE_Start = []
        # Defines when the node sends Hallo
        NODE_Hallo = []
        # Defines when Client sends message
        CLIENT_tx = []
        # Stores the routing table next hop entries for each node for a given destination
        DESTINATION_ROUTING_table_next = [[[120,110]], [[130,120]], [[130,110]], [[130]]]
        # STores the next hop for the chosen path
        DESTINATION_ROUTING_table_path = [[[120]], [[130]], [[130]], [[130]]]
        # STores amount messages sent per second uplink
        NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # STores amount messages received per second downlink
        NEIGH_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # STores amount hallo received per second downlink
        # If this amount is not at least hallo freq then link breaks
        HALLO_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        #Defines the hallo counter
        HALLO_counter = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # On next tick if the index to the right is lower then left then feed forward the message.
        MESSAGE_rx = [0, 0, 0, 0]
        # Defines when client sent message
        MESSAGE_tx = [0]
        # Defines when destination received message
        DEST_MESSAGE_rx = [0]
        # Defines how many messages I actually sent
        NODE_tx = [0, 0, 0, 0]
        # Defines messages I actually received
        NODE_rx = [0, 0, 0, 0]
        # Store neighbour addresses here
        #Define two, one for what the node actually knows and one for what neighbours can receive any message
        #This is what the node knows
        NEIGH_add_tx = [[110, 120], [100, 120, 130], [100, 110, 130], [110, 120]]
        #This is what the modal knows
        NEIGH_add_rx = [[110, 120], [100, 120, 130], [100, 110, 130], [110, 120]]
        # Stores the distance between the node and it's neighbour (m)
        NEIGH_add_distance = [[10, 10], [10, 10, 10], [10, 10, 10], [10, 10]]
        # Store the average SNR of received link rememeber this is again unsigned???? makes sure dB
        SNR_value = [[10, 10], [10, 10, 10], [10, 10, 10], [10, 10]]
        # Hallo time outs
        hallo_time_out = 0
        # Store destination address here
        DEST_add = [130]

        # STores client addresses here
        CLIENT_add = [100]
        # Initialize measurement arrays
        # This will keep track of a change in message receive and reply
        MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
        # Store the loads here
        LOAD_array = []
        for i in range(0, len(NODE_index)):
            LOAD_array.append([])

        #Store the averaging amount
        LOAD_array_average = []
        for i in range(0, len(NODE_index)):
            holder = []
            for j in range(0,time_length):
                holder.append(0)
        LOAD_array_average.append(holder)
        LOAD_array_average = np.array(LOAD_array_average)

        #Store average for amount of packets
        PACKETS_sent_average = []
        for i in range(0, len(NEIGH_tx)):
            holder = []
            for j in range(0,len(NEIGH_tx[i])):
                holder_two = []
                for k in range(0,time_length):
                    holder_two.append(0)
                holder.append(holder_two)
            PACKETS_sent_average.append(holder)
        PACKETS_sent_average = PACKETS_sent_average


        # Store amount of packets sent here
        PACKETS_sent = []
        for i in range(0, len(NEIGH_tx)):
            holder = []
            for j in range(len(NEIGH_tx[i])):
                holder.append([])
            PACKETS_sent.append(holder)

        # Store average amount of packets received
        PACKETS_receive_average = []
        for i in range(0, len(NEIGH_rx)):
            holder = []
            for j in range(0,len(NEIGH_rx[i])):
                holder_two = []
                for k in range(0,time_length):
                    holder_two.append(0)
                holder.append(holder_two)
            PACKETS_receive_average.append(holder)
        PACKETS_receive_average = PACKETS_receive_average


        # Store amount of packets received here
        PACKETS_received = []
        for i in range(0, len(NEIGH_rx)):
            holder = []
            for j in range(len(NEIGH_rx[i])):
                holder.append([])
            PACKETS_received.append(holder)

        #Storing client tx average amount
        Client_TX_Amount_average = []
        for i in range(0, len(CLIENT_add)):
            holder = []
            for j in range(0,time_length):
                holder.append(0)
            Client_TX_Amount_average.append(holder)
        Client_TX_Amount_average = np.array(Client_TX_Amount_average)


        Client_TX_Amount = []
        for i in range(0, len(CLIENT_add)):
            Client_TX_Amount.append([])

        #Storing dest rx average amount
        Dest_RX_Amount_average = []
        for i in range(0, len(DEST_add)):
            holder = []
            for j in range(0,time_length):
                holder.append(0)
            Dest_RX_Amount_average.append(holder)
        Dest_RX_Amount_average = np.array(Dest_RX_Amount_average)


        # Stores the amount of message packets received per epoch
        Dest_RX_Amount = []
        for i in range(0, len(DEST_add)):
            Dest_RX_Amount.append([])

        # Set up the times when the nodes have started
        for i in range(0, len(NODE_index)):
            NODE_Start.append(int(np.random.uniform() * amount_symbols))
        print("#### FINISHED INITIAL VALUES   #########")
        print(NODE_Start)
        # Set up when the hallo messages started
        # Typically the node will send the hallo when it has started but allow for some variance
        for i in range(0, len(NODE_index)):
            number = (int(np.random.uniform() * 5 + NODE_Start[i])) % amount_symbols
            # Cant have these equal
            while number in NODE_Start:
                number = (int(np.random.uniform() * 5 + NODE_Start[i])) % amount_symbols
            NODE_Hallo.append(number)

        print("#### FINISHED HALLO TIMERS   #########")
        print(NODE_Hallo)
        # Now setup when the client sends a message make sure not in the time's of itself
        for i in range(0, len(CLIENT_add)):
            number = int(np.random.uniform() * amount_symbols)
            while (number == NODE_Start[NODE_index.index(CLIENT_add[i])]) or (
                    number == NODE_Start[NODE_index.index(CLIENT_add[i])]):
                number = int(np.random.uniform() * amount_symbols)
            CLIENT_tx.append(number)
        print("#### FINISHED CLIENT TIMERS   #########")
        print(CLIENT_tx)
        # Some assunptions made for now. Now RREQ messages or RREP yet only HALLO and MAIN message for now
        # PATHS have been initialized already thus the client starts sending a message
        for b in range(0, repititions):
            for i in range(0, time_length):
                # Initialize the events each second
                if i > 0:
                    # Only do this after the first time stepFF
                    # First check if no hallo timer has been missed
                    # Repeat until flag is down
                    flag = True
                    removal_neigh = []
                    for t in range(0, len(HALLO_rx)):
                        removal_neigh_holder = []
                        for g in range(0, len(HALLO_rx[t])):
                            if HALLO_rx[t][g] < hallo_freq / 2:
                                #Add missed coiunter
                                HALLO_counter[t][g]+=1
                                if HALLO_counter[t][g] == HALLO_TIMEOUT:
                                    # Remove the neighbour from the neighbour list
                                    hallo_time_out += 1
                                    removal_neigh_holder.append(NEIGH_add_rx[t][g])
                                    #Reset counter
                                    HALLO_counter[t][g] = 0
                        removal_neigh.append(removal_neigh_holder)
                    # After all nodes been obtained that needs deletion start removing
                    for t in range(0, len(removal_neigh)):
                        for g in range(0, len(removal_neigh[t])):
                            if removal_neigh[t][g] in NEIGH_add_tx[t]:
                                NEIGH_add_tx[t].remove(removal_neigh[t][g])
                HALLO_rx = []
                for t in range(0, len(NEIGH_add_rx)):
                    holder = []
                    for g in range(0, len(NEIGH_add_rx[t])):
                        holder.append(0)
                    HALLO_rx.append(holder)
                for j in range(0, amount_symbols):
                    # Reset the checker
                    # STores amount hallo received per second downlink
                    # If this amount is not at least hallo freq then link breaks
                    # Here we will propagate the sent message with the nodes
                    for t in range(0, len(MESSAGE_rx)):
                        if ((MESSAGE_rx[t] - MESSAGE_RX_PREV[t] > 0) and (NODE_index[t] not in CLIENT_add) and (
                                NODE_index[t] not in DEST_add)):
                            # This means the node received a message previously now forward it
                            # This node then sends a hallo
                            node_index = t
                            # Define who it sends to
                            # Define who it sends to
                            # Local neighbour list
                            local_neigh = NEIGH_add_tx[node_index]
                            tx = NODE_tx[node_index]
                            rx = NODE_rx[node_index]
                            # Sends a hallo to each
                            # COunts as one message
                            # Obtain the current traffic for the node
                            traffic = tx + rx
                            # TODO make this more general
                            # Define the next hop
                            target = DESTINATION_ROUTING_table_path[node_index][0][0]
                            target_index = NODE_index.index(target)
                            # Update my tx
                            NODE_tx[node_index] += 1
                            #Obtain neighbour index in tx
                            if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[target_index])
                                NEIGH_tx[node_index][neigh_target_index] += 1
                            traffic = NODE_tx[target_index] + NODE_rx[target_index]
                            if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                # CHeck if there is a path
                                if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                    #We essentially checked if the next hop neighbour is in the neighbour table,
                                    # we then check if the neighbour exists in tx. If not we ignore it
                                    #NEighbours can only be learned through hallo to esnuree they are trusted
                                    MESSAGE_rx[target_index] += 1
                                    NODE_rx[target_index] += 1
                                    if NODE_index[target_index] in DEST_add:
                                        DEST_MESSAGE_rx[DEST_add.index(NODE_index[target_index])] += 1
                                    rx_index = NEIGH_add_rx[target_index].index(NODE_index[node_index])
                                    NEIGH_rx[target_index][rx_index] += 1
                                else:
                                    # This means the node could not find a path as such look for an extra path
                                    # TODO make more dynamic
                                    # Define the index of the destination
                                    dst_index = 0
                                    route_next = DESTINATION_ROUTING_table_next[node_index][dst_index]
                                    # Set true to check for another path if can be taken
                                    bool = True
                                    i = 0
                                    while ((bool) and (i < len(route_next))):
                                        if (route_next[i] != target):
                                            # Try to see if we can yse this path
                                            new_target = route_next[i]
                                            new_target_index = NODE_index.index(new_target)
                                            if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                                neigh_target_index = NEIGH_add_tx[node_index].index(
                                                    NODE_index[new_target_index])
                                                NEIGH_tx[node_index][neigh_target_index] += 1
                                            traffic = NODE_tx[new_target_index] + NODE_rx[new_target_index]
                                            if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                                if (NODE_index[new_target_index] in NEIGH_add_tx[node_index]):
                                                    # Message went through
                                                    MESSAGE_rx[new_target_index] += 1
                                                    NODE_rx[new_target_index] += 1
                                                    if NODE_index[new_target_index] in DEST_add:
                                                        DEST_MESSAGE_rx[DEST_add.index(NODE_index[new_target_index])] += 1
                                                    # Update rx
                                                    rx_index = NEIGH_add_rx[new_target_index].index(NODE_index[node_index])
                                                    NEIGH_rx[new_target_index][rx_index] += 1
                                                    bool = False
                                                    # Alsoe update path table
                                                    # TODO make more dynamic
                                                    #Remove this so it does not get stuck in a loop
                                                    #DESTINATION_ROUTING_table_path[node_index][0][0] = new_target
                                        i += 1
                    # Make a prev copy again
                    MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
                    # Initializes the amount for smallest possible time step
                    if j in NODE_Hallo:
                        # This node then sends a hallo
                        node_index = NODE_Hallo.index(j)

                        # Define who it sends to
                        # Local neighbour list
                        local_neigh = NEIGH_add_tx[node_index]
                        tx = NODE_tx[node_index]
                        rx = NODE_rx[node_index]
                        # Sends a hallo to each
                        # COunts as one message
                        # Obtain the current traffic for the node
                        traffic = tx + rx
                        # Update my tx
                        NODE_tx[node_index] += 1

                        for k in range(0, len(local_neigh)):
                            # UPdate tx
                            NEIGH_tx[node_index][k] += 1
                            temp_index = NODE_index.index(local_neigh[k])
                            traffic = NODE_rx[temp_index] + NODE_rx[temp_index]
                            if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                # Message went through
                                NODE_rx[NODE_index.index(NEIGH_add_rx[node_index][k])] += 1
                                if (NODE_index[node_index] not in NEIGH_add_tx[NODE_index.index(NEIGH_add_rx[node_index][k])]):
                                    # Append me to the neighbour list
                                    NEIGH_add_tx[NODE_index.index(NEIGH_add_rx[node_index][k])].append(NODE_index[node_index])
                                    #HALLO_rx[NODE_index.index(NEIGH_add_rx[node_index][k])].append(NODE_index[node_index])
                                # Update rx
                                node_neigh_index = NODE_index.index(local_neigh[k])
                                rx_index = NEIGH_add_rx[node_neigh_index].index(NODE_index[node_index])
                                NEIGH_rx[node_neigh_index][rx_index] += 1
                                HALLO_rx[node_neigh_index][rx_index] += 1
                                #Reset counter
                                HALLO_counter[node_neigh_index][rx_index] = 0
                        # Update timer for hallo
                        NODE_Hallo[NODE_Hallo.index(j)] = int(
                            (NODE_Hallo[NODE_Hallo.index(j)] + amount_symbols / hallo_freq) % amount_symbols)
                    if j in CLIENT_tx:
                        # This node then sends a hallo
                        node_index = NODE_index.index(CLIENT_add[CLIENT_tx.index(j)])
                        # Define who it sends to
                        # Define who it sends to
                        # Local neighbour list
                        local_neigh = NEIGH_add_tx[node_index]
                        tx = NODE_tx[node_index]
                        rx = NODE_rx[node_index]
                        # Sends a hallo to each
                        # COunts as one message
                        # Obtain the current traffic for the node
                        traffic = tx + rx
                        # TODO make this more general
                        # Define the next hop
                        target = DESTINATION_ROUTING_table_path[node_index][0][0]
                        target_index = NODE_index.index(DESTINATION_ROUTING_table_path[node_index][0][0])
                        # Update my tx
                        NODE_tx[node_index] += 1
                        # UPdate tx
                        MESSAGE_tx[node_index] += 1
                        if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                            neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[target_index])
                            NEIGH_tx[node_index][neigh_target_index] += 1
                        traffic = NODE_tx[target_index] + NODE_rx[target_index]
                        if not (is_collide(collision(traffic*(PACKET_LENGTH+PREAMBLE_BYTE) , 1))):
                            if (NODE_index[target_index] in NEIGH_add_tx[node_index]):
                                    # Message went through
                                MESSAGE_rx[target_index] += 1
                                NODE_rx[target_index] += 1
                                    # Update rx
                                rx_index = NEIGH_add_rx[target_index].index(NODE_index[node_index])
                                NEIGH_rx[target_index][rx_index] += 1
                            else:
                                #This means the node could not find a path as such look for an extra path
                                #TODO make more dynamic
                                #Define the index of the destination
                                dst_index = 0
                                route_next = DESTINATION_ROUTING_table_next[node_index][dst_index]
                                #Set true to check for another path if can be taken
                                bool = True
                                i = 0
                                while ((bool) and (i<len(route_next))):
                                    if (route_next[i] != target):
                                        #Try to see if we can yse this path
                                        new_target = route_next[i]
                                        new_target_index = NODE_index.index(new_target)
                                        if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                            neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[new_target_index])
                                            NEIGH_tx[node_index][neigh_target_index] += 1
                                        traffic = NODE_tx[new_target_index] + NODE_rx[new_target_index]
                                        if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                            if (NODE_index[new_target_index] in NEIGH_add_tx[node_index]):
                                                # Message went through
                                                MESSAGE_rx[new_target_index] += 1
                                                NODE_rx[new_target_index] += 1
                                                # Update rx
                                                rx_index = NEIGH_add_rx[new_target_index].index(NODE_index[node_index])
                                                NEIGH_rx[new_target_index][rx_index] += 1
                                                bool = False
                                                #Alsoe update path table
                                                #TODO make more dynamic
                                                DESTINATION_ROUTING_table_path[node_index][0][0] = new_target
                                    i+=1

                        # Update timer for message
                        CLIENT_tx[CLIENT_tx.index(j)] = int(
                            (CLIENT_tx[CLIENT_tx.index(j)] + amount_symbols / packet_freq) % amount_symbols)
                # After all events have been driven create a time stamp array similar to what is done for the measurement model
                # Save Loads
                for s in range(0, len(NODE_rx)):
                    LOAD_array[s].append(NODE_rx[s] + NODE_tx[s])
                # Save packets sent
                for s in range(0, len(NEIGH_tx)):
                    for l in range(0, len(NEIGH_tx[s])):
                        PACKETS_sent[s][l].append(NEIGH_tx[s][l])
                # Save packets received
                for s in range(0, len(NEIGH_rx)):
                    for l in range(0, len(NEIGH_rx[s])):
                        PACKETS_received[s][l].append(NEIGH_rx[s][l])
                for s in range(0, len(MESSAGE_tx)):
                    Client_TX_Amount[s].append(MESSAGE_tx[s])
                # TODO MAKE THIS MORE DYNAMIC
                Dest_RX_Amount[0].append(DEST_MESSAGE_rx[0])
                # Now clear the trackers
                # STores amount messages sent per second uplink
                NEIGH_tx = []
                for h in range(0,len(NEIGH_add_rx)):
                    NEIGH_tx_holder = []
                    for y in range(0,len(NEIGH_add_rx[h])):
                        NEIGH_tx_holder.append(0)
                    NEIGH_tx.append(NEIGH_tx_holder)
                # STores amount messages received per second downlink
                NEIGH_rx = []
                for h in range(0,len(NEIGH_add_rx)):
                    NEIGH_rx_holder = []
                    for y in range(0,len(NEIGH_add_rx[h])):
                        NEIGH_rx_holder.append(0)
                    NEIGH_rx.append(NEIGH_rx_holder)
                # Defines when client sent message
                MESSAGE_tx = []
                for h in range(0,len(CLIENT_add)):
                    MESSAGE_tx.append(0)
                #Defines when destination received a message
                DEST_MESSAGE_rx = []
                for h in range(0,len(DEST_add)):
                    DEST_MESSAGE_rx.append(0)
                # Defines how many messages I actually sent
                NODE_tx = []
                for h in range(0,len(NODE_index)):
                    NODE_tx.append(0)
                # Defines messages I actually received
                NODE_rx = []
                for h in range(0, len(NODE_index)):
                    NODE_rx.append(0)
            LOAD_array_average = LOAD_array_average + np.array(LOAD_array)
            #Add arrays together
            for q in range(0,len(PACKETS_sent_average)):
                for e in range(0,len(PACKETS_sent_average[q])):
                    for a in range(len(PACKETS_sent_average[q][e])):
                        PACKETS_sent_average[q][e][a] = PACKETS_sent_average[q][e][a] + PACKETS_sent[q][e][a]
            for q in range(0,len(PACKETS_receive_average)):
                for e in range(0,len(PACKETS_receive_average[q])):
                    for a in range(len(PACKETS_receive_average[q][e])):
                        PACKETS_receive_average[q][e][a] = PACKETS_receive_average[q][e][a] + PACKETS_received[q][e][a]
            Dest_RX_Amount_average = Dest_RX_Amount_average + np.array(Dest_RX_Amount)
            Client_TX_Amount_average = Client_TX_Amount_average + np.array(Client_TX_Amount)
            # Reset all normal trackers
            # Store the loads here
            LOAD_array = []
            for i in range(0, len(NODE_index)):
                LOAD_array.append([])
            # Store amount of packets sent here
            PACKETS_sent = []
            for i in range(0, len(NEIGH_tx)):
                holder = []
                for j in range(len(NEIGH_tx[i])):
                    holder.append([])
                PACKETS_sent.append(holder)
            # Store amount of packets received here
            PACKETS_received = []
            for i in range(0, len(NEIGH_rx)):
                holder = []
                for j in range(len(NEIGH_rx[i])):
                    holder.append([])
                PACKETS_received.append(holder)
            # SToring client tx amount
            Client_TX_Amount = []
            for i in range(0, len(CLIENT_add)):
                Client_TX_Amount.append([])
            # Stores the amount of message packets received per epoch
            Dest_RX_Amount = []
            for i in range(0, len(DEST_add)):
                Dest_RX_Amount.append([])
            # STores amount messages sent per second uplink
            NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # STores amount messages received per second downlink
            NEIGH_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            HALLO_counter = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # STores amount hallo received per second downlink
            # If this amount is not at least hallo freq then link breaks
            HALLO_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # On next tick if the index to the right is lower then left then feed forward the message.
            MESSAGE_rx = [0, 0, 0, 0]
            # Defines when client sent message
            MESSAGE_tx = [0]
            # Defines when destination received message
            DEST_MESSAGE_rx = [0]
            # Defines how many messages I actually sent
            NODE_tx = [0, 0, 0, 0]
            # Defines messages I actually received
            NODE_rx = [0, 0, 0, 0]


        #Now average out the arrays
        LOAD_array_average = 1/repititions * LOAD_array_average
        for q in range(0, len(PACKETS_sent_average)):
            for e in range(0, len(PACKETS_sent_average[q])):
                for a in range(len(PACKETS_sent_average[q][e])):
                    PACKETS_sent_average[q][e][a] = PACKETS_sent_average[q][e][a] * 1/repititions
        for q in range(0, len(PACKETS_receive_average)):
            for e in range(0, len(PACKETS_receive_average[q])):
                for a in range(len(PACKETS_receive_average[q][e])):
                    PACKETS_receive_average[q][e][a] = PACKETS_receive_average[q][e][a] *1/repititions
        Dest_RX_Amount_average = 1/repititions * Dest_RX_Amount_average
        Client_TX_Amount_average = 1/repititions * Client_TX_Amount_average

        print(LOAD_array_average)
        print(PACKETS_sent_average)
        print(PACKETS_receive_average)
        print(Dest_RX_Amount_average)
        print(hallo_time_out)
        print("########### Starting Plotting Data ###########")
        #Print the load data
        print("########### Plotting "+DATATYPE_LIST[0]+" ###########")
        plt.ylabel(DATATYPE_LIST[0])
        plt.xlabel("Time (s)")
        # fig.tight_layout()
        plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
        plt.grid(True)
        #Obtaining the legend array
        legend = []
        for i in range (0,len(NODE_index)):
            legend.append("Node "+str(NODE_index[i]))
        for i in range(0,len(LOAD_array_average)):
            plt.plot(X_axis,LOAD_array_average[i],LINE_COLORS[i])
        plt.legend(legend)
        plt.savefig(test_array[current_test]+measurement_array[0]+".pdf")
        plt.show()
        plt.close()
        #Print the load data
        print("########### Plotting " + DATATYPE_LIST[1] + " ###########")
        #Now plotting the PDR data
        for i in range(0,len(PACKETS_receive_average)):
            plt.ylabel(DATATYPE_LIST[1])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0,len(PACKETS_receive_average[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                neigh_add = NEIGH_add_rx[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(PACKETS_receive_average[i][j])):
                    #Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add_rx[node_index].index(NODE_index[i])
                    #As such the corresponding data received was sent by node_index to my_index
                    if (PACKETS_sent_average[node_index][my_index][k]!=0):
                        PDR_data.append(PACKETS_receive_average[i][j][k]/PACKETS_sent_average[node_index][my_index][k])
                    else:
                        PDR_data.append(0)
                    #CETX_data.append(1/(PACKETS_received[i][j][k]*PACKETS_sent[node_index][my_index][k]))
                plt.plot(X_axis, PDR_data, LINE_COLORS[j])
                holder.append(PDR_data)
            NODE_PDR_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[1] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[2] + " ###########")
        #Now plotting the ETX data
        for i in range(0,len(NODE_PDR_value)):
            plt.ylabel(DATATYPE_LIST[2])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0,len(NODE_PDR_value[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                print(NEIGH_add_rx)
                print(len(PDR_data))
                print(NEIGH_add_rx[i][j])
                print(i)
                print(j)
                neigh_add = NEIGH_add_rx[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(NODE_PDR_value[i][j])):
                    #Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add_rx[node_index].index(NODE_index[i])
                    #As such the corresponding data received was sent by node_index to my_index
                    #PDR_data.append(PACKETS_received[i][j][k]/PACKETS_sent[node_index][my_index][k])
                    if (NODE_PDR_value[node_index][my_index][k] and NODE_PDR_value[i][j][k]):
                        CETX_data.append(1/(NODE_PDR_value[i][j][k]*NODE_PDR_value[node_index][my_index][k]))
                    else:
                        CETX_data.append(0)
                plt.plot(X_axis, CETX_data, LINE_COLORS[j])
                holder.append(CETX_data)
            NODE_ETX_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[2] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[5] + " ###########")
        #Now plotting the Throughput data
        for i in range(0,len(Dest_RX_Amount_average)):
            plt.ylabel(DATATYPE_LIST[5])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            client_add = 100
            # Define the RX holder
            RX_holder = []
            legend.append("Client " + str(client_add))
            for j in range(0,len(Dest_RX_Amount_average[i])):
                # for k in range(0,len(Dest_RX_Amount[i][j])):
                RX_holder.append(Dest_RX_Amount_average[i][j])
            plt.plot(X_axis, RX_holder, LINE_COLORS[i])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[5] + "_for_destination_"+str(DEST_add[i])+".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[7] + " ###########")
        #Now plotting the MDR data
        for i in range(0,len(Client_TX_Amount_average)):
            plt.ylabel(DATATYPE_LIST[7])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            dest_add = 130
            # Define the mdr holder
            MDR_holder = []
            legend.append("Client " + str(client_add))
            for j in range(0,len(Client_TX_Amount_average[i])):
                #Obtain index of the current client the measurements were received from
                dest_index = DEST_add.index(dest_add)
                # Obtain index of the current destination in the client's destination index
                my_index = 0
                #As such the corresponding data received was received by dest_index from my_index
                if (Client_TX_Amount_average[i][j]!=0):
                    MDR_holder.append(Dest_RX_Amount_average[dest_index][my_index]/Client_TX_Amount_average[i][j])
                else:
                    MDR_holder.append(0)
            plt.plot(X_axis, MDR_holder, LINE_COLORS[i])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[7] + "_for_client_"+str(CLIENT_add[i])+".pdf")
            plt.show()
            plt.close()


        print("########### Plotting " + DATATYPE_LIST[8] + " ###########")
        DST_Network = nx.DiGraph()
        G = Update_Destination_Graph(NEIGH_add_rx)
        DST_Network.update(G)
        Display_Destination_Graph(DST_Network)

    if AOMDV_LB:
        # STores the PDR for each link between node x and neighbour y
        NODE_PDR_value = []

        # What test are we doing????
        current_test = 2
        print("#### Starting AOMDV Simulations ########")
        # Defines the amount of missed hallo
        HALLO_TIMEOUT = 4
        # Store the addresses here
        # Address index corresponds to index of the measured node
        NODE_index = [100, 110, 120, 130]
        # Defines when the Node started within the 1 second gap
        NODE_Start = []
        # Defines when the node sends Hallo
        NODE_Hallo = []
        # Defines when Client sends message
        CLIENT_tx = []
        # Stores the routing table next hop entries for each node for a given destination
        DESTINATION_ROUTING_table_next = [[[120, 110]], [[130]], [[130]], [[130]]]
        # STores the next hop for the chosen path
        DESTINATION_ROUTING_table_path = [[[120]], [[130]], [[130]], [[130]]]
        # STores amount messages sent per second uplink
        NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # STores amount messages received per second downlink
        NEIGH_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # STores amount hallo received per second downlink
        # If this amount is not at least hallo freq then link breaks
        HALLO_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # Defines the hallo counter
        HALLO_counter = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
        # On next tick if the index to the right is lower then left then feed forward the message.
        MESSAGE_rx = [0, 0, 0, 0]
        # Defines when client sent message
        MESSAGE_tx = [0]
        # Defines when destination received message
        DEST_MESSAGE_rx = [0]
        # Defines how many messages I actually sent
        NODE_tx = [0, 0, 0, 0]
        # Defines messages I actually received
        NODE_rx = [0, 0, 0, 0]
        # Store neighbour addresses here
        # Define two, one for what the node actually knows and one for what neighbours can receive any message
        # This is what the node knows
        NEIGH_add_tx = [[110, 120], [100, 120, 130], [100, 110, 130], [110, 120]]
        # This is what the modal knows
        NEIGH_add_rx = [[110, 120], [100, 120, 130], [100, 110, 130], [110, 120]]
        # Stores the distance between the node and it's neighbour (m)
        NEIGH_add_distance = [[10, 10], [10, 10, 10], [10, 10, 10], [10, 10]]
        # Store the average SNR of received link rememeber this is again unsigned???? makes sure dB
        SNR_value = [[10, 10], [10, 10, 10], [10, 10, 10], [10, 10]]
        # Hallo time outs
        hallo_time_out = 0
        # Store destination address here
        DEST_add = [130]

        # STores client addresses here
        CLIENT_add = [100]
        # Initialize measurement arrays
        # This will keep track of a change in message receive and reply
        MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
        # Store the loads here
        LOAD_array = []
        for i in range(0, len(NODE_index)):
            LOAD_array.append([])

        # Store the averaging amount
        LOAD_array_average = []
        for i in range(0, len(NODE_index)):
            holder = []
            for j in range(0, time_length):
                holder.append(0)
        LOAD_array_average.append(holder)
        LOAD_array_average = np.array(LOAD_array_average)

        # Store average for amount of packets
        PACKETS_sent_average = []
        for i in range(0, len(NEIGH_tx)):
            holder = []
            for j in range(0, len(NEIGH_tx[i])):
                holder_two = []
                for k in range(0, time_length):
                    holder_two.append(0)
                holder.append(holder_two)
            PACKETS_sent_average.append(holder)
        PACKETS_sent_average = PACKETS_sent_average

        # Store amount of packets sent here
        PACKETS_sent = []
        for i in range(0, len(NEIGH_tx)):
            holder = []
            for j in range(len(NEIGH_tx[i])):
                holder.append([])
            PACKETS_sent.append(holder)

        # Store average amount of packets received
        PACKETS_receive_average = []
        for i in range(0, len(NEIGH_rx)):
            holder = []
            for j in range(0, len(NEIGH_rx[i])):
                holder_two = []
                for k in range(0, time_length):
                    holder_two.append(0)
                holder.append(holder_two)
            PACKETS_receive_average.append(holder)
        PACKETS_receive_average = PACKETS_receive_average

        # Store amount of packets received here
        PACKETS_received = []
        for i in range(0, len(NEIGH_rx)):
            holder = []
            for j in range(len(NEIGH_rx[i])):
                holder.append([])
            PACKETS_received.append(holder)

        # Storing client tx average amount
        Client_TX_Amount_average = []
        for i in range(0, len(CLIENT_add)):
            holder = []
            for j in range(0, time_length):
                holder.append(0)
            Client_TX_Amount_average.append(holder)
        Client_TX_Amount_average = np.array(Client_TX_Amount_average)

        Client_TX_Amount = []
        for i in range(0, len(CLIENT_add)):
            Client_TX_Amount.append([])

        # Storing dest rx average amount
        Dest_RX_Amount_average = []
        for i in range(0, len(DEST_add)):
            holder = []
            for j in range(0, time_length):
                holder.append(0)
            Dest_RX_Amount_average.append(holder)
        Dest_RX_Amount_average = np.array(Dest_RX_Amount_average)

        # Stores the amount of message packets received per epoch
        Dest_RX_Amount = []
        for i in range(0, len(DEST_add)):
            Dest_RX_Amount.append([])

        # Set up the times when the nodes have started
        for i in range(0, len(NODE_index)):
            NODE_Start.append(int(np.random.uniform() * amount_symbols))
        print("#### FINISHED INITIAL VALUES   #########")
        print(NODE_Start)
        # Set up when the hallo messages started
        # Typically the node will send the hallo when it has started but allow for some variance
        for i in range(0, len(NODE_index)):
            number = (int(np.random.uniform() * 5 + NODE_Start[i])) % amount_symbols
            # Cant have these equal
            while number in NODE_Start:
                number = (int(np.random.uniform() * 5 + NODE_Start[i])) % amount_symbols
            NODE_Hallo.append(number)

        print("#### FINISHED HALLO TIMERS   #########")
        print(NODE_Hallo)
        # Now setup when the client sends a message make sure not in the time's of itself
        for i in range(0, len(CLIENT_add)):
            number = int(np.random.uniform() * amount_symbols)
            while (number == NODE_Start[NODE_index.index(CLIENT_add[i])]) or (
                    number == NODE_Start[NODE_index.index(CLIENT_add[i])]):
                number = int(np.random.uniform() * amount_symbols)
            CLIENT_tx.append(number)
        print("#### FINISHED CLIENT TIMERS   #########")
        print(CLIENT_tx)
        # Some assunptions made for now. Now RREQ messages or RREP yet only HALLO and MAIN message for now
        # PATHS have been initialized already thus the client starts sending a message
        for b in range(0, repititions):
            for i in range(0, time_length):
                # Initialize the events each second
                if i > 0:
                    # Only do this after the first time step
                    # First check if no hallo timer has been missed
                    # Repeat until flag is down
                    flag = True
                    removal_neigh = []
                    for t in range(0, len(HALLO_rx)):
                        removal_neigh_holder = []
                        for g in range(0, len(HALLO_rx[t])):
                            if HALLO_rx[t][g] < hallo_freq / 2:
                                #Add a counter to HALLO counter
                                HALLO_counter[t][g]+=1
                            # if HALLO_rx[t][g] < 0:
                                # print(HALLO_rx[t][g])
                                if (HALLO_counter[t][g]==HALLO_TIMEOUT):
                                    # Remove the neighbour from the neighbour list
                                    hallo_time_out += 1
                                    removal_neigh_holder.append(NEIGH_add_rx[t][g])
                                    #Reset counter
                                    HALLO_counter[t][g] = 0
                        removal_neigh.append(removal_neigh_holder)
                    # After all nodes been obtained that needs deletion start removing
                    for t in range(0, len(removal_neigh)):
                        for g in range(0, len(removal_neigh[t])):
                            if removal_neigh[t][g] in NEIGH_add_tx[t]:
                                NEIGH_add_tx[t].remove(removal_neigh[t][g])
                HALLO_rx = []
                for t in range(0, len(NEIGH_add_rx)):
                    holder = []
                    for g in range(0, len(NEIGH_add_rx[t])):
                        holder.append(0)
                    HALLO_rx.append(holder)
                for j in range(0, amount_symbols):
                    # Reset the checker
                    # STores amount hallo received per second downlink
                    # If this amount is not at least hallo freq then link breaks
                    # Here we will propagate the sent message with the nodes
                    for t in range(0, len(MESSAGE_rx)):
                        if ((MESSAGE_rx[t] - MESSAGE_RX_PREV[t] > 0) and (NODE_index[t] not in CLIENT_add) and (
                                NODE_index[t] not in DEST_add)):
                            # This means the node received a message previously now forward it
                            # This node then sends a hallo
                            node_index = t
                            # Define who it sends to
                            # Define who it sends to
                            # Local neighbour list
                            local_neigh = NEIGH_add_tx[node_index]
                            tx = NODE_tx[node_index]
                            rx = NODE_rx[node_index]
                            # Sends a hallo to each
                            # COunts as one message
                            # Obtain the current traffic for the node
                            traffic = tx + rx
                            # TODO make this more general
                            # Define the next hop
                            target = DESTINATION_ROUTING_table_path[node_index][0][0]
                            target_index = NODE_index.index(target)
                            # Update my tx
                            NODE_tx[node_index] += 1
                            if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[target_index])
                                NEIGH_tx[node_index][neigh_target_index] += 1
                            # Before the algorithm starts it proceeds to find the traffic for it's neighbours in order of next hop in table
                            traffic_neighbour = []
                            traffic_neigh_add = []
                            for z in range(0, len(DESTINATION_ROUTING_table_next[node_index][0])):
                                if NODE_index[NODE_index.index(DESTINATION_ROUTING_table_next[node_index][0][z])] in \
                                        NEIGH_add_tx[node_index]:
                                    traffic_neighbour.append(NODE_tx[z] + NODE_rx[z])
                                    traffic_neigh_add.append(DESTINATION_ROUTING_table_next[node_index][0][z])
                            # It then selects the neighbour with the lowest traffic
                            lowest = 10000000000
                            lowest_index = 0
                            for z in range(0, len(traffic_neighbour)):
                                if traffic_neighbour[z] < lowest:
                                    lowest = traffic_neighbour[z]
                                    lowest_index = traffic_neigh_add[z]
                            # Once that has been obtained it then obtains the new target address
                            if (lowest_index!=0):
                                #If none found the normal AOMDV malgorithm will handle the error
                                target = lowest_index
                                target_index = NODE_index.index(lowest_index)
                                # Obtain the load for the target address
                                target_load = NODE_tx[target_index] + NODE_rx[target_index]

                            if not (is_collide(collision(target_load *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                # CHeck if there is a path
                                if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                    #We essentially checked if the next hop neighbour is in the neighbour table,
                                    # we then check if the neighbour exists in tx. If not we ignore it
                                    #NEighbours can only be learned through hallo to esnuree they are trusted
                                    MESSAGE_rx[target_index] += 1
                                    NODE_rx[target_index] += 1
                                    if NODE_index[target_index] in DEST_add:
                                        DEST_MESSAGE_rx[DEST_add.index(NODE_index[target_index])] += 1
                                    rx_index = NEIGH_add_rx[target_index].index(NODE_index[node_index])
                                    NEIGH_rx[target_index][rx_index] += 1
                                else:
                                    # This means the node could not find a path as such look for an extra path
                                    # TODO make more dynamic
                                    # Define the index of the destination
                                    dst_index = 0
                                    route_next = DESTINATION_ROUTING_table_next[node_index][dst_index]
                                    # Set true to check for another path if can be taken
                                    bool = True
                                    i = 0
                                    while ((bool) and (i < len(route_next))):
                                        if (route_next[i] != target):
                                            # Try to see if we can yse this path
                                            new_target = route_next[i]
                                            new_target_index = NODE_index.index(new_target)
                                            if NODE_index[new_target_index] in NEIGH_add_tx[node_index]:
                                                neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[new_target_index])
                                                NEIGH_tx[node_index][neigh_target_index] += 1
                                            if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                                if (NODE_index[new_target_index] in NEIGH_add_tx[node_index]):
                                                    # Message went through
                                                    MESSAGE_rx[new_target_index] += 1
                                                    NODE_rx[new_target_index] += 1
                                                    if NODE_index[new_target_index] in DEST_add:
                                                        DEST_MESSAGE_rx[DEST_add.index(NODE_index[new_target_index])] += 1
                                                    # Update rx
                                                    rx_index = NEIGH_add_rx[new_target_index].index(NODE_index[node_index])
                                                    NEIGH_rx[new_target_index][rx_index] += 1
                                                    bool = False
                                                    # Alsoe update path table
                                                    # TODO make more dynamic
                                                    #Remove this so it does not get stuck in a loop
                                                    #DESTINATION_ROUTING_table_path[node_index][0][0] = new_target
                                        i += 1
                    # Make a prev copy again
                    MESSAGE_RX_PREV = list(np.copy(MESSAGE_rx))
                    # Initializes the amount for smallest possible time step
                    if j in NODE_Hallo:
                        # This node then sends a hallo
                        node_index = NODE_Hallo.index(j)

                        # Define who it sends to
                        # Local neighbour list
                        local_neigh = NEIGH_add_tx[node_index]
                        tx = NODE_tx[node_index]
                        rx = NODE_rx[node_index]
                        # Sends a hallo to each
                        # COunts as one message
                        # Obtain the current traffic for the node
                        traffic = tx + rx
                        # Update my tx
                        NODE_tx[node_index] += 1
                        for k in range(0, len(local_neigh)):
                            # UPdate tx
                            NEIGH_tx[node_index][k] += 1
                            temp_index = NODE_index.index(local_neigh[k])
                            traffic = NODE_tx[temp_index] + NODE_rx[temp_index]
                            if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                # Message went through
                                NODE_rx[NODE_index.index(NEIGH_add_rx[node_index][k])] += 1
                                if (NODE_index[node_index] not in NEIGH_add_tx[NODE_index.index(NEIGH_add_rx[node_index][k])]):
                                    # Append me to the neighbour list
                                    NEIGH_add_tx[NODE_index.index(NEIGH_add_rx[node_index][k])].append(NODE_index[node_index])
                                    #HALLO_rx[NODE_index.index(NEIGH_add_rx[node_index][k])].append(NODE_index[node_index])
                                # Update rx
                                node_neigh_index = NODE_index.index(local_neigh[k])
                                rx_index = NEIGH_add_rx[node_neigh_index].index(NODE_index[node_index])
                                NEIGH_rx[node_neigh_index][rx_index] += 1
                                HALLO_rx[node_neigh_index][rx_index] += 1
                                HALLO_counter[node_neigh_index][rx_index] = 0
                        # Update timer for hallo
                        NODE_Hallo[NODE_Hallo.index(j)] = int(
                            (NODE_Hallo[NODE_Hallo.index(j)] + amount_symbols / hallo_freq) % amount_symbols)
                    if j in CLIENT_tx:
                        # This node then sends a hallo
                        node_index = NODE_index.index(CLIENT_add[CLIENT_tx.index(j)])
                        # Define who it sends to
                        # Define who it sends to
                        # Local neighbour list
                        local_neigh = NEIGH_add_tx[node_index]
                        tx = NODE_tx[node_index]
                        rx = NODE_rx[node_index]
                        # Sends a hallo to each
                        # COunts as one message
                        # Obtain the current traffic for the node
                        traffic = tx + rx
                        # TODO make this more general
                        # Define the next hop
                        target = DESTINATION_ROUTING_table_path[node_index][0][0]
                        target_index = NODE_index.index(DESTINATION_ROUTING_table_path[node_index][0][0])
                        # Update my tx
                        NODE_tx[node_index] += 1
                        # UPdate tx
                        MESSAGE_tx[node_index] += 1
                        if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                            neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[target_index])
                            NEIGH_tx[node_index][neigh_target_index] += 1
                        # Before the algorithm starts it proceeds to find the traffic for it's neighbours in order of next hop in table
                        traffic_neighbour = []
                        traffic_neigh_add = []
                        for z in range(0,len(DESTINATION_ROUTING_table_next[node_index][0])):
                            if NODE_index[NODE_index.index(DESTINATION_ROUTING_table_next[node_index][0][z])] in NEIGH_add_tx[node_index]:
                                traffic_neighbour.append(NODE_tx[z]+NODE_rx[z])
                                traffic_neigh_add.append(DESTINATION_ROUTING_table_next[node_index][0][z])
                        #It then selects the neighbour with the lowest traffic
                        lowest = 10000000000
                        lowest_index = 0
                        for z in range(0,len(traffic_neighbour)):
                            if traffic_neighbour[z]<lowest:
                                lowest = traffic_neighbour[z]
                                lowest_index = traffic_neigh_add[z]
                        #Once that has been obtained it then obtains the new target address
                        if (lowest_index != 0):
                            # If none found the normal AOMDV malgorithm will handle the error
                            target = lowest_index
                            target_index = NODE_index.index(lowest_index)
                            # Obtain the load for the target address
                            target_load = NODE_tx[target_index] + NODE_rx[target_index]
                        if not (is_collide(collision(target_load *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                            if (NODE_index[target_index] in NEIGH_add_tx[node_index]):
                                    # Message went through
                                MESSAGE_rx[target_index] += 1
                                NODE_rx[target_index] += 1
                                    # Update rx
                                rx_index = NEIGH_add_rx[target_index].index(NODE_index[node_index])
                                NEIGH_rx[target_index][rx_index] += 1
                            else:
                                #It should never get into here
                                #This means the node could not find a path as such look for an extra path
                                #TODO make more dynamic
                                #Define the index of the destination
                                dst_index = 0
                                route_next = DESTINATION_ROUTING_table_next[node_index][dst_index]
                                #Set true to check for another path if can be taken
                                bool = True
                                i = 0
                                while ((bool) and (i<len(route_next))):
                                    if (route_next[i] != target):
                                        #Try to see if we can yse this path
                                        new_target = route_next[i]
                                        new_target_index = NODE_index.index(new_target)
                                        if NODE_index[target_index] in NEIGH_add_tx[node_index]:
                                            neigh_target_index = NEIGH_add_tx[node_index].index(NODE_index[new_target_index])
                                            NEIGH_tx[node_index][neigh_target_index] += 1
                                        if not (is_collide(collision(traffic *(PACKET_LENGTH+PREAMBLE_BYTE), 1))):
                                            if (NODE_index[new_target_index] in NEIGH_add_tx[node_index]):
                                                # Message went through
                                                MESSAGE_rx[new_target_index] += 1
                                                NODE_rx[new_target_index] += 1
                                                # Update rx
                                                rx_index = NEIGH_add_rx[new_target_index].index(NODE_index[node_index])
                                                NEIGH_rx[new_target_index][rx_index] += 1
                                                bool = False
                                                #Alsoe update path table
                                                #TODO make more dynamic
                                                DESTINATION_ROUTING_table_path[node_index][0][0] = new_target
                                    i+=1

                        # Update timer for message
                        CLIENT_tx[CLIENT_tx.index(j)] = int(
                            (CLIENT_tx[CLIENT_tx.index(j)] + amount_symbols / packet_freq) % amount_symbols)
                # After all events have been driven create a time stamp array similar to what is done for the measurement model
                # Save Loads
                for s in range(0, len(NODE_rx)):
                    LOAD_array[s].append(NODE_rx[s] + NODE_tx[s])
                # Save packets sent
                for s in range(0, len(NEIGH_tx)):
                    for l in range(0, len(NEIGH_tx[s])):
                        PACKETS_sent[s][l].append(NEIGH_tx[s][l])
                # Save packets received
                for s in range(0, len(NEIGH_rx)):
                    for l in range(0, len(NEIGH_rx[s])):
                        PACKETS_received[s][l].append(NEIGH_rx[s][l])
                for s in range(0, len(MESSAGE_tx)):
                    Client_TX_Amount[s].append(MESSAGE_tx[s])
                # TODO MAKE THIS MORE DYNAMIC
                Dest_RX_Amount[0].append(DEST_MESSAGE_rx[0])
                # Now clear the trackers
                # STores amount messages sent per second uplink
                NEIGH_tx = []
                for h in range(0,len(NEIGH_add_rx)):
                    NEIGH_tx_holder = []
                    for y in range(0,len(NEIGH_add_rx[h])):
                        NEIGH_tx_holder.append(0)
                    NEIGH_tx.append(NEIGH_tx_holder)
                # STores amount messages received per second downlink
                NEIGH_rx = []
                for h in range(0,len(NEIGH_add_rx)):
                    NEIGH_rx_holder = []
                    for y in range(0,len(NEIGH_add_rx[h])):
                        NEIGH_rx_holder.append(0)
                    NEIGH_rx.append(NEIGH_rx_holder)
                # Defines when client sent message
                MESSAGE_tx = []
                for h in range(0,len(CLIENT_add)):
                    MESSAGE_tx.append(0)
                #Defines when destination received a message
                DEST_MESSAGE_rx = []
                for h in range(0,len(DEST_add)):
                    DEST_MESSAGE_rx.append(0)
                # Defines how many messages I actually sent
                NODE_tx = []
                for h in range(0,len(NODE_index)):
                    NODE_tx.append(0)
                # Defines messages I actually received
                NODE_rx = []
                for h in range(0, len(NODE_index)):
                    NODE_rx.append(0)
            LOAD_array_average = LOAD_array_average + np.array(LOAD_array)
            #Add arrays together
            for q in range(0,len(PACKETS_sent_average)):
                for e in range(0,len(PACKETS_sent_average[q])):
                    for a in range(len(PACKETS_sent_average[q][e])):
                        PACKETS_sent_average[q][e][a] = PACKETS_sent_average[q][e][a] + PACKETS_sent[q][e][a]
            for q in range(0,len(PACKETS_receive_average)):
                for e in range(0,len(PACKETS_receive_average[q])):
                    for a in range(len(PACKETS_receive_average[q][e])):
                        PACKETS_receive_average[q][e][a] = PACKETS_receive_average[q][e][a] + PACKETS_received[q][e][a]
            Dest_RX_Amount_average = Dest_RX_Amount_average + np.array(Dest_RX_Amount)
            Client_TX_Amount_average = Client_TX_Amount_average + np.array(Client_TX_Amount)
            # Reset all normal trackers
            # Store the loads here
            LOAD_array = []
            for i in range(0, len(NODE_index)):
                LOAD_array.append([])
            # Store amount of packets sent here
            PACKETS_sent = []
            for i in range(0, len(NEIGH_tx)):
                holder = []
                for j in range(len(NEIGH_tx[i])):
                    holder.append([])
                PACKETS_sent.append(holder)
            # Store amount of packets received here
            PACKETS_received = []
            for i in range(0, len(NEIGH_rx)):
                holder = []
                for j in range(len(NEIGH_rx[i])):
                    holder.append([])
                PACKETS_received.append(holder)
            # SToring client tx amount
            Client_TX_Amount = []
            for i in range(0, len(CLIENT_add)):
                Client_TX_Amount.append([])
            # Stores the amount of message packets received per epoch
            Dest_RX_Amount = []
            for i in range(0, len(DEST_add)):
                Dest_RX_Amount.append([])
            # STores amount messages sent per second uplink
            NEIGH_tx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # STores amount messages received per second downlink
            NEIGH_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            HALLO_counter = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # STores amount hallo received per second downlink
            # If this amount is not at least hallo freq then link breaks
            HALLO_rx = [[0, 0], [0, 0, 0], [0, 0, 0], [0, 0]]
            # On next tick if the index to the right is lower then left then feed forward the message.
            MESSAGE_rx = [0, 0, 0, 0]
            # Defines when client sent message
            MESSAGE_tx = [0]
            # Defines when destination received message
            DEST_MESSAGE_rx = [0]
            # Defines how many messages I actually sent
            NODE_tx = [0, 0, 0, 0]
            # Defines messages I actually received
            NODE_rx = [0, 0, 0, 0]
            # Now average out the arrays
        LOAD_array_average = 1 / repititions * LOAD_array_average
        for q in range(0, len(PACKETS_sent_average)):
            for e in range(0, len(PACKETS_sent_average[q])):
                for a in range(len(PACKETS_sent_average[q][e])):
                    PACKETS_sent_average[q][e][a] = PACKETS_sent_average[q][e][a] * 1 / repititions
        for q in range(0, len(PACKETS_receive_average)):
            for e in range(0, len(PACKETS_receive_average[q])):
                for a in range(len(PACKETS_receive_average[q][e])):
                    PACKETS_receive_average[q][e][a] = PACKETS_receive_average[q][e][a] * 1 / repititions
        Dest_RX_Amount_average = 1 / repititions * Dest_RX_Amount_average
        Client_TX_Amount_average = 1 / repititions * Client_TX_Amount_average

        print(LOAD_array_average)
        print(PACKETS_sent_average)
        print(PACKETS_receive_average)
        print(Dest_RX_Amount_average)
        print(hallo_time_out)
        print("########### Starting Plotting Data ###########")
        # Print the load data
        print("########### Plotting " + DATATYPE_LIST[0] + " ###########")
        plt.ylabel(DATATYPE_LIST[0])
        plt.xlabel("Time (s)")
        # fig.tight_layout()
        plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
        plt.grid(True)
        # Obtaining the legend array
        legend = []
        for i in range(0, len(NODE_index)):
            legend.append("Node " + str(NODE_index[i]))
        for i in range(0, len(LOAD_array_average)):
            plt.plot(X_axis, LOAD_array_average[i], LINE_COLORS[i])
        plt.legend(legend)
        plt.savefig(test_array[current_test] + measurement_array[0] + ".pdf")
        plt.show()
        plt.close()
        # Print the load data
        print("########### Plotting " + DATATYPE_LIST[1] + " ###########")
        # Now plotting the PDR data
        for i in range(0, len(PACKETS_receive_average)):
            plt.ylabel(DATATYPE_LIST[1])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0, len(PACKETS_receive_average[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                neigh_add = NEIGH_add_rx[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0, len(PACKETS_receive_average[i][j])):
                    # Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add_rx[node_index].index(NODE_index[i])
                    # As such the corresponding data received was sent by node_index to my_index
                    if (PACKETS_sent_average[node_index][my_index][k] != 0):
                        PDR_data.append(
                            PACKETS_receive_average[i][j][k] / PACKETS_sent_average[node_index][my_index][k])
                    else:
                        PDR_data.append(0)
                    # CETX_data.append(1/(PACKETS_received[i][j][k]*PACKETS_sent[node_index][my_index][k]))
                plt.plot(X_axis, PDR_data, LINE_COLORS[j])
                holder.append(PDR_data)
            NODE_PDR_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[1] + "_for_node_" + str(NODE_index[i]) + ".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[2] + " ###########")
        # Now plotting the ETX data
        for i in range(0, len(NODE_PDR_value)):
            plt.ylabel(DATATYPE_LIST[2])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0, len(NODE_PDR_value[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                neigh_add = NEIGH_add_rx[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0, len(NODE_PDR_value[i][j])):
                    # Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add_rx[node_index].index(NODE_index[i])
                    # As such the corresponding data received was sent by node_index to my_index
                    # PDR_data.append(PACKETS_received[i][j][k]/PACKETS_sent[node_index][my_index][k])
                    if (NODE_PDR_value[node_index][my_index][k] and NODE_PDR_value[i][j][k]):
                        CETX_data.append(
                            1 / (NODE_PDR_value[i][j][k] * NODE_PDR_value[node_index][my_index][k]))
                    else:
                        CETX_data.append(0)
                plt.plot(X_axis, CETX_data, LINE_COLORS[j])
                holder.append(CETX_data)
            NODE_ETX_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[2] + "_for_node_" + str(NODE_index[i]) + ".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[5] + " ###########")
        # Now plotting the Throughput data
        for i in range(0, len(Dest_RX_Amount_average)):
            plt.ylabel(DATATYPE_LIST[5])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            client_add = 100
            # Define the RX holder
            RX_holder = []
            legend.append("Client " + str(client_add))
            for j in range(0, len(Dest_RX_Amount_average[i])):
                # for k in range(0,len(Dest_RX_Amount[i][j])):
                RX_holder.append(Dest_RX_Amount_average[i][j])
            plt.plot(X_axis, RX_holder, LINE_COLORS[i])
            plt.legend(legend)
            plt.savefig(
                test_array[current_test] + measurement_array[5] + "_for_destination_" + str(DEST_add[i]) + ".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[7] + " ###########")
        # Now plotting the MDR data
        for i in range(0, len(Client_TX_Amount_average)):
            plt.ylabel(DATATYPE_LIST[7])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            dest_add = 130
            # Define the mdr holder
            MDR_holder = []
            legend.append("Client " + str(client_add))
            for j in range(0, len(Client_TX_Amount_average[i])):
                # Obtain index of the current client the measurements were received from
                dest_index = DEST_add.index(dest_add)
                # Obtain index of the current destination in the client's destination index
                my_index = 0
                # As such the corresponding data received was received by dest_index from my_index
                if (Client_TX_Amount_average[i][j] != 0):
                    MDR_holder.append(Dest_RX_Amount_average[dest_index][my_index] / Client_TX_Amount_average[i][j])
                else:
                    MDR_holder.append(0)
            plt.plot(X_axis, MDR_holder, LINE_COLORS[i])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[7] + "_for_client_" + str(CLIENT_add[i]) + ".pdf")
            plt.show()
            plt.close()

        print("########### Plotting " + DATATYPE_LIST[8] + " ###########")
        DST_Network = nx.DiGraph()
        G = Update_Destination_Graph(NEIGH_add_rx)
        DST_Network.update(G)
        Display_Destination_Graph(DST_Network)

    if GRAPH:
        # load the image
        data_1 = np.load('Collision_data.npy')
        data_2= np.load('Collision_data_STATIONARY.npy')
        data_3 = np.load('Load_data.npy')
        data_4= np.load('Load_data_STATIONARY.npy')
        print(data_3)

        data_3 = 1/44* data_3
        data_4 = 1 / 44 * data_4

        x_axis_1 = []
        for i in range(0,len(data_3)):
            x_axis_1.append(i*2)

        x_axis_2 = []
        for i in range(0,len(data_4)):
            x_axis_2.append(i*2)

        plt.grid()
        plt.xlabel("Time (s)")
        plt.ylabel("Packet Delivery Ratio")
        plt.plot(x_axis_1,data_3)
        plt.savefig("PDR_Driving.pdf")
        plt.show()

        # image = Image.open('img_100x100_1x8bit_B01R20_GRAY_grid_circles_progressive_b.png')
        # # convert image to numpy array
        # data = np.asarray(image)
        # print(data[0])
        # string_array = "{"
        # IMAGE_DATA = []
        # for i in range(0,len(data)):
        #     for j in range(0,len(data[i])):
        #         string_array+=str(data[i][j])+","
        #         IMAGE_DATA.append(data[i][j])
        # string_array+="}"
        # print(string_array)
        # # create Pillow image
        # image2 = Image.fromarray(data)
        # image2.show()
        # IMAGE_ROWS = 5
        # IMAGE_COL = 5
        # # Read in the image data and create and image type. Save and display the image
        # image_data_type = []
        # for q in range(0, IMAGE_ROWS-1):
        #     holder = []
        #     for z in range(0, IMAGE_COL):
        #         holder.append(IMAGE_DATA[(IMAGE_COL) * q + z])
        #     image_data_type.append(holder)
        # image_data_type = np.array(image_data_type)
        # # create Pillow image
        # image2 = Image.fromarray(image_data_type)
        # image2.save("Obtained_Image.png", format="png")
        # image2.show()
        #
        # # Writing the data from the image to a txt file
        # # open text file
        # text_file = open("data.txt", "w")
        #
        # # write string to file
        # line1 = "The Amount Of Missed Indexes = "+"\n"
        # line2 = "The Total Download Time = "+"\n"
        # text_file.writelines([line1, line2])
        # # close file
        # text_file.close()
        #
        #
        #
        #
        #
        # # Gaining the TOA
        # T_symbol = 2 ** 7 / (250*10**3)
        # T_preamble = (8 + 4.25) * T_symbol
        # PACKET_L = 14
        # L_payload = 8 + ((8 * PACKET_L - 4 * 7 + 28 + 16 - 1 * 20) / (4 * 7)) * (1 + 4)
        # T_payload = L_payload * T_symbol
        # TOA = (T_preamble + T_payload)
        #
        # print(TOA)
        # print(channel_cap(55)/8)
        # x_axis = []
        # for i in range(0,int(2000/(PACKET_LENGTH+PREAMBLE_BYTE))):
        #     x_axis.append(i)
        # y_axis = []
        # for i in range(0,len(x_axis)):
        #     y_axis.append(collision(x_axis[i]/8*(PACKET_LENGTH+PREAMBLE_BYTE),1))
        # plt.plot(x_axis,y_axis)
        # plt.show()
        # print(path_loss(0.015)-6)
        # print(TOA*2)
        # Constructing the spreading factors to be testes
        # spreading_factor = [7,8,9,10,11,12]
        # # BW = [125*10**3,250*10**3]
        # x_axis = []
        # # for i in range(0,int(BIT_Rate_Calc(7,BW))):
        # #     x_axis.append(i)
        # # for i in range(0,2000):
        # #     x_axis.append(i)
        # for i in range(0,256-PREAMBLE_BYTE):
        #     x_axis.append(i)
        # results = [[],[],[],[],[],[]]
        # # results = [[], []]
        # # print(spreading_factor)
        # # print(x_axis)
        # # for i in range(0,len(spreading_factor)):
        # #     for j in range(0,len(x_axis)):
        # #         results[i].append(calc_collision(x_axis[j],spreading_factor[i])*100)
        #
        # legend = ["SF7","SF8","SF9","SF10","SF11","SF12"]
        # # legend = ["BW = 125KHz", "BW = 250 KHz"]
        # # for i in range(0,len(BW)):
        # #     for j in spreading_factor:
        # #         results[i].append(BIT_Rate_Calc(j,BW[i]))
        #
        # for i in range(0,len(spreading_factor)):
        #     for j in range(0,len(x_axis)):
        #         results[i].append(TOA_calc(spreading_factor[i],x_axis[j])*1000)
        #
        # # for i in range(0,len(results)):
        # #     plt.plot(spreading_factor,results[i],LINE_COLORS[i])
        # for i in range(0,len(results)):
        #     plt.plot(x_axis,results[i],LINE_COLORS[i])
        # plt.legend(legend)
        # plt.xlabel("Data Packet Size (Bytes)")
        # # plt.xlabel("Current Load (packets/s)")
        # # plt.xlabel("Spreading Factor")
        # plt.ylabel("TOA (ms)")
        # # plt.ylabel("Bit Rate (bits/s)")
        # plt.grid()
        # plt.savefig("TOA_SF.pdf")
        # # plt.savefig("BR_SF.pdf")
        # plt.show()
        #print(TOA_calc(7,PREAMBLE_BYTE+PACKET_LENGTH))




