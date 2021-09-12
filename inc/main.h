#ifndef __MAIN_H__
#define __MAIN_H__
#include "dot_util.h"
#include "RadioEvent.h"


#include <algorithm>  
#include "aodv_neighbours.h"
#include "aodv_queue.h"
#include "aodv_table.h"
#include "network_config.h"
#include "aodv_id_cache.h"
#include "lora_route.h"

///BIG REMEMBER ALWAYS SEND TIME IN SECONDS AND CONVERT TO TIME WHEN RECEIVED
////FINE TO KEEP BIG WHEN IN MEMORY FOR NOW

///////////////////////////////////////////////////////////////////////////////
// QUEUE VARIABLES DEFINED HERE //////////////////////////////////////////////
RequestQueue route_queue = RequestQueue(QUEUE_SIZE, QUEUE_BUFFER_TIME*CLOCKS_PER_SEC/1000);
RequestQueue message_request_queue = RequestQueue(QUEUE_SIZE, QUEUE_BUFFER_TIME*CLOCKS_PER_SEC/1000);

 //////////////////////////////////////////////////////////////////////////////   
// EVENT HANDLERS ////////////////////////////////////////////////////////////

void queue_request_queue_handler(void);
//Function that gets called to handle the equest queue
void request_queue_handler(void);

void queue_message_handler(void);
//Function that gets called to handle the message queue
void message_queue_handler(void);

/////////////////////////////////////////////////////////////////////////////
/////DEVICE ADDRESSING BASED ON WHO THE DEVICE IS //////////////////////////

#if ACTIVE_USER == DESTINATION_NODE
    uint8_t device_ip_address = 100;
    uint8_t destination_ip_address = 100;
#elif ACTIVE_USER == ROUTING_NODE
    uint8_t device_ip_address = 50;
    uint8_t destination_ip_address = 100;
#elif ACTIVE_USER == CLIENT_NODE
    uint8_t device_ip_address = 20;
    uint8_t destination_ip_address = 100;

#endif

//////////////////////////////////////////////////////////////////////////////
//////////MAIN VARIABLES ////////////////////////////////////////////////////

uint8_t m_sequence;
Neighbors myNeighbour = Neighbors(NEIGHBOUR_TIMEOUT*CLOCKS_PER_SEC/1000);
RoutingTable m_routing_table = RoutingTable (MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000);
std::map<uint8_t, uint32_t> m_unreachableDstSeqNo; //keeps track of unreachables for rrer
uint8_t m_requestId;
IdCache m_rreqIdCache = IdCache(DUBLICATE_CACHE_TIMEOUT*CLOCKS_PER_SEC/1000);
uint8_t m_rreqCount;
uint8_t m_rerrCount;
uint8_t m_neighbourCount; //how many tries to reach neighbour

EventQueue main_queue(32 * EVENTS_EVENT_SIZE); //this will call an event in IRQ so the process can be handled safely.
Thread main_thread; //Thread that handles the queue

///////////////////////////////////////////////////////////////////////////////
//////////MAIN FUNCTIONS//////////////////////////////////////////////////////
//Function that waits on radio to finish
void wait_on_radio();

//This is where the initial configurations are made
void start();

//Function that broadcasts hallo message in order to obtain all neighbours
void obtain_neighbours();

//Function to send the initial RREQ packets
//Parameters
//dest address of device to establish a route towards
void send_rreq(uint8_t dest);

//Function to send RREP's
//Parameters
//packet packet from RREQ message that provoked this reply
//toOrigin table entry to route reply to the origin of the RREQ
void SendReply(std::vector<uint8_t> packet , RoutingTableEntry const & toOrigin);

//Send RREP by intermediate node.
//Parameters
//toDst   routing table entry to destination
//toOrigin    routing table entry to originator
//gratRep indicates whether a gratuitous RREP should be unicast to destination
void SendReplyByIntermediateNode (RoutingTableEntry & toDst, RoutingTableEntry & toOrigin, bool gratRep);

//Send RREP_ACK.
//Parameters
//neighbor    neighbor address
void send_reply_ack(uint8_t neighbor_add);

//Send RERR message when no route to forward input packet.
//
//Unicast if there is reverse route to originating node, broadcast otherwise.
//
//Parameters
//dst - destination node IP address
//dstSeqNo    - destination node sequence number
//origin  - originating node IP address
void SendRerrWhenNoRouteToForward(uint8_t dst, uint8_t dstSeqNo, uint8_t origin);

//Initiate RERR.
//
//Parameters
//nextHop next hop address
void SendRerrWhenBreaksLinkToNextHop(uint8_t nextHop);

//Forward RERR.
//
//Parameters
//packet  packet
//precursors  list of addresses of the visited nodes
void SendRerrMessage(std::vector<uint8_t> packet, std::vector< uint8_t > precursors);

