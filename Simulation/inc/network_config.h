#ifndef __NETWORK_CONFIG_H__
#define __NETWORK_CONFIG_H__
#include <algorithm> 

///////////////////////////////////////////////////////////////////////////////
////DEFINE THE TYPE OF USER THE DEVICE IS ////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////

#define DESTINATION_NODE 1
#define ROUTING_NODE 2
#define CLIENT_NODE 3

//Select the active user
#if !defined(ACTIVE_USER)
#define ACTIVE_USER  ROUTING_NODE
#endif

//////////////////////////////////////////////////////////////////////////////
////// ADDING VERSION CONTROL FOR DEMO PURPOSES /////////////////////////////
////////////////////////////////////////////////////////////////////////////

#define AODV 1
#define AOMDV 2
#define AOMDV_LD_LR 3
#define LR_EE_AOMDV_LD_LR 4

//Select the current protocol version
#if !defined(ACTIVE_VERSION)
#define ACTIVE_VERSION  AODV
#endif

//NOTE ALL TIMING IS DONE IN MS
//TO USE WITH QUEUE TIMING CONVERT TO TIME IN TERMS OF CPU TICKS

#define ACTIVE_ROUTE_TIMEOUT              30000  // Used during upper bound delete calculations
#define ALLOWED_HELLO_LOSS                2  // Number of hallo packet drops allowed
#define ALLOWED_R_ACK_LOSS          2 //Number of times sending retrying to receive an r_ack
#define HELLO_INTERVAL           20000  // If defined for node, this indicates how often hallo packets are sent to check links
#define TTL_START     1  // 
#define TTL_THRESHOLD          2  //
#define TTL_INCREMENT   1
#define RREQ_RETRIES             5  // 
#define NET_DIAMETER    35
#define NODE_TRAVERSAL_TIME 4000
#define NET_TRAVERSAL_TIME  2 * NODE_TRAVERSAL_TIME * NET_DIAMETER
#define BLACKLIST_TIMEOUT   RREQ_RETRIES * NET_TRAVERSAL_TIME
#define LOCAL_ADD_TTL   2
#define MAX_REPAIR_TTL  0.3 * NET_DIAMETER
#define MY_ROUTE_TIMEOUT    2 * ACTIVE_ROUTE_TIMEOUT
#define PATH_DISCOVERY_TIME 2 * NET_TRAVERSAL_TIME
#define RERR_RATELIMIT  10
#define RING_TRAVERSAL_TIME 2 * NODE_TRAVERSAL_TIME *(TTL_VALUE + TIMEOUT_BUFFER)
#define RREQ_RATELIMIT  10
#define TIMEOUT_BUFFER  2 
#define QUEUE_BUFFER_TIME 2000 //The maximum period of time that a routing protocol is allowed to buffer a packet for, milli-seconds
#define QUEUE_SIZE 10 //Defines the max amount to go to queue
#define QUEUE_TIMEOUT 20000 //Expire time for queue entry
#define K_VALUE 5
#define DELETE_PERIOD K_VALUE * max (ACTIVE_ROUTE_TIMEOUT, HELLO_INTERVAL)
#define HELLO_TIME_OUT 60000
#define NEIGHBOUR_TIMEOUT 30000
//DEFINING THE EVENT FREQUENCIES IN MS
#define REQUEST_QUEUE_PERIOD 10000
#define MESSAGE_QUEUE_PERIOD 15000
#define M_BROADCAST_ID 40 //This is my broadcast ID for now
#define DUBLICATE_CACHE_TIMEOUT  10000
#define RREP_TIMEOUT 5000
#define RRER_DEST_LIMIT 6 //limits the max size of destnumber in rrer packet
#define ENABLE_HALLO 1 //enables hallo packets
#define TX_NEXT_WAIT 20ms
// #define EVENTS_EVENT_SIZE 10
// DEFINING THE INDEX OF PARTS OF PACKETS
//TEMPLATE BEING USED /////
// FORMAT OF RREQ MORE INFO AT https://datatracker.ietf.org/doc/html/rfc3561#section-5.1
//      0                   1                   2                   3
//    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |     Type      |J|R|G|D|U|   Reserved          |   Hop Count   |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                            RREQ ID                            |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                    Destination IP Address                     |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                  Destination Sequence Number                  |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                    Originator IP Address                      |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                  Originator Sequence Number                   |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

#define RREQ_PACKET_TYPE 0
#define RREQ_RECIPIENT 1
#define RREQ_SENDER 2
#define RREQ_PACKET_HOP_COUNT 3
#define RREQ_PACKET_RREQ_ID 4
#define RREQ_PACKET_DESTINATION_IP 5
#define RREQ_PACKET_DESTINATION_SEQ 6
#define RREQ_PACKET_ORIGIN_IP 7
#define RREQ_PACKET_ORIGIN_SEQ 8
#define RREQ_PACKET_UNKOWN_SEQ 9
#define RREQ_PACKET_G 10
#define RREQ_PACKET_TTL 11
#define RREQ_PACKET_ACK 12

// FORMAT OF RREP MORE INFO AT https://datatracker.ietf.org/doc/html/rfc3561#section-5.1
//      0                   1                   2                   3
//    0                   1                   2                   3
//    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |     Type      |R|A|    Reserved     |Prefix Sz|   Hop Count   |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                           Lifetime                            |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                     Destination IP address                    |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                  Destination Sequence Number                  |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                    Originator IP address                      |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#define RREP_PACKET_TYPE 0
#define RREP_PACKET_RECIPIENT 1
#define RREP_PACKET_SENDER 2
#define RREP_PACKET_PREFIX 3
#define RREP_PACKET_HOP_COUNT 4
#define RREP_PACKET_LIFETIME 5
#define RREP_PACKET_DESTINATION_IP 6
#define RREP_PACKET_DESTINATION_SEQ 7
#define RREP_PACKET_ORIGIN_IP 8
#define RREP_PACKET_TTL 9
#define RREP_PACKET_ACK 10