//If route exists and is valid, forward packet.
//
//Parameters
//p   the packet to route
//Returns
//true if forwarded
bool forward_message(std::vector<uint8_t> p, uint8_t dst, uint8_t origin);

//Send hello.
void SendHallo();

//Route an input packet (to be forwarded or locally delivered)
//
//This lookup is used in the forwarding process. The packet is handed over to the Ipv4RoutingProtocol, and will get forwarded onward by one of the callbacks. The Linux equivalent is ip_route_input(). There are four valid outcomes, and a matching callbacks to handle each.
//
//Parameters
//p   received packet
//dst destination to be routed to
//origin address of packet origin
//Returns
//true if the Ipv4RoutingProtocol takes responsibility for forwarding or delivering the packet, false otherwise
bool Route_Input(std::vector<uint8_t> p, uint8_t dst, uint8_t origin);

//Function to update sequence number
//type indicates if function called during RREP or RREQ
// seq the equence number that needs to be compared with (during RREP)
void update_node_seq(uint8_t type, uint8_t seq);

//Function to receive a rreq
//Receive RREQ.
//Parameters
//p   packet
//receiver    receiver address
//src sender address
void receive_rreq(std::vector<uint8_t> packet , uint8_t source);

//Receive RREP.
//Parameters
//packet   RREP packet sent
//my  destination address
//src sender address
void receive_rrep(std::vector<uint8_t> packet, uint8_t my, uint8_t src);

//Receive RREP_ACK.
//Parameters
//neighbor    neighbor address
void receive_ack (uint8_t neigh_add);

//Receive RERR.
//
//Parameters
//p   packet
//src sender address Receive from node with address src
void receive_rrer(std::vector<uint8_t> p, uint8_t src);

//Set lifetime field in routing table entry to the maximum of existing lifetime and lt, if the entry exists.
//
//Parameters
//addr    - destination address
//lt  - proposed time for lifetime field in routing table entry for destination with address addr.
//Returns
//true if route to destination address addr exist
bool UpdateRouteLifeTime (uint8_t addr, clock_t lifetime);

//Returns true if can add more un dest
//dst destination
//seqNO destination sequence number to add
bool AddUnDestination (uint8_t dst, uint32_t seqNo );

//Delete pair (address + sequence number) from REER header, if the number of unreachable destinations > 0.
//
//Parameters
//un  unreachable pair (address + sequence number)
//Returns
//true on success
bool RemoveUnDestination (std::pair<uint8_t, uint32_t> & un );

//Process hello message.
//
//Parameters
//packet  RREP message header
void ProcessHello(std::vector<uint8_t> packet);

// Repeated attempts by a source node at route discovery for a single destination use the expanding ring search technique.

// Parameters
// dst	the destination IP address
void ScheduleRreqRetry(uint8_t dst);

///////////////////////////////////////////////////////////////////////////////
/////////////PACKET SENDING FUNCTIONS/////////////////////////////////////////
int send_rreq(uint8_t recipient_address, uint8_t sender_address ,uint8_t source_add, uint8_t destination_add, uint8_t hop_count, uint8_t rreq_id, uint8_t dest_seq_num, uint8_t origin_seq_num, uint8_t seq_valid, uint8_t g, uint8_t m_ttl, uint8_t r_ack);

int send_rrep(uint8_t recipient_add, uint8_t sender_address, uint8_t source_add, uint8_t destination_add, uint8_t prefix_size, uint8_t hop_count, uint8_t lifetime, uint8_t dest_seq_num, uint8_t m_ttl, uint8_t r_ack);

int send_rrer(uint8_t recipient_add, uint8_t sender_address, uint8_t N, uint8_t DestCount, uint8_t ttl, std::vector<uint8_t> u_dest, std::vector<uint8_t> u_dest_seq);

int send_hallo(uint8_t recipient_add, uint8_t sender_address, uint8_t source_add, uint8_t destination_add, uint8_t prefix_size, uint8_t hop_count, uint8_t lifetime, uint8_t dest_seq_num, uint8_t m_ttl, uint8_t r_ack);

int send_ack(uint8_t recipient_address, uint8_t sender_address, uint8_t ttl);

int send_message_data(uint8_t recipient_address, uint8_t sender_address, uint8_t origin, uint8_t dest, uint8_t ttl, std::vector<uint8_t> packet);

 ///////////////////////////////////////////////////////////////////////////
 //Functions For Serial Interface /////////////////////////////////////////
 

void Rx_interrupt();
void read_line();