//Route Error (RERR) Message Format https://datatracker.ietf.org/doc/html/rfc3561#section-5.1
//
//    0                   1                   2                   3
//    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |     Type      |N|          Reserved           |   DestCount   |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |            Unreachable Destination IP Address (1)             |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |         Unreachable Destination Sequence Number (1)           |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-|
//   |  Additional Unreachable Destination IP Addresses (if needed)  |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |Additional Unreachable Destination Sequence Numbers (if needed)|
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

#define RERR_PACKET_TYPE 0
#define RRER_PACKET_RECIPIENT 1
#define RRER_PACKET_SENDER 2
#define RRER_PACKET_N 3
#define RRER_PACKET_DESTCOUNT 4
#define RRER_PACKET_TTL 5
#define RRER_PACKET_DEST_DELETE 6
#define RRER_PACKET_DEST_SSEQ 7


////////////////////////
//Defining indexes for the message packet
//int send_message_data(uint8_t recipient_address, uint8_t sender_address,uint8_t origin, uint8_t dest,uint8_t ttl, std::vector<uint8_t> packet)
#define MESSAGE_PACKET_TYPE 0
#define MESSAGE_PACKET_RECIPIENT 1
#define MESSAGE_PACKET_SENDER 2
#define MESSAGE_PACKET_ORIGIN 3
#define MESSAGE_PACKET_DESTINATION 4
#define MESSAGE_PACKET_TTL 5



//      Route Request (RREQ)            1
//      Route Reply (RREP)              2
//      Route Error (RERR)              3
//      Route-Reply Ack (RREP-ACK)      4
//      My Hallo Message Extention      5
//      Data packets                    6
//Enumerations for network definitions
typedef enum {
    ROUTE_REQUEST = 1,
    ROUTE_REPLY = 2,
    ROUTE_ERROR = 3,
    ROUTE_REPLY_ACK = 4,
    HALLO_MESSAGE = 5,
    DATA_MESSAGE = 6,
} MessageTypes;

////////////////////////////////////////////////
/////ADDITIONAL AOMDV CONFIGURATIONS////////////
////////////////////////////////////////////////
#if ACTIVE_VERSION==AOMDV || ACTIVE_VERSION==AOMDV_LD_LR || ACTIVE_VERSION == LR_EE_AOMDV_LD_LR
#define RREQ_PACKET_ORIGIN_NEIGH 13
#define RREQ_PACKET_RRER_RREQ 14
#define RREP_PACKET_ORIGIN_NEIGH 11
#define RREP_PACKET_RRER_RREQ 12
#define K_REPEATS 3
#endif

//////////////////////////////////////////////////
/////ADDITIONAL LREEAOMDVLDLR CONFIGURATIONS ////
////////////////////////////////////////////////

#if ACTIVE_VERSION == LR_EE_AOMDV_LD_LR

#define RREQ_PACKET_CETX_ONE 15
#define RREQ_PACKET_CETX_TWO 16
#define RREQ_PACKET_CETX_THREE 17
#define RREQ_PACKET_CETX_FOUR 18

#define RREQ_PACKET_CETE_ONE 19
#define RREQ_PACKET_CETE_TWO 20
#define RREQ_PACKET_CETE_THREE 21
#define RREQ_PACKET_CETE_FOUR 22

#define RREQ_PACKET_RE_ENERGY_ONE 23
#define RREQ_PACKET_RE_ENERGY_TWO 24
#define RREQ_PACKET_RE_ENERGY_THREE 25
#define RREQ_PACKET_RE_ENERGY_FOUR 26

#define RREQ_LENGTH 27

#define RREP_PACKET_CETX_ONE 13
#define RREP_PACKET_CETX_TWO 14
#define RREP_PACKET_CETX_THREE 15
#define RREP_PACKET_CETX_FOUR 16

#define RREP_PACKET_CETE_ONE 17
#define RREP_PACKET_CETE_TWO 18
#define RREP_PACKET_CETE_THREE 19
#define RREP_PACKET_CETE_FOUR 20

#define RREP_PACKET_RE_ENERGY_ONE 21
#define RREP_PACKET_RE_ENERGY_TWO 22
#define RREP_PACKET_RE_ENERGY_THREE 23
#define RREP_PACKET_RE_ENERGY_FOUR 24

#define RREP_LENGTH 25

#define R_ACK_PACKET_TYPE 0
#define R_ACK_PACKET_RECIPIENT 1
#define R_ACK_PACKET_SENDER 2
#define R_ACK_PACKET_TTL 3
#define R_ACK_PACKET_LINK_ONE 4
#define R_ACK_PACKET_LINK_TWO 5
#define R_ACK_PACKET_LINK_THREE 6
#define R_ACK_PACKET_LINK_FOUR 7
#define R_ACK_PACKET_LOAD_ONE 8
#define R_ACK_PACKET_LOAD_TWO 9
#define R_ACK_PACKET_LOAD_THREE 10
#define R_ACK_PACKET_LOAD_FOUR 11

#define EPOCH_CHRONO 10s //chrono time of epoch
#define EPOCH 10//time in seconds for calculations

//Phyical parameters
#define CURRENT 30 //mA
#define VOLTAGE 3.3 //V
#define PRECISION 1000 //defines precision in doubles when sent over channel
#define FULL_BATTERY 650 //mAh
#endif

#endif


//   MIN_REPAIR_TTL           should be the last known hop count to the destination. Define in main more likely 
//   TTL_VALUE                This is needed but follow rules at https://datatracker.ietf.org/doc/html/rfc3561#section-6.4