// Circular buffers for serial TX and RX data - used by interrupt routines
const int buffer_size = 255;
// might need to increase buffer size for high baud rates
char tx_buffer[buffer_size];
uint8_t rx_buffer[buffer_size];
// Circular buffer pointers
// volatile makes read-modify-write atomic
volatile int tx_in=0;
volatile int tx_out=0;
volatile int rx_in=0;
volatile int rx_out=0;
// Line buffers for sprintf and sscanf
//char tx_line[80];
uint8_t rx_line[80];
//Flags for events????
uint8_t rx_bit = 0;

/////////////////////////
//TICKER FUNCTIONALITY

//Main routing queue request handler
Ticker routing_t;
//Main message queue request handler
Ticker message_t;
//Main Error Thread
Ticker rreq_t;

///Flags to keep track of errors
bool hallo_flag;
Ticker h_timer;
void Hallo_Timer_Expire();
void Queue_Hallo_Timer_Expire();
//Handles the time between hallos of neighbours to keep track of link breaks
std::map<uint8_t, clock_t> m_hallo_tracker;
//Tracks the amount of retries for the address
//KEY   VALUE
//dst   retries
std::map<uint8_t, uint8_t> m_hallo_retry;

bool rreq_rate_flag;
Ticker rreq_rate_timer;
//Reset RREQ count and schedule RREQ rate limit timer with delay 1 sec.
void RreqRateLimitTimerExpire();

bool rrer_rate_flag;
Ticker rrer_rate_timer;
//Reset RRER count and schedule RRER rate limit timer with delay 1 sec.
void RrerRateLimitTimerExpire();

//Helps manage the RREQ of different addresses
std::map<uint8_t, clock_t> m_addressReqTimer;
//Tracks the amount of retries for the RREQ
//KEY   VALUE
//dst   retries
std::map<uint8_t, uint8_t> m_rreq_retry;

//Repeatedly call this to check the rate of RREQ and to reschedule RREQ
void RouteRequestTimerExpire ();
//Queues the function into event so it exists the IRQ
void QueueRouteRequestTimerExpire();

void AckTimerExpire (uint8_t neighbor, clock_t blacklistTimeout);

//Keep track of the last bcast time.
clock_t m_lastBcastTime;  
/////////////////////////////////////////////////////////////
// * these options must match between the two devices in   //
//   order for communication to be successful
/////////////////////////////////////////////////////////////
static uint8_t network_address[] = { 0x01, 0x02, 0x03, 0x04 };
static uint8_t network_session_key[] = { 0x01, 0x02, 0x03, 0x04, 0x01, 0x02, 0x03, 0x04, 0x01, 0x02, 0x03, 0x04, 0x01, 0x02, 0x03, 0x04 };
static uint8_t data_session_key[] = { 0x01, 0x02, 0x03, 0x04, 0x01, 0x02, 0x03, 0x04, 0x01, 0x02, 0x03, 0x04, 0x01, 0x02, 0x03, 0x04 };

mDot* dot = NULL;
lora::ChannelPlan* plan = NULL;

//TX and RX handler
mbed::UnbufferedSerial pc(USBTX, USBRX);


/////////////////////////////////////////////////////////////
//// Functionality of the serial interface is here /////////


// Interupt Routine to read in data from serial port
void Rx_interrupt() {
// Loop just in case more than one character is in UART's receive FIFO buffer
// Stop if buffer full
    while ((pc.readable()) || (((rx_in + 1) % buffer_size) == rx_out)) {
        pc.read(&rx_buffer[rx_in], 1);
// Uncomment to Echo to USB serial to watch data flow
//        monitor_device.putc(rx_buffer[rx_in]);
        rx_in = (rx_in + 1) % buffer_size;
    }
    rx_bit = 1;
    return;
}
#endif






////////////////////////////////////////////////////////////////////////////////
/////////////ARCHIVE OF OLD CODE/////////////////////////////
//This is the main queue
//EventQueue request_event_queue;
////This is the error handler queue
//EventQueue error_event_queue;
////This will be an event type to handle the request queue
//Event<void(void)> request_queue(&request_event_queue, request_queue_handler);
////This will be an event type to handle the message queue
//Event<void(void)> message_queue(&request_event_queue, message_queue_handler);
////This will be activated as hallo packet is sent to neighbours to check if neighbours exist
//Event<void(void)> hallo_time_out(&error_event_queue, hallo_timeout);

//void send_rreq_handler(void)
//{
// send_rreq(device_ip_address,destination_ip_address,1,1,2,1);   
//    }
// 

//void post_queue_handlers(void)
//{
//    request_queue.post();
//    message_queue.post();
//}
//void cancel_request_queue(void)
//{
//    request_queue.cancel();
//}
//void cancel_message_queue(void)
//{
//    message_queue.cancel();
//}
//
//void post_error_handlers(void)
//{
//    hallo_time_out.post();
//    }
//    
//void cancel_hallo_time(void)
//{
//    hallo_time_out.cancel();
//    }