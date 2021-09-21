///////////////////////////////////////////////////////////////////////////////
/// SUMMARY OF INNER WORKINGS OF THE PROGRAM SPECIFICS WILL FOLLOW AT FILES ///
///////////////////////////////////////////////////////////////////////////////
///// ROUTE DETECTION ////////////////////////////////////////////////////////
//TODO FIX NEXTHOP AOVDM
//TODO FIX SEQUENCE NUMBER UPDATE AOVDM
//TODO CHECK RRER FOR AOVDM
//NB GetHop is the same as get advertised hop
//NB SetHop is the same as set advertised hop
//NB To Look For AOMDV specific things simply CTRL+F and search ACTIVE_VERSION
//TODO check if my neighbour table works with my hallo timer properly
//NB Routes to Destination is marked with source from where the RREP came from
//NB Routes to Origin is marked by Origin Neighbour tag

#include "aomdv_main.h"

#if ACTIVE_VERSION == AOMDV

#include <algorithm>
#include <cstdint>
#include <ctime>
#include <iostream>
#include <string>
#include <vector>

//KEY               VALUE
//Neighbour ID     list of sources that RREP came from
std::map<uint8_t, std::vector<uint8_t>> rrep_firsthop_list;

int main() {
    // Custom event handler for automatically displaying RX data
    RadioEvent events;
    
    uint32_t tx_frequency;
    uint8_t tx_datarate;
    uint8_t tx_power;
    uint8_t frequency_band;

    pc.baud(115200);
    
    // Setup a serial interrupt function to receive data
    pc.attach(&Rx_interrupt, UnbufferedSerial::RxIrq);
    
    mts::MTSLog::setLogLevel(mts::MTSLog::TRACE_LEVEL);

    // Create channel plan
    plan = create_channel_plan();
    assert(plan);

    dot = mDot::getInstance(plan);
    assert(dot);

    logInfo("mbed-os library version: %d.%d.%d", MBED_MAJOR_VERSION, MBED_MINOR_VERSION, MBED_PATCH_VERSION);

    // start from a well-known state
    logInfo("defaulting Dot configuration");
    dot->resetConfig();

    // make sure library logging is turned on
    dot->setLogLevel(mts::MTSLog::INFO_LEVEL);

    // attach the custom events handler
    dot->setEvents(&events);

    // update configuration if necessary
    if (dot->getJoinMode() != mDot::PEER_TO_PEER) {
        logInfo("changing network join mode to PEER_TO_PEER");
        if (dot->setJoinMode(mDot::PEER_TO_PEER) != mDot::MDOT_OK) {
            logError("failed to set network join mode to PEER_TO_PEER");
        }
    }
    frequency_band = dot->getFrequencyBand();
    switch (frequency_band) {
        case lora::ChannelPlan::EU868:
            // 250kHz channels achieve higher throughput
            // DR_6 : SF7 @ 250kHz
            // DR_0 - DR_5 (125kHz channels) available but much slower
            tx_frequency = 869850000;
            tx_datarate = lora::DR_6;
            // the 869850000 frequency is 100% duty cycle if the total power is under 7 dBm - tx power 0 + antenna gain 3 = 3
            tx_power = 0;
            break;

        default:
            while (true) {
                logFatal("no known channel plan in use - extra configuration is needed!");
                ThisThread::sleep_for(5s);
            }
            break;
    }
    // in PEER_TO_PEER mode there is no join request/response transaction
    // as long as both Dots are configured correctly, they should be able to communicate
    update_peer_to_peer_config(network_address, network_session_key, data_session_key, tx_frequency, tx_datarate, tx_power);

    // save changes to configuration
    logInfo("saving configuration");
    if (!dot->saveConfig()) {
        logError("failed to save configuration");
    }

    // display configuration
    display_config();
    //This is where the initial configurations are made
    start();
//Function that broadcasts hallo message in order to obtain all neighbours
    obtain_neighbours();
        
    while (true) {
        std::vector<uint8_t> tx_data;

        // join network if not joined
        if (!dot->getNetworkJoinStatus()) {
            join_network();
        }
        
        
        #if ACTIVE_USER == CLIENT_NODE
            //Client thus it will take things from serial input and forward it to the needed route if it exhists
                   if (rx_bit){
           logInfo("waiting for 200ms so rx buffer is empty");
           ThisThread::sleep_for(200ms);
           
           // get some dummy data and send it to the gateway
           for (int i =0; i<rx_in ; i= i+1) {
               tx_data.push_back(rx_buffer[i]);
               } 
            uint8_t type = 6;

            tx_data.insert(tx_data.begin(),0);
            tx_data.insert(tx_data.begin(),destination_ip_address);
            tx_data.insert(tx_data.begin(),device_ip_address);
            tx_data.insert(tx_data.begin(),device_ip_address);
            tx_data.insert(tx_data.begin(),0);
            tx_data.insert(tx_data.begin(),type);

            QueueEntry newEntry (tx_data,QUEUE_TIMEOUT*CLOCKS_PER_SEC/1000);
            std::cout<<"Enqeued entry with dead time "<<std::to_string(newEntry.GetExpireTime())<<" Current time is "<<std::to_string(clock())<<endl;
            std::cout<<"Total clock cycles that it will survive "<<std::to_string(QUEUE_TIMEOUT*CLOCKS_PER_SEC/1000)<<" now it is "<<std::to_string(newEntry.GetTimeTillExpire())<<endl;
           if(!message_request_queue.Enqueue(newEntry))
           {
               std::cout<<"Error enqeueing in line 112"<<endl;
           }
           rx_bit = 0;
           rx_in = 0;
       }
        #endif

    }
 
    return 0;
}






void start()
{
        //Setting all default values
        m_sequence = 0;
        m_requestId = M_BROADCAST_ID;
        m_rreqCount = 0;
        m_rerrCount = 0;
        m_neighbourCount = 0;
        //////////////////////////////////////
    ///Here is the main event specifiers//
    //////////////////////////////////////
    //HERE WE SEE WHO IS WHAT AND INITIALIZE THE TIMERS BASED ON THAT
    #if ACTIVE_USER == DESTINATION_NODE
        //Destination has no need of RREQ
        h_timer.attach(&Queue_Hallo_Timer_Expire, 10s);
        routing_t.attach(&queue_request_queue_handler,1s);
        message_t.attach(&queue_message_handler,1s);
        rreq_rate_timer.attach(&RreqRateLimitTimerExpire,1s);
        rrer_rate_timer.attach(&RrerRateLimitTimerExpire,1s);
        //        //Start the queue threads
        main_thread.start(callback(&main_queue, &EventQueue::dispatch_forever));
        main_queue.event(Hallo_Timer_Expire);
        main_queue.event(request_queue_handler);
        main_queue.event(message_queue_handler);
    #elif ACTIVE_USER == ROUTING_NODE
        rreq_t.attach(&QueueRouteRequestTimerExpire,4s);
        h_timer.attach(&Queue_Hallo_Timer_Expire, 10s);
        routing_t.attach(&queue_request_queue_handler,1s);
        message_t.attach(&queue_message_handler,1s);
        rreq_rate_timer.attach(&RreqRateLimitTimerExpire,1s);
        rrer_rate_timer.attach(&RrerRateLimitTimerExpire,1s);
        //        //Start the queue threads
        main_thread.start(callback(&main_queue, &EventQueue::dispatch_forever));
        main_queue.event(Hallo_Timer_Expire);
        main_queue.event(request_queue_handler);
        main_queue.event(RouteRequestTimerExpire);
        main_queue.event(message_queue_handler);
    #elif ACTIVE_USER == CLIENT_NODE
        rreq_t.attach(&QueueRouteRequestTimerExpire,4s);
        h_timer.attach(&Queue_Hallo_Timer_Expire, 10s);
        routing_t.attach(&queue_request_queue_handler,1s);
        message_t.attach(&queue_message_handler,1s);
        rreq_rate_timer.attach(&RreqRateLimitTimerExpire,1s);
        rrer_rate_timer.attach(&RrerRateLimitTimerExpire,1s);
        //        //Start the queue threads
        main_thread.start(callback(&main_queue, &EventQueue::dispatch_forever));
        main_queue.event(Hallo_Timer_Expire);
        main_queue.event(request_queue_handler);
        main_queue.event(RouteRequestTimerExpire);
        main_queue.event(message_queue_handler);
        //FOR NOW SINCE TESTING SEND A RREQ STRAIGHT
        // send_rreq(destination_ip_address); 
    #endif  
    
    }
    
 void obtain_neighbours()
 {
     logInfo("Initial HALLO message is being schedule to be sent");
    SendHallo(); 
     }    

void wait_on_radio()
{
    }

bool UpdateRouteLifeTime (uint8_t addr, clock_t lifetime)
{
   logInfo("Checking If Route Exists For UpdateRouteLifeTime");
       //create an initial dummy
    std::vector<RouteEntity> route_list;
   RoutingTableEntry rt = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   
   if (m_routing_table.LookupRoute (addr, rt))
     {
       if (rt.GetFlag () == VALID)
         {
           logInfo ("Updating VALID route");
           rt.SetRreqCnt (0);
           if (lifetime>=rt.GetLifeTime ()-clock())
           {
            rt.SetLifeTime (lifetime);
               }
            else
            {
               rt.SetLifeTime (rt.GetLifeTime ()-clock()); 
                }
           m_routing_table.Update (rt);
           return true;
         }
     }
   return false;
    }

 bool AddUnDestination (uint8_t dst, uint32_t seqNo )
 {
   if (m_unreachableDstSeqNo.find (dst) != m_unreachableDstSeqNo.end ())
     {
       return true;
     }
  
    if ((uint8_t)m_unreachableDstSeqNo.size ()> RRER_DEST_LIMIT)//can't support more than RRER_DEST_LIMIT destinations in single RERR
    {
        return false;
        }
   m_unreachableDstSeqNo.insert (std::make_pair (dst, seqNo));
   return true;
 }
 
bool RemoveUnDestination (std::pair<uint8_t, uint32_t> & un )
 {
   if (m_unreachableDstSeqNo.empty ())
     {
       return false;
     }
   std::map<uint8_t, uint32_t>::iterator i = m_unreachableDstSeqNo.begin ();
   un = *i;
   m_unreachableDstSeqNo.erase (i);
   return true;
 } 
 
void send_reply_ack(uint8_t neighbor_add)
{
       logInfo ("Sending reply ack to ");
   send_ack(neighbor_add, device_ip_address, 1);
    }
    
void SendReply(std::vector<uint8_t> packet , RoutingTableEntry & toOrigin, uint8_t neighbour_source)
{
    //This stays the same for AOMDV
       logInfo ("Sending a reply back from destination");
   /*
    * Destination node MUST increment its own sequence number by one if the sequence number in the RREQ packet is equal to that
    * incremented value. Otherwise, the destination does not change its sequence number before generating the  RREP message.
    */
   if (!(packet.at(RREQ_PACKET_UNKOWN_SEQ)==1) && (packet.at(RREQ_PACKET_DESTINATION_SEQ) == m_sequence + 1))
     {
       m_sequence++;
     }  
    //If a request is sent update the advertised hop count
    toOrigin.update_advertise_hop();                                
    uint8_t ttl =toOrigin.GetHop ();
    //Sends the RREP now
    //send_rrep( toOrigin.GetDestination (), packet.at(RREQ_PACKET_DESTINATION_IP), 0, 0, RREP_TIMEOUT*CLOCKS_PER_SEC/1000, m_sequence, ttl);
    wait_on_radio();
    //TODO fix uint8_t conversionerror
    //Changed so it sends to every neighbour 
    //Put in small delay
    std::vector<uint8_t> hop_list = toOrigin.GetNextHop(packet.at(RREQ_PACKET_ORIGIN_NEIGH)); 
    for (int i = 0;i<hop_list.size();i++)
    {
        send_rrep(hop_list.at(i),device_ip_address,toOrigin.GetDestination (), packet.at(RREQ_PACKET_DESTINATION_IP), 0, 0, RREP_TIMEOUT*CLOCKS_PER_SEC/1000, m_sequence, ttl,0,neighbour_source); 
        ThisThread::sleep_for(100ms); //Small gap in sending receiving
        //TODO find out if fine
        //TODO find out if precursor needed
    }
     }
    
//FOr AOMDV I need to know neighbour of RREQ when sending intermediate reply
void SendReplyByIntermediateNode (RoutingTableEntry & toDst, RoutingTableEntry & toOrigin, bool gratRep, uint8_t neighbour_source, uint8_t src)
{
       logInfo ("Sending Reply By Intermediate Node");
       //Generate the RREP message parameters
    uint8_t prefix_m = 0;
    uint8_t hops_m = toDst.GetHop ();
    uint8_t dest_m = toDst.GetDestination ();
    uint8_t dest_seq_m =  toDst.GetSeqNo ();
    uint8_t source_m = toOrigin.GetDestination ();
    uint8_t lifetime_m = toDst.GetLifeTime ()-clock();
    uint8_t r_ack_m = 0;
    uint8_t ttl_m = toOrigin.GetHop ();
    //Dummy route list to feed in roujte enrty route
    std::vector<RouteEntity> route_list;
   /* If the node we received a RREQ for is a neighbor we are
    * probably facing a unidirectional link... Better request a RREP-ack
    */
    std::vector<uint8_t> hop_list_origin = toOrigin.GetNextHop(neighbour_source); 
    std::vector<uint8_t> hop_list_Dst = toDst.GetNextHop(src); 
    std::vector<RouteEntity> entity_list_origin = toOrigin.get_entity_with_neigh_source(neighbour_source);
    std::vector<RouteEntity> entity_list_dst = toDst.get_entity_with_neigh_source(src);
   if (hops_m == 1)
     {
    //    r_ack_m = 1;
    //    RoutingTableEntry toNextHop = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
    //    m_routing_table.LookupRoute (toOrigin.GetNextHop (0), toNextHop);
       //TODO set a RREP_ACK wait timer
     }
    for (int i = 0;i<entity_list_origin.size();i++)
    {
        for(int j = 0;j<hop_list_Dst.size();j++)
        {
            //adding precursor to every new entry from source
            entity_list_origin.at(i).InsertPrecursor(hop_list_Dst.at(j));
        }
    }
    for (int i = 0;i<entity_list_dst.size();i++)
    {
        for(int j = 0;j<hop_list_origin.size();j++)
        {
            //adding precursor to every new entry from source
            entity_list_dst.at(i).InsertPrecursor(hop_list_origin.at(j));
        }
    }
   m_routing_table.Update (toDst);
   m_routing_table.Update (toOrigin);
   #if ACTIVE_VERSION == AOMDV
   //Everytime a request is sent update advertised hop count
   toDst.update_advertise_hop();
   toOrigin.update_advertise_hop();
   #endif

    for(int j = 0;j<hop_list_origin.size();j++)
        {
   //sending rrep towards origin route entry next hop
    send_rrep(hop_list_origin.at(j), device_ip_address, source_m,dest_m,prefix_m,hops_m,lifetime_m,dest_seq_m,ttl_m,r_ack_m,neighbour_source);
    ThisThread::sleep_for(100ms); //Small gap in sending receiving
        }
  
   // Generating gratuitous RREPs
   if (gratRep)
     {
            uint8_t prefix_g = 0;
    uint8_t hops_g = toOrigin.GetHop ();
    uint8_t dest_g =  toOrigin.GetDestination ();
    uint8_t dest_seq_g =  toOrigin.GetSeqNo ();
    uint8_t source_g = toDst.GetDestination ();
    uint8_t lifetime_g = toOrigin.GetLifeTime () - clock();
    uint8_t r_ack_g = 0;
    uint8_t ttl_g = toDst.GetHop ();
       logInfo ("Send gratuitous RREP ");
           for(int j = 0;j<hop_list_Dst.size();j++)
        {
   //sending rrep towards origin route entry next hop
    send_rrep(hop_list_Dst.at(j), device_ip_address, source_g,dest_g,prefix_g,hops_g,lifetime_g,dest_seq_g,ttl_g,r_ack_g,neighbour_source);
    ThisThread::sleep_for(100ms); //Small gap in sending receiving
        }
     }
    }      

void send_rreq(uint8_t dest)//Only client really calls this
{
    //create an initial dummy
    std::vector<RouteEntity> route_list;
    RoutingTableEntry rt = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
    uint8_t ttl = TTL_START;
    uint8_t reply_seq_origin = 0;
    uint8_t reply_seq_dest = 0;
    uint8_t sseq_known_reply = 0;
    uint8_t gratious_reply = 0;
    //Does ring calculations
    if (m_routing_table.LookupRoute (dest, rt))
     {
       if (rt.GetFlag () != IN_SEARCH)
         {
           ttl = std::min<uint16_t> (rt.GetHop () + TTL_INCREMENT, NET_DIAMETER);
         }
       else
         {
           ttl = rt.GetHop () + TTL_INCREMENT;
           if (ttl > TTL_THRESHOLD)
             {
               ttl = NET_DIAMETER;
             }
         }
       if (ttl == NET_DIAMETER)
         {
           rt.IncrementRreqCnt ();
         }
       if (rt.GetValidSeqNo ())
         {
           reply_seq_dest = rt.GetSeqNo ();
         }
       else
         {
           sseq_known_reply = 1;
         }
       rt.SetHop (ttl);
       rt.SetFlag (IN_SEARCH);
       rt.SetLifeTime (NET_TRAVERSAL_TIME);
       m_routing_table.Update (rt);
        //Whenever node i sends request update advertised hop to d
        rt.update_advertise_hop();
     }
   else
     {
       sseq_known_reply = 1;
       //For AOMDV MAKE INITIAL HOP BE NET_DIAMETER
        RoutingTableEntry newEntry = RoutingTableEntry(destination_ip_address,m_sequence,NET_DIAMETER,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
       // Check if TtlStart == NetDiameter
       if (ttl == NET_DIAMETER)
         {
           newEntry.IncrementRreqCnt ();
         }
       newEntry.SetFlag (IN_SEARCH);
       m_routing_table.AddRoute (newEntry,0);
        //Whenever node i sends request update advertised hop to d
        newEntry.update_advertise_hop();
     }
     
   update_node_seq(1,1);
   reply_seq_origin = m_sequence;
   m_requestId++;
   //Schedule a wait thing to wait to RREQ again depedning on repeats.
   ScheduleRreqRetry (dest);
   //Sending the RREQ now then
   //I do want to send a Gratuitous RREP
   //Sending RREQ to every known neighbour
    std::vector<Neighbors::Neighbor> current_neighbours = myNeighbour.getListNeighbours();
    for (int i = 0;i<current_neighbours.size();i++)
    {
        logInfo ("Sending RREQ");
        send_rreq(current_neighbours.at(i).m_neighborAddress, device_ip_address, device_ip_address, destination_ip_address,0, m_requestId, reply_seq_dest, reply_seq_origin, sseq_known_reply ,1,ttl,0,current_neighbours.at(i).m_neighborAddress);//I know first neighbours from origin so format packet according
       }
    } 
 
void SendRerrWhenNoRouteToForward(uint8_t dst, uint8_t dstSeqNo, uint8_t origin)
{
       logInfo ("Sending RerrWhenNoRouteToForward");
       std::vector<RouteEntity> route_list;
   // A node SHOULD NOT originate more than RERR_RATELIMIT RERR messages per second.
   if (m_rerrCount == RERR_RATELIMIT)
     {
       // Just make sure that the RerrRateLimit timer is running and will expire
       // discard the packet and return
       logInfo("RRER rate limit has been reached");
       return;
     }
    std::vector<uint8_t> m_dest; 
    std::vector<uint8_t> m_dest_seq;
    m_dest.push_back(dst);
    m_dest_seq.push_back(dstSeqNo);
   RoutingTableEntry toOrigin = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   uint8_t ttl_m = 1;
   if (m_routing_table.LookupValidRoute (origin, toOrigin))
     {
       logDebug ("Unicast RERR to the source of the data transmission No delete flag??");
       //send_rrer(uint8_t recipient_add, uint8_t sender_address, uint8_t N, uint8_t DestCount, uint8_t ttl std::vector<uint8_t> u_dest, std::vector<uint8_t> u_dest_seq)
       //socket->SendTo (packet, 0, InetSocketAddress (toOrigin.GetNextHop (), AODV_PORT));
       //Since no route to destination tell every node back to origin that this node is bad
       std::vector<uint8_t> list_warning = toOrigin.GetEveryHop();
       for (std::vector<uint8_t>::iterator i = list_warning.begin (); i!= list_warning.end ();i++ )
       {
           send_rrer(*i, device_ip_address, 0, 1, ttl_m, m_dest, m_dest_seq);
           //Wait between no to overload
           ThisThread::sleep_for(200ms);
       }
     }
   else
     {
         //Broadcast to every neighbour
             std::vector<Neighbors::Neighbor> current_neighbours = myNeighbour.getListNeighbours();
             for (int i = 0;i<current_neighbours.size();i++)
                {
                 send_rrer(current_neighbours.at(i).m_neighborAddress, device_ip_address, 0, 1, ttl_m, m_dest, m_dest_seq);
                }
     }
    } 

void SendRerrWhenBreaksLinkToNextHop(uint8_t nextHop)
{
    std::cout<<"Processing RRER since link to "<<nextHop<<" broke.";
    //i) Find routes that use this address in any entity
    //ii) Remove the entity from route list
    //iii) update LoRaRoute
    //iV) If no valid route exhists for some destination due to node unreachable then merely invalidate the route
    //We only need to do this since it is trusted that every node will manage their respective links. Proper rediscovery only needs to be done once a node as no route 
    //to destination

    std::vector<RouteEntity> route_list;
//     std::vector<uint8_t> precursors;
    std::map<uint8_t, uint32_t> unreachable;
    std::map<uint8_t, uint32_t> destination_devices;
     m_routing_table.GetListOfDestinationWithNextHopAOMDV(nextHop, destination_devices); //gets destination address with this hop
    for (std::map<uint8_t, uint32_t>::const_iterator i =destination_devices.begin (); i != destination_devices.end (); ++i) //step through entries
        {
            RoutingTableEntry toDst = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address); //modify table entries routes
            if (m_routing_table.LookupRoute (i->first, toDst))
            {
                RouteEntity remover = RouteEntity(nextHop,0,0);
                if(toDst.removeSpecificEntity(remover))
                {
                    //was removed
                    if (toDst.isRouteListEmpty())
                    {
                        //Nothing left so push back list of unreachable
                        unreachable.insert (std::make_pair (i->first, i->second));
                    }
                }
            }
        }
    RoutingTableEntry toNeigh = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address); //modify table entries routes
    if (m_routing_table.LookupRoute (nextHop, toNeigh))  
    {
        unreachable.insert (std::make_pair (nextHop, toNeigh.GetSeqNo ()));
    }      
       for (std::map<uint8_t, uint32_t>::const_iterator i = unreachable.begin (); i
        != unreachable.end (); )
     {
       AddUnDestination (i->first, i->second);
     }
    m_routing_table.InvalidateRoutesWithDst (unreachable);
//    //Deleting neighbours as well
    myNeighbour.RemoveNeighbour(nextHop);
    }
  
void SendRerrMessage(std::vector<uint8_t> packet, std::vector< uint8_t > precursors)
{
      std::vector<RouteEntity> route_list;
      logInfo ("Forwarding RRER Message");
   if (precursors.empty ())
     {
       logInfo ("No precursors so needn't worry");
       return;
     }
   // A node SHOULD NOT originate more than RERR_RATELIMIT RERR messages per second.
   if (m_rerrCount == RERR_RATELIMIT)
     {
       // Just make sure that the RerrRateLimit timer is running and will expire
       // discard the packet and return
       logInfo("RRER rate limit has been reached");
       return;
     }
     
   // If there is only one precursor, RERR SHOULD be unicast toward that precursor
   if (precursors.size () == 1)
     {
       RoutingTableEntry toPrecursor = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
       if (m_routing_table.LookupValidRoute (precursors.front (), toPrecursor))
         {
           logInfo ("one precursor => unicast RERR to: TODO morew info make clear");
           packet.at(RRER_PACKET_RECIPIENT) = precursors.front ();
           packet.at(RRER_PACKET_SENDER) = device_ip_address;
           m_rerrCount++;
           wait_on_radio();
           send_data(packet);
         }
       return;
     }
  
   //  Should only transmit RERR on those interfaces which have precursor nodes for the broken route
   std::vector<uint8_t> addresses_send_rrer ;
   RoutingTableEntry toPrecursor = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   for (std::vector<uint8_t>::const_iterator i = precursors.begin (); i != precursors.end (); ++i)
     {
       if (m_routing_table.LookupValidRoute (*i, toPrecursor))
         {
             std::vector<uint8_t> precursor_hop_list = toPrecursor.GetEveryHop();
             for (int j = 0;j<precursor_hop_list.size();j++)
             {
                addresses_send_rrer.push_back (precursor_hop_list.at(j)); //adds next hop to get to precursor as rrer+
             }
         }
     }
  
   for (std::vector<uint8_t>::const_iterator i = addresses_send_rrer.begin (); i != addresses_send_rrer.end (); ++i)
     {
        packet.at(RRER_PACKET_RECIPIENT) = *i;
        packet.at(RRER_PACKET_SENDER) = device_ip_address;
        m_rerrCount++;
        logInfo("Preparing to send RRER to: TODO add address detail");
        wait_on_radio();
        send_data(packet);
     } 
    }  
    
bool forward_message(std::vector<uint8_t> p, uint8_t dst, uint8_t origin)
{
    logInfo("Trying to forward message through a route");
   m_routing_table.Purge ();
       //create an initial dummy
    std::vector<RouteEntity> route_list;
   RoutingTableEntry toDst = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   if (m_routing_table.LookupRoute (dst, toDst))
     {
       if (toDst.GetFlag () == VALID)
         {
             toDst.update_LoRa_path(); //Update so chooses best next hop
           LoRaRoute route = toDst.GetRoute ();
            std::cout<<"Received message ";
           for (std::vector<uint8_t>::const_iterator i = p.begin (); i != p.end (); ++i)
           {
               std::cout<<*i;
           }
            std::cout<<" from "<<origin<<" forwarding it to "<<route.GetNextHop ()<<" destination is "<<dst<<endl;
  
           /*
            *  Each time a route is used to forward a data packet, its Active Route
            *  Lifetime field of the source, destination and the next hop on the
            *  path to the destination is updated to be no less than the current
            *  time plus ActiveRouteTimeout.
            */
           UpdateRouteLifeTime (origin, ACTIVE_ROUTE_TIMEOUT);
           UpdateRouteLifeTime (dst, ACTIVE_ROUTE_TIMEOUT);
           UpdateRouteLifeTime (route.GetNextHop (), ACTIVE_ROUTE_TIMEOUT);
           /*
            *  Since the route between each originator and destination pair is expected to be symmetric, the
            *  Active Route Lifetime for the previous hop, along the reverse path back to the IP source, is also updated
            *  to be no less than the current time plus ActiveRouteTimeout
            */
           RoutingTableEntry toOrigin = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
           m_routing_table.LookupRoute (origin, toOrigin);
           
           //NB making assumnption that sender is the Origin.nedxtHop route that needs updated
           UpdateRouteLifeTime (p.at(MESSAGE_PACKET_SENDER), ACTIVE_ROUTE_TIMEOUT);
  
           myNeighbour.Update (route.GetNextHop (), ACTIVE_ROUTE_TIMEOUT);
           myNeighbour.Update (p.at(MESSAGE_PACKET_SENDER), ACTIVE_ROUTE_TIMEOUT);
            logInfo("Sending Packet Forward TODO choosing path load etc");
            send_message_data(route.GetNextHop (), device_ip_address, origin, dst,0, p);
           return true;
         }
       else
         {
           if (toDst.GetValidSeqNo ())
             {
                //toDst is made INVALID if no alternative path is provided to dst so then tell every to not use this node anymore
               SendRerrWhenNoRouteToForward (dst, toDst.GetSeqNo (), origin);
               logInfo ("Drop packet because no route to forward it sending SendRerrWhenNoRouteToForward line 621.");
               return false;
             }
         }
     }
    logInfo ("Drop packet because no route to forward it sending SendRerrWhenNoRouteToForward line 621.");
   SendRerrWhenNoRouteToForward (dst, 0, origin);
   return false;
    } 
    
bool Route_Input(std::vector<uint8_t> p, uint8_t dst, uint8_t origin)
{
       std::vector<RouteEntity> route_list;
       logInfo ("Routing the input Route_Input()");
   // Deferred route request
//   if (idev == m_lo)
//     {
//       DeferredRouteOutputTag tag;
//       if (p->PeekPacketTag (tag))
//         {
//           DeferredRouteOutput (p, header, ucb, ecb);
//           return true;
//         }
//     }
  
   // Duplicate of own packet
   if (origin == device_ip_address)
     {
         std::cout<<"Why did origin receive message from itself"<<endl;
       return true;
     }
  
   // AODV is not a multicast routing protocol
   //TODO check for AODVM
//   if (dst.IsMulticast ())
//     {
//       return false;
//     }
  //TODO should I check for dublicate packets
   // Broadcast local delivery/forwarding
   // Checks if this node is the destination
   if (dst == device_ip_address)
     {
       UpdateRouteLifeTime (origin, ACTIVE_ROUTE_TIMEOUT);
       RoutingTableEntry toOrigin = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
       if (m_routing_table.LookupValidRoute (origin, toOrigin))
         {
           UpdateRouteLifeTime (p.at(MESSAGE_PACKET_SENDER), ACTIVE_ROUTE_TIMEOUT);
           myNeighbour.Update (p.at(MESSAGE_PACKET_SENDER), ACTIVE_ROUTE_TIMEOUT);
           std::cout<<"Received message ";
           for (std::vector<uint8_t>::const_iterator i = p.begin (); i != p.end (); ++i)
           {
               std::cout<<*i;
           }
            std::cout<<" from "<<origin<<endl;
         }
       return true;
     }
  
   // Forwarding
   //forward_message(std::vector<uint8_t> p, uint8_t dst, uint8_t origin)
   return forward_message (p, dst, origin);
    }
    
void SendHallo()
{
       /* Broadcast a MODIFIED RREP with TTL = 1 with the RREP message fields set as follows:
    *   Destination IP Address         The node's IP address.
    *   Destination Sequence Number    The node's latest sequence number.
    *   Hop Count                      0
    *   Lifetime                       AllowedHelloLoss * HelloInterval
    */
//    int send_hallo(uint8_t recipient_add, uint8_t sender_address, uint8_t source_add, 
//    uint8_t destination_add, uint8_t prefix_size, uint8_t hop_count, uint8_t lifetime, uint8_t dest_seq_num, uint8_t m_ttl, uint8_t r_ack);
//NB EVERYTHING SENT OVER MESSAGE WRT TIMING IS IN SECONDS TO KEEP PACKET SMALLER
    logInfo("Broadcasting a Hallo message");
    //NB 255 REFERS TO WILD CARD SO ANY NODE MUST ACCEPT THIS
    send_hallo(255,device_ip_address,  device_ip_address, device_ip_address, 0, 0, HELLO_INTERVAL*ALLOWED_HELLO_LOSS/1000, m_sequence, 1, 0); 
    }
    
void ProcessHello(std::vector<uint8_t> packet)
{
       logInfo ("Received a hello from TODO add info");
   /*
    *  Whenever a node receives a Hello message from a neighbor, the node
    * SHOULD make sure that it has an active route to the neighbor, and
    * create one if necessary.
    */
    //First add the time neighbour updates have been sent to the tracker
    if(m_hallo_tracker.empty())
    {
        //simply add the new entry
        m_hallo_tracker.insert(std::make_pair (packet.at(RREP_PACKET_DESTINATION_IP), clock()));
        }
    else
    {
        //check if it is in the map
        auto element = m_hallo_tracker.find(packet.at(RREP_PACKET_DESTINATION_IP));
        if (element->first == packet.at(RREP_PACKET_DESTINATION_IP))
        {
            //the key does exhist update the value
            element->second = clock();
            }
        }
        
    std::vector<RouteEntity> route_list;
   RoutingTableEntry toNeighbor = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);;
   if (!m_routing_table.LookupRoute (packet.at(RREP_PACKET_DESTINATION_IP), toNeighbor))
     {
       RoutingTableEntry newEntry = RoutingTableEntry(/*dst=*/ packet.at(RREP_PACKET_DESTINATION_IP), /*seqno=*/ packet.at(RREP_PACKET_DESTINATION_SEQ),
                                               /*hop=*/ 1, /*nextHop=*/ route_list, /*lifeTime= (times 1000 to make in milliseconds)*/ packet.at(RREP_PACKET_LIFETIME)*CLOCKS_PER_SEC, device_ip_address);
        /*validSeqNo=true*/
       newEntry.SetValidSeqNo(true);
       //adding the hop to the multipath
       newEntry.SetNextHop();
       m_routing_table.AddRoute (newEntry,1);
        RouteEntity newEntity = RouteEntity(packet.at(RREP_PACKET_DESTINATION_IP),1,packet.at(packet.at(RREP_PACKET_DESTINATION_IP)));
        newEntry.SetValidSeqNo(true);
        newEntry.addRoutingEntity(newEntity);
        newEntry.update_advertise_hop();
        newEntry.update_LoRa_path();
       m_routing_table.AddRoute (newEntry,0);
     }
   else
     {
       if (HELLO_INTERVAL*ALLOWED_HELLO_LOSS*CLOCKS_PER_SEC+clock()>toNeighbor.GetLifeTime ())
       {
                  toNeighbor.SetLifeTime (HELLO_INTERVAL*ALLOWED_HELLO_LOSS);
           }
           else
           {
               toNeighbor.SetLifeTime (toNeighbor.GetLifeTime ()-clock());
               }
       toNeighbor.SetSeqNo (packet.at(RREP_PACKET_DESTINATION_SEQ));
       toNeighbor.SetValidSeqNo (true);
       toNeighbor.SetFlag (VALID);
       toNeighbor.SetHop (1);
       toNeighbor.SetNextHop ();
       m_routing_table.Update (toNeighbor);
     }
   if (ENABLE_HALLO)
     {
       myNeighbour.Update (packet.at(RREP_PACKET_DESTINATION_IP),HELLO_INTERVAL*ALLOWED_HELLO_LOSS*CLOCKS_PER_SEC);
     }
    myNeighbour.Print();
    }



void receive_rreq(std::vector<uint8_t> packet,  uint8_t source)
{
   logInfo("Received an RREQ AOMDV mode");
  std::vector<RouteEntity> route_list;
   uint8_t id = packet.at(RREQ_PACKET_RREQ_ID);
   uint8_t origin = packet.at(RREQ_PACKET_ORIGIN_IP);

   RoutingTableEntry checker = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   
   if (m_routing_table.LookupRoute (origin, checker))
     {
       //Here origin is not empty so if fresher packet then clear everything
       if (checker.GetValidSeqNo ())
       {
           //Valid to check if neweer packet
           if (int8_t (packet.at(RREQ_PACKET_ORIGIN_SEQ)) - int8_t (checker.GetSeqNo ()) > 0)
           {
                //Fresher RREQ so clear the trackers.
                   neighbour_source_list.clear();
                   firsthop_counter.clear();
                   firsthop_list.clear();
           }
       }
       else 
       {
                 //Treat this as fresher RREQ so clear the trackers.
                   neighbour_source_list.clear();
                   firsthop_counter.clear();
                   firsthop_list.clear();          
       }
     }


   #if ACTIVE_USER == CLIENT_NODE || ACTIVE_USER == ROUTING_NODE
    //During RREQ AOMDV does not drop packets. Instead it keeps a list of source neighbours that RREQ came from
    //TODO must the list be reset during retry?
    //Also this holds only for every other route. Destination replies and sees every unique one 
    if (firsthop_list.empty())
    {
        //Nothing in it so fill up with first entry
        std::vector<uint8_t> holder;
        holder.push_back(packet.at(RREQ_PACKET_ORIGIN_NEIGH));
        firsthop_list.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_IP), holder));
        //Also keep track of the source the nighbour came from
        std::vector<uint8_t> neigh_holder;
        neigh_holder.push_back(packet.at(RREQ_SENDER));
        neighbour_source_list.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_NEIGH), neigh_holder));
    }
    else 
    {
        //See if already in the list of neighbours
        auto element=firsthop_list.find(packet.at(RREQ_PACKET_ORIGIN_IP));
        if (element->first == packet.at(RREQ_PACKET_ORIGIN_IP))
        {
            //destination has been found update the addresses that has been received from
            //First see if ORIGIN_NEIGH packet has been received'
            if (std::find(element->second.begin(), element->second.end(), packet.at(RREQ_PACKET_ORIGIN_NEIGH))!=element->second.end())
            {
                //This RREQ has been received check if it is a new unique entry in neigh_holder
                auto neigh_element=neighbour_source_list.find(packet.at(RREQ_PACKET_ORIGIN_NEIGH));
                //First find the key in the map
                if (element->first == packet.at(RREQ_PACKET_ORIGIN_NEIGH))
                {
                    //The key has been found check if the source exhists
                    if (std::find(neigh_element->second.begin(), neigh_element->second.end(), packet.at(RREQ_SENDER))!=neigh_element->second.end())
                        {
                            //Exhists now drop this useless packet
                            return;
                        }
                    else
                        {
                            //add to the neighbour source add list
                            neigh_element->second.push_back(packet.at(RREQ_SENDER));
                            //This does not stop a packet from entering with a higher hop count if a new source for this add is found
                            //But during origin update there will be a check to stop this from forming loops
                        }
                }
                else
                {
                    //At the start I always add a firsthop entry and neigh source entry this can't happen
                    std::cout<<"Error at entering new source into neighbour add list"<<endl;
                }

            }
            else {
                element->second.push_back(packet.at(RREQ_PACKET_ORIGIN_NEIGH));//add address to the list
                //This is a new neighbour so add new entry to the source tracking list
                std::vector<uint8_t> neigh_holder;
                neigh_holder.push_back(packet.at(RREQ_SENDER));
                neighbour_source_list.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_NEIGH), neigh_holder));
            }
        }
        else {
            //destination not been found add it to the queue
            std::vector<uint8_t> holder;
            holder.push_back(packet.at(RREQ_PACKET_ORIGIN_NEIGH));
            firsthop_list.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_IP), holder));
            //Also keep track of the source the nighbour came from
            std::vector<uint8_t> neigh_holder;
            neigh_holder.push_back(packet.at(RREQ_SENDER));
            neighbour_source_list.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_NEIGH), neigh_holder));
        }
    }
   #elif ACTIVE_USER == DESTINATION_NODE
    //Here looser packet entry restrictions are passed since this is destination node
    //Only setup route back if hops smaller or same as advertise routing
    if (firsthop_list.empty())
    {
        //Nothing in it so fill up with first entry
        std::vector<uint8_t> holder;
        holder.push_back(packet.at(RREQ_PACKET_ORIGIN_NEIGH));
        firsthop_list.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_IP), holder));
        //Keep track of amount of RREQ received if below K
        firsthop_counter.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_NEIGH), 1));
    }
    else 
    {
        //See if already in the list of neighbours
        auto element=firsthop_list.find(packet.at(RREQ_PACKET_ORIGIN_IP));
        if (element->first == packet.at(RREQ_PACKET_ORIGIN_IP))
        {
            //destination has been found update the addresses that has been received from
            //First see if ORIGIN_NEIGH packet has been received'
            if (std::find(element->second.begin(), element->second.end(), packet.at(RREQ_PACKET_ORIGIN_NEIGH))!=element->second.end())
            {
                //check if the amount received from this neighbour is smaller
                //First find the entry in the counter list
                auto element_counter=firsthop_counter.find(packet.at(RREQ_PACKET_ORIGIN_NEIGH));
                if (element_counter->first == packet.at(RREQ_PACKET_ORIGIN_NEIGH))
                {
                    //found it
                    if (element_counter->second>K_REPEATS)
                    {
                        return;//count too high drop
                    }
                    else  
                    {
                        element_counter->second++; //increment the amount found
                    }
                }
                else 
                {
                    std::cout<<"Error when trying to increase k count"<<endl;
                }
            }
            else {
                element->second.push_back(packet.at(RREQ_PACKET_ORIGIN_NEIGH));//add address to the list
                //This is a new neighbour so add new entry to the source tracking list
                //Keep track of amount of RREQ received if below K
                firsthop_counter.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_NEIGH), 1));
            }
        }
        else {
            //destination not been found add it to the queue
            std::vector<uint8_t> holder;
            holder.push_back(packet.at(RREQ_PACKET_ORIGIN_NEIGH));
            firsthop_list.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_IP), holder));
            //Keep track of amount of RREQ received if below K
            firsthop_counter.insert(std::make_pair (packet.at(RREQ_PACKET_ORIGIN_NEIGH), 1));
        }
    }
   #endif

  
   // Increment RREQ hop count
   uint8_t hop = packet.at(RREQ_PACKET_HOP_COUNT) + 1;
   uint8_t hop_rrep = hop;
   packet.at(RREQ_PACKET_HOP_COUNT) = hop_rrep;
  
   /*
    *  When the reverse route is created or updated, the following actions on the route are also carried out:
    *  1. the Originator Sequence Number from the RREQ is compared to the corresponding destination sequence number
    *     in the route table entry and copied if greater than the existing value there
    *  2. the valid sequence number field is set to true;
    *  3. the next hop in the routing table becomes the node from which the  RREQ was received
    *  4. the hop count is copied from the Hop Count in the RREQ message;
    *  5. the Lifetime is set to be the maximum of (ExistingLifetime, MinimalLifetime), where
    *     MinimalLifetime = current time + 2*NetTraversalTime - 2*HopCount*NodeTraversalTime
    */
   RoutingTableEntry toOrigin = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   
   if (!m_routing_table.LookupRoute (origin, toOrigin))
     {
       
       RoutingTableEntry newEntry =RoutingTableEntry( /*dst=*/ origin,/*seqNo=*/ packet.at(RREQ_PACKET_ORIGIN_SEQ),/*hops=*/ hop,route_list,  /*timeLife=*/MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000, device_ip_address);
       RouteEntity newEntity = RouteEntity(source,hop,packet.at(RREQ_PACKET_ORIGIN_NEIGH));
        newEntry.SetValidSeqNo(true);
        newEntry.addRoutingEntity(newEntity);
        newEntry.update_advertise_hop();
        newEntry.update_LoRa_path();
       m_routing_table.AddRoute (newEntry,0);
     }
   else
     {
       if (toOrigin.GetValidSeqNo ())
         {
           if (int8_t (packet.at(RREQ_PACKET_ORIGIN_SEQ)) - int8_t (toOrigin.GetSeqNo ()) > 0)
             {
               toOrigin.SetSeqNo (packet.at(RREQ_PACKET_ORIGIN_SEQ));
               //Here is the unique AOMDV for finding path backwards
               if (device_ip_address!=packet.at(RREQ_PACKET_DESTINATION_IP))
               {
                   //This is not the origin
                   toOrigin.SetHop(255); //Set to infinity
                   toOrigin.clear_route_list(); //Route list = NULL
                   RouteEntity newEntity = RouteEntity(source,hop,packet.at(RREQ_PACKET_ORIGIN_NEIGH)); //Insert this into the route list
                   toOrigin.addRoutingEntity(newEntity);
               }
               else {
                   toOrigin.SetHop(0); //add hop count is 0
               }
             }
            else if ((int8_t (packet.at(RREQ_PACKET_ORIGIN_SEQ)) - int8_t (toOrigin.GetSeqNo ()) == 0) && (toOrigin.GetHop()>=packet.at(RREQ_PACKET_HOP_COUNT)) ) {
            //Second case NB modified it so it is less strict than pure AOMDV
                RouteEntity newEntity = RouteEntity(source,hop,packet.at(RREQ_PACKET_ORIGIN_NEIGH)); //Insert this into the route list
                toOrigin.addRoutingEntity(newEntity);
            }
         }
       else
         {
             //Treat this as when a fresher sequence number came
                toOrigin.SetSeqNo (packet.at(RREQ_PACKET_ORIGIN_SEQ));
               //Here is the unique AOMDV for finding path backwards
               if (device_ip_address!=packet.at(RREQ_PACKET_DESTINATION_IP))
               {
                   //This is not the origin
                   toOrigin.SetHop(255); //Set to infinity
                   toOrigin.clear_route_list(); //Route list = NULL
                   RouteEntity newEntity = RouteEntity(source,hop,packet.at(RREQ_PACKET_ORIGIN_NEIGH)); //Insert this into the route list
                   toOrigin.addRoutingEntity(newEntity);
               }
               else {
                   toOrigin.SetHop(0); //add hop count is 0
               }
         }
       toOrigin.SetValidSeqNo (true);
       m_routing_table.Update (toOrigin);
       myNeighbour.Update (source,CLOCKS_PER_SEC/1000*ALLOWED_HELLO_LOSS*HELLO_INTERVAL);
     }
  
    //This is fine maintain this to keep routes to potential new destinations
   RoutingTableEntry toNeighbor = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,ACTIVE_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   if (!m_routing_table.LookupRoute (source, toNeighbor))
     {
       logInfo ("Neighbor: not found in routing table. Creating an entry");
       
       RoutingTableEntry newEntry  = RoutingTableEntry( /*dst=*/ source,/*seqNo=*/ packet.at(RREQ_PACKET_ORIGIN_SEQ),/*hops=*/ 1, route_list, /*timeLife=*/MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000, device_ip_address);
       RouteEntity newEntity = RouteEntity(source,1,source);
       newEntry.addRoutingEntity(newEntity);
       newEntry.SetNextHop();
       m_routing_table.AddRoute (newEntry,0);
     }
   else
     {
       toNeighbor.SetLifeTime (MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000);
       toNeighbor.SetValidSeqNo (false);
       toNeighbor.SetSeqNo (packet.at(RREQ_PACKET_ORIGIN_SEQ));
       toNeighbor.SetFlag (VALID);
       toNeighbor.SetHop (1);
       toNeighbor.SetNextHop ();
       m_routing_table.Update (toNeighbor);
     }
     
   myNeighbour.Update (origin, HELLO_TIME_OUT*CLOCKS_PER_SEC/1000);
//  
//   NS_LOG_LOGIC (receiver << " receive RREQ with hop count " << static_cast<uint32_t> (rreqHeader.GetHopCount ())
//                          << " ID " << rreqHeader.GetId ()
//                          << " to destination " << rreqHeader.GetDst ());
  
   //  A node generates a RREP if either:
   //  (i)  it is itself the destination,
   if (packet.at(RREQ_PACKET_DESTINATION_IP)==device_ip_address)
     {
         //Destination sends reply up to k times to
       m_routing_table.LookupRoute (origin, toOrigin);
       logInfo ("Send reply since I am the destination");
       SendReply (packet, toOrigin, packet.at(RREP_PACKET_ORIGIN_NEIGH));
       return;
     }
   /*
    * (ii) or it has an active route to the destination, the destination sequence number in the node's existing route table entry for the destination
    *      is valid and greater than or equal to the Destination Sequence Number of the RREQ, and the "destination only" flag is NOT set.
    */
   RoutingTableEntry toDst = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   uint8_t dst = packet.at(RREQ_PACKET_DESTINATION_IP);
   
   if (m_routing_table.LookupRoute (dst, toDst))
     {
       /*
        * Drop RREQ, This node RREP will make a loop.
        * Validate if conditions exhists for one entry. If so remove it. If the only entry then return.
        */
        std::vector<RouteEntity> entity_list_Dst = toDst.get_entity_with_neigh_source(packet.at(RREQ_PACKET_ORIGIN_NEIGH));
        for (int i =0;i<entity_list_Dst.size();i++)
        {
            if (entity_list_Dst.at(i).get_next_hop() == source)
                {
                logInfo("This packet is me so remove from entity list else it makes a loop");
                toDst.removeRouteEntity(i);
                }
        }
        if (toDst.get_entity_with_neigh_source(packet.at(RREQ_PACKET_ORIGIN_NEIGH)).size()==0)
        {
            return; //there is no entities to reply to so just leave
        }

       /*
        * The Destination Sequence number for the requested destination is set to the maximum of the corresponding value
        * received in the RREQ message, and the destination sequence value currently maintained by the node for the requested destination.
        * However, the forwarding node MUST NOT modify its maintained value for the destination sequence number, even if the value
        * received in the incoming RREQ is larger than the value currently maintained by the forwarding node.
        */
       if (( (packet.at(RREQ_PACKET_UNKOWN_SEQ)==1) || (int8_t (toDst.GetSeqNo ()) - int8_t (packet.at(RREQ_PACKET_DESTINATION_SEQ)) >= 0))
           && toDst.GetValidSeqNo () )
         {
           //if (!rreqHeader.GetDestinationOnly () && toDst.GetFlag () == VALID)
           if (toDst.GetFlag () == VALID)
             {
               m_routing_table.LookupRoute (origin, toOrigin);
               //Create this function
               logInfo("Sending route by intermediate node");
               SendReplyByIntermediateNode (toDst, toOrigin, packet.at(RREQ_PACKET_G),packet.at(RREQ_PACKET_ORIGIN_NEIGH),source);
               return;
             }
            
           uint8_t seq_rrep = toDst.GetSeqNo ();
           uint8_t seq_known_rrep = 0;
           packet.at(RREQ_PACKET_DESTINATION_SEQ) = seq_rrep;
           packet.at(RREQ_PACKET_UNKOWN_SEQ) = seq_known_rrep;
         }
     }
   if (packet.at(RREQ_PACKET_TTL) < 2)
     {
       logDebug ("TTL exceeded. Drop RREQ origin " );
       return;
     }
    
    // //Schedule a wait thing to wait to RREQ again depedning on repeats.
    // ScheduleRreqRetry (dst);
  //JUST SENDING AN RREQ AGAIN I GUESS
    //When sending RREQ update the hop counts
    toOrigin.update_advertise_hop(); 
    packet.at(RREQ_PACKET_TTL) = packet.at(RREQ_PACKET_TTL) - 1; 
    //change RREQ source to this address
    packet.at(RREQ_SENDER) = device_ip_address;
    if ((firsthop_list.size()<=1) && (firsthop_list.begin()->second.size()<=1))
    {
        //THis is the first RREQ so only reply to this 
        //Sending RREQ to every known neighbour
        std::vector<Neighbors::Neighbor> current_neighbours = myNeighbour.getListNeighbours();
        for (int i = 0;i<current_neighbours.size();i++)
        {
        //DOnt want it to needlessly go back to origin
        //Also don't want it to be needlessly sent back to source else it will make loop
        if ((current_neighbours.at(i).m_neighborAddress!=packet.at(RREQ_PACKET_ORIGIN_IP)) && (current_neighbours.at(i).m_neighborAddress!=packet.at(RREQ_SENDER)))
        {
            packet.at(RREQ_RECIPIENT) = current_neighbours.at(i).m_neighborAddress;
            send_data(packet);
            }
        
        }
        }
    } 
    
void receive_rrep(std::vector<uint8_t> packet, uint8_t my, uint8_t src)
{
    //For AOMDV to create link disjointed I need to keep track of the unique rrep sources.
    //The built in hop count and sequence number will help manage packets.
    //Addtionally I will monitor where RREP packets came from when they go throuhg the check
    //This is to ensure no dublicates are obtained 
        //Create dummy routelist for entry initialization
    std::vector<RouteEntity> route_list;
    RoutingTableEntry checker = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   
   if (m_routing_table.LookupRoute (packet.at(RREP_PACKET_DESTINATION_IP), checker))
     {
       //Here origin is not empty so if fresher packet then clear everything
       if (checker.GetValidSeqNo ())
       {
           //Valid to check if neweer packet
           if (int8_t (packet.at(RREQ_PACKET_ORIGIN_SEQ)) - int8_t (checker.GetSeqNo ()) > 0)
           {
                //Fresher RREQ so clear the trackers.
                rrep_firsthop_list.clear();
           }
       }
       else 
       {
            //Treat this as fresher RREQ so clear the trackers.
            rrep_firsthop_list.clear();       
       }
     }

    if (rrep_firsthop_list.empty())
    {
        //Nothing in it so fill up with first entry
        std::vector<uint8_t> holder;
        holder.push_back(src);
        rrep_firsthop_list.insert(std::make_pair (packet.at(RREP_PACKET_DESTINATION_IP), holder));
    }
    else 
    {
        //See if already in the list of neighbours
        auto element=rrep_firsthop_list.find(packet.at(RREP_PACKET_DESTINATION_IP));
        if (element->first == packet.at(RREP_PACKET_DESTINATION_IP))
        {
            //destination has been found update the addresses that has been received from
            //First see if SOURCE packet has been received'
            if (std::find(element->second.begin(), element->second.end(), src)!=element->second.end())
            {
                //This RREP has been received check if it is a new unique entry in neigh_holder
                std::cout<<"RREP packet from source "<<src<<" has been received drop packet."<<endl;
                return;
            }
            else {
                element->second.push_back(src);//add address to the list
            }
        }
        else {
        //Nothing in it so fill up with first entry
        std::vector<uint8_t> holder;
        holder.push_back(src);
        rrep_firsthop_list.insert(std::make_pair (packet.at(RREP_PACKET_DESTINATION_IP), holder));
        }
    }
    
    logInfo("Received an RREP replying to it now");
   uint8_t dst = packet.at(RREP_PACKET_DESTINATION_IP);
   uint8_t hop = packet.at(RREP_PACKET_HOP_COUNT) + 1;
   packet.at(RREP_PACKET_HOP_COUNT) = hop;
  
   // If RREP is Hello message
   if (dst == packet.at(RREP_PACKET_ORIGIN_IP))
     {
       ProcessHello (packet);
       logInfo("Hallo message received TODO this");
       return;
     }
  
   /*
    * If the route table entry to the destination is created or updated, then the following actions occur:
    * -  the route is marked as active,
    * -  the destination sequence number is marked as valid,
    * -  the next hop in the route entry is assigned to be the node from which the RREP is received,
    *    which is indicated by the source IP address field in the IP header,
    * -  the hop count is set to the value of the hop count from RREP message + 1
    * -  the expiry time is set to the current time plus the value of the Lifetime in the RREP message,
    * -  and the destination sequence number is the Destination Sequence Number in the RREP message.
    */ 
   RoutingTableEntry toDst = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   if (m_routing_table.LookupRoute (dst, toDst))
     {
       /*
        * The existing entry is updated only in the following circumstances:
        * (i) the sequence number in the routing table is marked as invalid in route table entry.
        * Count this as when a fresh sequence number comes
        * FOr all these fresh sequence numbers delete the exhisting trackers
        */
       if (!toDst.GetValidSeqNo ())
         {
                //Treat this as when a fresher sequence number came
                toDst.SetSeqNo (packet.at(RREP_PACKET_DESTINATION_SEQ));
               //Here is the unique AOMDV for finding path backwards
               if (device_ip_address!=packet.at(RREP_PACKET_DESTINATION_IP))
               {
                   //This is not the origin
                   toDst.SetHop(255); //Set to infinity
                   toDst.clear_route_list(); //Route list = NULL
                   RouteEntity newEntity = RouteEntity(src,hop,src); //Insert this into the route list
                   toDst.addRoutingEntity(newEntity);
                    toDst.SetNextHop();
                    toDst.SetValidSeqNo(true);
                    m_routing_table.Update (toDst);
               }
               else {
                   toDst.SetHop(0); //add hop count is 0
                    toDst.SetNextHop();
                    toDst.SetValidSeqNo(true);
                    m_routing_table.Update (toDst);
               }
         }
       // (ii)the Destination Sequence Number in the RREP is greater than the node's copy of the destination sequence number and the known value is valid,
       else if ((int8_t (packet.at(RREP_PACKET_DESTINATION_SEQ)) - int8_t (toDst.GetSeqNo ())) > 0)
         {
                toDst.SetSeqNo (packet.at(RREP_PACKET_DESTINATION_SEQ));
               //Here is the unique AOMDV for finding path backwards
               if (device_ip_address!=packet.at(RREP_PACKET_DESTINATION_IP))
               {
                   //This is not the origin
                   toDst.SetHop(255); //Set to infinity
                   toDst.clear_route_list(); //Route list = NULL
                   RouteEntity newEntity = RouteEntity(src,hop,src); //Insert this into the route list
                   toDst.addRoutingEntity(newEntity);
                    toDst.SetNextHop();
                    toDst.SetValidSeqNo(true);
                    m_routing_table.Update (toDst);
               }
               else {
                   toDst.SetHop(0); //add hop count is 0
                    toDst.SetNextHop();
                    toDst.SetValidSeqNo(true);
                    m_routing_table.Update (toDst);
               }
         }
       else
         {
           // (iii) the sequence numbers are the same, but the route is marked as inactive.
           if ((packet.at(RREP_PACKET_DESTINATION_SEQ) == toDst.GetSeqNo ()) && (toDst.GetFlag () != VALID))
             {
                toDst.SetSeqNo (packet.at(RREP_PACKET_DESTINATION_SEQ));
               //Here is the unique AOMDV for finding path backwards
               if (device_ip_address!=packet.at(RREP_PACKET_DESTINATION_IP))
               {
                   //This is not the origin
                   toDst.SetHop(255); //Set to infinity
                   toDst.clear_route_list(); //Route list = NULL
                   RouteEntity newEntity = RouteEntity(src,hop,src); //Insert this into the route list
                   toDst.addRoutingEntity(newEntity);
                    toDst.SetNextHop();
                    toDst.SetValidSeqNo(true);
                    m_routing_table.Update (toDst);
               }
               else {
                   toDst.SetHop(0); //add hop count is 0
                    toDst.SetNextHop();
                    toDst.SetValidSeqNo(true);
                    m_routing_table.Update (toDst);
               }
             }
           // (iv)  the sequence numbers are the same, and the New Hop Count is smaller than the hop count in route table entry.
           //Here I need to track if the source is unique
           else if ((packet.at(RREP_PACKET_DESTINATION_SEQ) == toDst.GetSeqNo ()) && (hop <= toDst.GetHop ()))
             {
                    RouteEntity newEntity = RouteEntity(src,hop,src); //Insert this into the route list
                    toDst.addRoutingEntity(newEntity);
                    toDst.SetNextHop();
                    toDst.SetValidSeqNo(true);
                    m_routing_table.Update (toDst);
             }
         }
     }
   else
     {
       // The forward route for this destination is created if it does not already exist.
       logInfo ("New Route Is Created");
        RoutingTableEntry newEntry = RoutingTableEntry(dst, packet.at(RREP_PACKET_DESTINATION_SEQ),255, route_list, packet.at(RREP_PACKET_LIFETIME),device_ip_address);
        newEntry.SetNextHop();
        newEntry.SetValidSeqNo(true);
        RouteEntity newEntity = RouteEntity(packet.at(RREP_PACKET_SENDER),hop,src);
        newEntry.addRoutingEntity(newEntity);
       m_routing_table.AddRoute (newEntry,0);
     }
   // Acknowledge receipt of the RREP by sending a RREP-ACK message back
   if (packet.at(RREP_PACKET_ACK)==1)
     {
       logInfo ("Sending Reply ACK TODO");
       //SendReplyAck (sender);
       packet.at(RREP_PACKET_ACK) = 0;
     }
   if (packet.at(RREP_PACKET_ORIGIN_IP)==device_ip_address)
     {
       if (toDst.GetFlag () == IN_SEARCH)
         {
        RoutingTableEntry newEntry = RoutingTableEntry(dst, packet.at(RREP_PACKET_DESTINATION_SEQ),255, route_list, packet.at(RREP_PACKET_LIFETIME),device_ip_address);
        newEntry.SetNextHop();
        newEntry.SetValidSeqNo(true);
        RouteEntity newEntity = RouteEntity(packet.at(RREP_PACKET_SENDER),hop,src);
        newEntry.addRoutingEntity(newEntity);
           m_routing_table.Update (newEntry);
           logInfo("Stopping RREQ timer TODO");
            m_addressReqTimer.erase(dst);//Deleting all entries after visited
            m_rreq_retry.erase(dst);
//           m_addressReqTimer[dst].Cancel ();
//           m_addressReqTimer.erase (dst);
         }
       m_routing_table.LookupRoute (dst, toDst);
       logInfo("Will be sending Packet From Message Queue I found the route");
       //SendPacketFromQueue (dst, toDst.GetRoute ());
       return;
     }
  
  //Just update toOrigin timers as this will be used
   RoutingTableEntry toOrigin = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   if (!m_routing_table.LookupRoute (packet.at(RREP_PACKET_ORIGIN_IP), toOrigin) || toOrigin.GetFlag () == IN_SEARCH)
     {
       logInfo("!m_routing_table.LookupRoute (packet.at(RREP_PACKET_ORIGIN_IP), toOrigin) || toOrigin.GetFlag () == IN_SEARCH impossible drop route");
       return; // Impossible! drop.
     }
     if (MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000+clock()>toOrigin.GetLifeTime ())
     {
         toOrigin.SetLifeTime (MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000);
         }
         else
         {
             toOrigin.SetLifeTime (toOrigin.GetLifeTime ()-clock());
             }
   m_routing_table.Update (toOrigin);
  
   // Update information about precursors
   if (m_routing_table.LookupValidRoute (packet.at(RREP_PACKET_DESTINATION_IP), toDst))
     {
         //Adding the precursor information for the relevant entries
        std::vector<uint8_t> hop_list_origin = toOrigin.GetNextHop(packet.at(RREP_PACKET_ORIGIN_NEIGH)); 
        std::vector<uint8_t> hop_list_Dst = toDst.GetNextHop(src); 
        std::vector<RouteEntity> entity_list_origin = toOrigin.get_entity_with_neigh_source(packet.at(RREP_PACKET_ORIGIN_NEIGH));
        std::vector<RouteEntity> entity_list_dst = toDst.get_entity_with_neigh_source(src);
        std::vector<RoutingTableEntry> toNextHopToDst_list;
        std::vector<RoutingTableEntry> toNextHopToOrigin_list;

        toDst.clear_route_list();
        for (int i = 0;i<entity_list_dst.size();i++)
        {
            for(int j = 0;j<hop_list_origin.size();j++)
            {
                //adding precursor to every new entry from source
                entity_list_dst.at(i).InsertPrecursor(hop_list_origin.at(j));
                toDst.addRoutingEntity(entity_list_origin.at(i));
            }
        }
        toDst.SetNextHop();
       m_routing_table.Update (toDst);

        //FOr every hop to dest need to find route entry and for each of it's hops use the origin hop as the precursor
        for(int i = 0;i<hop_list_Dst.size();i++)
            {
                //adding precursor to every new entry from source
                toNextHopToDst_list.push_back(RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address));
            for(int j = 0;j<hop_list_origin.size();j++)
                {
                    //adding precursor to every new entry from source
                    m_routing_table.LookupRoute (hop_list_Dst.at(i), toNextHopToDst_list.at(i));
                    std::vector<RouteEntity> temp = toNextHopToDst_list.at(i).get_entity_with_neigh_source(src);
                    toNextHopToDst_list.at(i).clear_route_list();
                    for (int l = 0;l<temp.size();l++)
                    {
                        for(int m = 0;m<hop_list_Dst.size();m++)
                        {
                            //adding precursor to every new entry from source
                            temp.at(l).InsertPrecursor(hop_list_Dst.at(m));
                            toNextHopToDst_list.at(i).addRoutingEntity(temp.at(l));
                        }
                    }  
                    toNextHopToDst_list.at(i).SetNextHop();
                    m_routing_table.Update (toNextHopToDst_list.at(i)) ;                
                }
            }
  
        toOrigin.clear_route_list();
        for (int i = 0;i<entity_list_origin.size();i++)
        {
            for(int j = 0;j<hop_list_Dst.size();j++)
            {
                //adding precursor to every new entry from source
                entity_list_origin.at(i).InsertPrecursor(hop_list_Dst.at(j));
                toOrigin.addRoutingEntity(entity_list_origin.at(i));
            }
        }
        toOrigin.SetNextHop();
       m_routing_table.Update (toOrigin);

        //FOr every hop to dest need to find route entry and for each of it's hops use the origin hop as the precursor
        for(int i = 0;i<hop_list_origin.size();i++)
            {
                //adding precursor to every new entry from source
                toNextHopToOrigin_list.push_back(RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address));
            for(int j = 0;j<hop_list_Dst.size();j++)
                {
                    //adding precursor to every new entry from source
                    m_routing_table.LookupRoute (hop_list_origin.at(i), toNextHopToOrigin_list.at(i));
                    std::vector<RouteEntity> temp = toNextHopToOrigin_list.at(i).get_entity_with_neigh_source(packet.at(RREP_PACKET_ORIGIN_NEIGH));
                    toNextHopToOrigin_list.at(i).clear_route_list();
                    for (int l = 0;l<temp.size();l++)
                    {
                        for(int m = 0;m<hop_list_origin.size();m++)
                        {
                            //adding precursor to every new entry from source
                            temp.at(l).InsertPrecursor(hop_list_origin.at(m));
                            toNextHopToOrigin_list.at(i).addRoutingEntity(temp.at(l));
                        }
                    }  
                    toNextHopToOrigin_list.at(i).SetNextHop();
                    m_routing_table.Update (toNextHopToOrigin_list.at(i)) ;                
                }
            }
     }
     uint8_t ttl_m = packet.at(RREP_PACKET_TTL);
   if (ttl_m < 2)
     {
       logInfo ("TTL exceeded. Drop RREP destination ");
       return;
     }

    packet.at(RREP_PACKET_TTL) = ttl_m - 1;
    packet.at(RREP_PACKET_SENDER) = device_ip_address;
    std::vector<uint8_t> hop_list_origin = toOrigin.GetNextHop(packet.at(RREP_PACKET_ORIGIN_NEIGH));
    for(int i = 0;i<hop_list_origin.size();i++)
    {
        //Send RREP to every route back to neighbour
        packet.at(RREP_PACKET_RECIPIENT) = hop_list_origin.at(i);
        ThisThread::sleep_for(200ms);
        send_data(packet); //Sending reply back to origin
    }
    }    
 
 
void receive_ack (uint8_t neigh_add)
{
        //Create dummy routelist for entry initialization
    std::vector<RouteEntity> route_list;
    logDebug ("Received an acknowledge from ");
   RoutingTableEntry rt =  RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
   if (m_routing_table.LookupRoute (neigh_add, rt))
     {
       logDebug("Route Exists set flag Valid TODO cancel ack timer");
       //rt.m_ackTimer.Cancel ();
       rt.SetFlag (VALID);
       m_routing_table.Update (rt);
     }   
    }

void receive_rrer(std::vector<uint8_t> p, uint8_t src)
{
    std::vector<RouteEntity> route_list;
    logInfo ("Received an RRER now handling it");
    m_unreachableDstSeqNo.clear();
   std::map<uint8_t, uint32_t> dstWithNextHopSrc;
   std::map<uint8_t, uint32_t> unreachable;
   m_routing_table.GetListOfDestinationWithNextHopAOMDV (src, dstWithNextHopSrc);
   std::pair<uint8_t, uint32_t> un;
   //add all unreachable destinations
   for (int i=0;i<p.at(RRER_PACKET_DESTCOUNT);i++)
   {
       m_unreachableDstSeqNo.insert(std::make_pair (p.at(RRER_PACKET_DEST_DELETE+2*i), p.at(RRER_PACKET_DEST_SSEQ+2*i)));
       }
   //determine the unreachable destinations    
   while (RemoveUnDestination (un))
     {
       for (std::map<uint8_t, uint32_t>::const_iterator i =
              dstWithNextHopSrc.begin (); i != dstWithNextHopSrc.end (); ++i)
         {
           if (i->first == un.first)
             {
               unreachable.insert (un);
             }
         }
     }
  
   std::vector<uint8_t> precursors;
   for (std::map<uint8_t, uint32_t>::const_iterator i = unreachable.begin ();
        i != unreachable.end (); )
     {
       if (!AddUnDestination (i->first, i->second))
         {
                 std::vector<uint8_t> output;
            uint8_t type = 3;
            //INsert the data into the packet
            output.push_back(type);
            output.push_back(0);
            output.push_back(device_ip_address);
            output.push_back(0);
            output.push_back(m_unreachableDstSeqNo.size());
            output.push_back(1);
            for (std::map<uint8_t, uint32_t>::const_iterator i = m_unreachableDstSeqNo.begin ();
        i != m_unreachableDstSeqNo.end ();i++)
                {
            //PUshing in all the destinations
            output.push_back(i->first);
            output.push_back((uint8_t)i->second);   
                }
             //Generating an RRER packet
             m_unreachableDstSeqNo.clear ();
             SendRerrMessage (output, precursors);
             
         }
       else
         {
           RoutingTableEntry toDst = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);;
           m_routing_table.LookupRoute (i->first, toDst);
           toDst.getPrecursorsEntry (precursors);
           ++i;
         }
     }
   if (m_unreachableDstSeqNo.size() != 0)
     {
                 std::vector<uint8_t> output;
            uint8_t type = 3;
            //INsert the data into the packet
            output.push_back(type);
            output.push_back(0);
            output.push_back(device_ip_address);
            output.push_back(0);
            output.push_back(m_unreachableDstSeqNo.size());
            output.push_back(1);
            for (std::map<uint8_t, uint32_t>::const_iterator i = m_unreachableDstSeqNo.begin ();
        i != m_unreachableDstSeqNo.end (); i++)
                {
            //PUshing in all the destinations
            output.push_back(i->first);
            output.push_back((uint8_t)i->second);   
                }
             //Generating an RRER packet
             m_unreachableDstSeqNo.clear ();
             SendRerrMessage (output, precursors);
     }
   m_routing_table.InvalidateRoutesWithDst (unreachable);
   //Deleting neighbour as well
   myNeighbour.RemoveNeighbour(src);
    }
           
void update_node_seq(uint8_t type ,uint8_t seq)
{
    //Check wy this was called
    if (type==ROUTE_REQUEST)
    {
        // -  Immediately before a node originates a route discovery, it MUST
//      increment its own sequence number.  This prevents conflicts with
//      previously established reverse routes towards the originator of a
//      RREQ.
        m_sequence = m_sequence+1;
        }
    else if(type==ROUTE_REPLY)
    {
//          Immediately before a destination node originates a RREP in
//      response to a RREQ, it MUST update its own sequence number to the
//      maximum of its current sequence number and the destination
//      sequence number in the RREQ packet.
        if (m_sequence<seq)
        {
            m_sequence = seq;
            }
        
        }
    } 

void queue_request_queue_handler(void)
{
    main_queue.call(request_queue_handler);
    }
             
void request_queue_handler(void)
{
        //Keep executing this thread
        if(route_queue.GetSize()>0)
        {

            //There is something here
            //QueueEntry (std::vector<uint8_t> packet, clock_t exp)
            std::vector<uint8_t> holder(0,0);
            QueueEntry handleRequest = QueueEntry(holder,0);
            if(route_queue.DequeueFront(handleRequest))
            {
                logInfo("Caught something");
                std::vector<uint8_t> packet = handleRequest.GetPacket ();
                
                switch (packet.at(0))
                {
                    case ROUTE_REQUEST:
                        //Handle RREQ messages
                        if ((packet.at(RREQ_RECIPIENT)==device_ip_address) || (packet.at(RREQ_RECIPIENT)==255))
                        {

                        #if ACTIVE_USER == DESTINATION_NODE
                            //I want to ignore my client node
                            if (packet.at(RREQ_SENDER)!=20)
                            {
                                //not the client so this is fine
                                logInfo("RREQ has been received by node");
                                receive_rreq(packet,packet.at(RREQ_SENDER));
                            }
                        #elif ACTIVE_USER == CLIENT_NODE
                            if (packet.at(RREQ_SENDER)!=100)
                            {
                                //not the client so this is fine
                                logInfo("RREQ has been received by node");
                                receive_rreq(packet,packet.at(RREQ_SENDER));
                            }
                        #else
                            //Packet is for me
                        logInfo("RREQ has been received by node");
                        receive_rreq(packet,packet.at(RREQ_SENDER));
                        #endif

                        }
                        break;
                    case ROUTE_REPLY:
                        //Handle RREP messages
                        if ((packet.at(RREP_PACKET_RECIPIENT)==device_ip_address) || (packet.at(RREP_PACKET_RECIPIENT)==255))
                        {
                            //This is for me
                            logInfo("Got a RREP packet");
                            receive_rrep(packet,packet.at(RREP_PACKET_RECIPIENT),packet.at(RREP_PACKET_SENDER));
                        }
                        break;
                    case ROUTE_ERROR:
                        //Handle RERR Messages
                        break;
                    case ROUTE_REPLY_ACK:
                        //Handle RRER-ACK messages
                        break;
                    case HALLO_MESSAGE:
                        #if ACTIVE_USER == DESTINATION_NODE
                            //I want to ignore my client node
                            if (packet.at(RREP_PACKET_SENDER)!=20)
                            {
                                //not the client so this is fine
                        logInfo("Got a hello message");
                        ProcessHello(packet);
                            }
                        #elif ACTIVE_USER == CLIENT_NODE
                            if (packet.at(RREQ_SENDER)!=100)
                            {
                                //not the client so this is fine
                        logInfo("Got a hello message");
                        ProcessHello(packet);
                            }                            
                        #else
                            //Packet is for me
                        logInfo("Got a hello message");
                        ProcessHello(packet);
                        #endif
                        break;
                    default:
                        logInfo("DEFAQ did you send me");
                        break;
                }
            }
            else
            {
                logInfo("Error Dequed Badly");
            }

        }
        else
        {
            //There was nothing here to handle
            //logInfo("Queue is empty Dequed Badly");
        } 

}
    
void queue_message_handler(void)
{
    main_queue.call(message_queue_handler);
} 

void message_queue_handler(void)
{
    std::vector<uint8_t> holder(0,0);
    QueueEntry handleRequest = QueueEntry(holder,0);
    //First checks what device are we at 
    if (message_request_queue.GetSize()>0)
    {
        logInfo("Something in message_queue_handler()");
    #if ACTIVE_USER == DESTINATION_NODE
    
            if(message_request_queue.DequeueFront(handleRequest))
        {
            if ((handleRequest.GetPacket().at(MESSAGE_PACKET_SENDER)!=20) && (handleRequest.GetPacket().at(MESSAGE_PACKET_RECIPIENT)==device_ip_address))
            {
                //Not from the client
            //Dequed fine
            if (Route_Input(handleRequest.GetPacket(),handleRequest.GetPacket().at(MESSAGE_PACKET_DESTINATION),handleRequest.GetPacket().at(MESSAGE_PACKET_ORIGIN)))
            {
               std::cout<<"Routed forward line 1393"<<endl; //successfully routed
            }
            else
            {
                std::cout<<"Couldn't route forward line 1397"<<endl;
            }                
            }
            else {
            std::cout<<"Packet dropped since received a message from "<<handleRequest.GetPacket().at(MESSAGE_PACKET_SENDER)<<" with intended receiver "
            <<handleRequest.GetPacket().at(MESSAGE_PACKET_RECIPIENT)<<endl;
            }
        }
        else
        {
            std::cout<<"Dequeue failure line 1407"<<endl;
        }

    #elif ACTIVE_USER == ROUTING_NODE   
        if(message_request_queue.DequeueFront(handleRequest))
        {
            if (handleRequest.GetPacket().at(MESSAGE_PACKET_RECIPIENT)==device_ip_address)
            {
                //Not from the client
            //Dequed fine
            if (Route_Input(handleRequest.GetPacket(),handleRequest.GetPacket().at(MESSAGE_PACKET_DESTINATION),handleRequest.GetPacket().at(MESSAGE_PACKET_ORIGIN)))
            {
               std::cout<<"Routed forward line 1419"<<endl; //successfully routed
            }
            else
            {
                std::cout<<"Couldn't route forward line 1423"<<endl;
            }                
            }
            else {
            std::cout<<"Packet dropped since received a message from "<<handleRequest.GetPacket().at(MESSAGE_PACKET_SENDER)<<" with intended receiver "
            <<handleRequest.GetPacket().at(MESSAGE_PACKET_RECIPIENT)<<endl;
            }
        }
        else
        {
            std::cout<<"Dequeue failure line 1389"<<endl;
        }
    #elif ACTIVE_USER == CLIENT_NODE
        //First check if route has been made 
        std::vector<RouteEntity> route_list;
        RoutingTableEntry toDst = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
        if(!m_routing_table.LookupRoute (destination_ip_address, toDst))
        {
            //RREQ hasn's been launched yet so start RREQ
            send_rreq(destination_ip_address);
        }
        else {
            //check the route status
            if (toDst.GetFlag()==VALID)
            {
                //routte exhists so forward
                if(message_request_queue.Dequeue(destination_ip_address, handleRequest))
                {
                    //Successfully dequed packet
                    logInfo("Calling function forward_message line 1453");
                    forward_message(handleRequest.GetPacket(),destination_ip_address,device_ip_address);
                }
                else {
                    std::cout<<"Odd it just disappeared"<<endl;
                }

            }
        }
    #endif
    }
}  
//HERE IS ALL THE MESSAGE HANDLERS REMEMBER THE FOLLOWING TYPES
//      Message Type                    Value
//      ---------------------------     -----
//      Route Request (RREQ)            1
//      Route Reply (RREP)              2
//      Route Error (RERR)              3
//      Route-Reply Ack (RREP-ACK)      4
      

int send_rreq(uint8_t recipient_address, uint8_t sender_address, uint8_t source_add, uint8_t destination_add, uint8_t hop_count, uint8_t rreq_id, uint8_t dest_seq_num, uint8_t origin_seq_num, uint8_t seq_valid, uint8_t g, uint8_t m_ttl, uint8_t r_ack, uint8_t neighbour_source) {
// FORMAT OF RREQ MORE INFO AT https://datatracker.ietf.org/doc/html/rfc3561#section-5.1
//      0                   1                   2                   3
//    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |     Type      |                                   Hop Count   |
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
//   |                            IS Seq valid                            |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                            SHould send response                            |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                    TTL                      |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |                    acknowledge the reply                      |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    std::vector<uint8_t> output;
    uint8_t type = 1;
    //INsert the data into the packet
    output.push_back(type);
    output.push_back(recipient_address);
    output.push_back(sender_address);
    output.push_back(hop_count);
    output.push_back(rreq_id);
    output.push_back(destination_add);
    output.push_back(dest_seq_num);
    output.push_back(source_add);
    output.push_back(origin_seq_num);
    output.push_back(seq_valid);
    output.push_back(g);
    output.push_back(m_ttl);
    output.push_back(r_ack);
    output.push_back(neighbour_source);
    //wait for the radio to be done
    wait_on_radio();
    return send_data(output);
    
    
    }

int send_rrep(uint8_t recipient_add,uint8_t sender_address, uint8_t source_add, uint8_t destination_add, uint8_t prefix_size, uint8_t hop_count, uint8_t lifetime, uint8_t dest_seq_num, uint8_t m_ttl, uint8_t r_ack, uint8_t neighbour_source) {
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
//   |                    TTL                      |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


    std::vector<uint8_t> output;
    uint8_t type = 2;
    //INsert the data into the packet
    output.push_back(type);
    output.push_back(recipient_add);
    output.push_back(sender_address);
    output.push_back(prefix_size);
    output.push_back(hop_count);
    output.push_back(lifetime);
    std::cout<<"The life time value for RREP is "<<lifetime<<endl;
    output.push_back(destination_add);
    output.push_back(dest_seq_num);
    output.push_back(source_add);
    output.push_back(m_ttl);
    output.push_back(r_ack);
    output.push_back(neighbour_source);
    //wait for the radio to be done
    std::cout<<"Sending "<<output.size()<<" bytes "<<endl;
    wait_on_radio();
    return send_data(output);
    
    
    }

int send_rrer(uint8_t recipient_add, uint8_t sender_address, uint8_t N, uint8_t DestCount , uint8_t ttl, std::vector<uint8_t> u_dest, std::vector<uint8_t> u_dest_seq)
{
//        0                   1                   2                   3
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
//
//   The format of the Route Error message is illustrated above, and
//   contains the following fields:
//
//      Type        3
//
//      N           No delete flag; set when a node has performed a local
//                  repair of a link, and upstream nodes should not delete
//                  the route.
//
//      Reserved    Sent as 0; ignored on reception.
//
//      DestCount   The number of unreachable destinations included in the
//                  message; MUST be at least 1.
//
//      Unreachable Destination IP Address
//                  The IP address of the destination that has become
//                  unreachable due to a link break.
//
//      Unreachable Destination Sequence Number
//                  The sequence number in the route table entry for
//                  the destination listed in the previous Unreachable
//                  Destination IP Address field.
    std::vector<uint8_t> output;
    uint8_t type = 3;
    //INsert the data into the packet
    output.push_back(type);
    output.push_back(recipient_add);
    output.push_back(sender_address);
    output.push_back(N);
    output.push_back(DestCount);
    output.push_back(ttl);
    for (int i =0;i<DestCount;i++)
    {
     //PUshing in all the destinations
     output.push_back(u_dest.at(i));
     output.push_back(u_dest_seq.at(i));   
        }
    //wait for the radio to be done
    wait_on_radio();
    return send_data(output);
    }    
    
int send_ack(uint8_t recipient_address, uint8_t sender_address, uint8_t ttl)
{
//        0                   1
//    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//   |     Type      |   Reserved    |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//
//      Type        4
//
//      Reserved    Sent as 0; ignored on reception.
    std::vector<uint8_t> output;
    uint8_t type = 4;
    //INsert the data into the packet
    output.push_back(type);
    output.push_back(recipient_address);
    output.push_back(sender_address);
    output.push_back(ttl);
    //wait for the radio to be done
    wait_on_radio();
    return send_data(output);
    }  
    
int send_hallo(uint8_t recipient_add, uint8_t sender_address, uint8_t source_add, uint8_t destination_add, uint8_t prefix_size, uint8_t hop_count, uint8_t lifetime, uint8_t dest_seq_num, uint8_t m_ttl, uint8_t r_ack)
{
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
//   |                    TTL                      |
//   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//THE FOLLOWING MODIFICATION IS IN HALLO TYPING IS NOW 5 AND:
//      Destination IP Address         The node's IP address.
//
//      Destination Sequence Number    The node's latest sequence number.
//
//      Hop Count                      0
//
//      Lifetime                       ALLOWED_HELLO_LOSS * HELLO_INTERVAL

    std::vector<uint8_t> output;
    uint8_t type = 5;
    //INsert the data into the packet
    output.push_back(type);
    output.push_back(recipient_add);
    output.push_back(sender_address);
    output.push_back(0);
    output.push_back(0);
    output.push_back(lifetime);
    output.push_back(destination_add);
    output.push_back(dest_seq_num);
    output.push_back(source_add);
    output.push_back(m_ttl);
    output.push_back(r_ack);
    //wait for the radio to be done
    wait_on_radio();
    return send_data(output);
    
    }
    
    

int send_message_data(uint8_t recipient_address, uint8_t sender_address,uint8_t origin, uint8_t dest,uint8_t ttl, std::vector<uint8_t> packet)
{
    ///////////////////////////////////////////////////////////
    //recipient_address-> intended recipient of forwarded message
    //sender_address-> address of the node the message was sent
    //origin-> origin destination of the original forwarded message 
    //dest-> address of intended destination of packet
    //ttl-> ttl number to be set
    //packet-> the data to be forwarded
    /////////////////////////////////////////////////////////
    uint8_t type = 6;
    packet.at(MESSAGE_PACKET_TTL) = ttl;
    packet.at(MESSAGE_PACKET_DESTINATION) = dest;
    packet.at(MESSAGE_PACKET_ORIGIN) = origin;
    packet.at(MESSAGE_PACKET_SENDER) = sender_address;
    packet.at(MESSAGE_PACKET_RECIPIENT) = recipient_address;
    packet.at(MESSAGE_PACKET_TYPE) = type;
    //wait for the radio to be done
    wait_on_radio();
    return send_data(packet);
}

///////////////////////////////////////////////////
////TIMERS COME HERE/////////////////////////////

void RreqRateLimitTimerExpire()
{
    // logTrace("RREQ RATE RESET");
    m_rreqCount = 0;
    }

void RrerRateLimitTimerExpire()
{
    // logTrace("RRER RATE RESET");
    m_rerrCount = 0;
}

void Queue_Hallo_Timer_Expire()
{
    main_queue.call(Hallo_Timer_Expire);
    }

void Hallo_Timer_Expire()
{   
    logInfo ("Sending Hallo");
    clock_t offset = clock();
    std::vector<uint8_t> delete_list; //stores dst to be removed
    for (std::map<uint8_t, clock_t>::const_iterator i = m_hallo_tracker.begin (); i!= m_hallo_tracker.end ();i++ )
    {
        if (i->second <offset-HELLO_INTERVAL*CLOCKS_PER_SEC/1000)
        {
            //That means I haven't recently obtained a response from the destination
            if (m_hallo_retry.empty())
            {
                //This means it will be the first entry
                m_hallo_retry.insert(std::make_pair (i->first, 1));
                }//if
            else
            {
                //it is not empty so we need to find if it is in 
                auto element=m_hallo_retry.find(i->first);
                if (element->first==i->first)
                {
                    //find returns end() if not found. So then element differs
                    //check if what was found is the same thejn update else add to map
                    if(element->second>ALLOWED_HELLO_LOSS)
                    {
                        //drops exceed the limit thus link error
                        //Also remove it from both lists
                        delete_list.push_back(element->first);
                        logInfo("Link Broke Sending RRER TODO give more info");
                        SendRerrWhenBreaksLinkToNextHop(element->first);
                        }
                    else
                    {
                        //update element
                        element->second+=1;
                        }
                }
                else
                {
                    //it is not actually in yet so insert it
                    m_hallo_retry.insert(std::make_pair (i->first, 1));
                    }
                
                }//else
            
            }//if
            else
            {
                //here we check if there was retries and then set them to 0
                if (!m_hallo_retry.empty())
                {
                    //only care if any element
                    auto element=m_hallo_retry.find(i->first);
                    if (element->first==i->first)
                    {
                        //exhisted so update to 0
                        element->second = 0;
                        }
                    }
                
                }
                
        }//for
        
        //broad cast hallos
        //FOr now test the RREQ
        for (std::vector<uint8_t>::const_iterator i = delete_list.begin (); i != delete_list.end (); ++i)
        {
                m_hallo_retry.erase(*i);
                m_hallo_tracker.erase(*i);
                std::cout<<"Deleting expired neighbour "<<*i<<endl;
        }    
        wait_on_radio();
        SendHallo();
    }

    void QueueRouteRequestTimerExpire()
    {
        main_queue.call(RouteRequestTimerExpire);
    }
    void RouteRequestTimerExpire ()
    {
        //REMEMBER RESENDRREQ IS TRIGGERED IN SEND_RREQ SO NO NEED TO DOUBLE CALL IT
        logInfo("In RouteRequestTimerExpire()");
        ///TESTING
         std::vector<RouteEntity> route_list;
        RoutingTableEntry toDst = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
        if(!m_routing_table.LookupRoute (destination_ip_address, toDst))
        {
            std::cout<<"Not in the table"<<endl;
        }
        else {
            m_routing_table.Print();
        }
        ///
        std::vector<uint8_t> delete_list; //stores dst to be removed
        clock_t offset = clock();
        for (std::map<uint8_t, clock_t>::const_iterator i = m_addressReqTimer.begin (); i!= m_addressReqTimer.end ();i++ )
        {
            //Goes through every destination that the RREQ has been schedule for
            if (i->second <offset) {
            //Here it checks if the time when the RREQ should go off has been met
            if (m_rreq_retry.empty())
            {
                //This means it will be the first retry
                m_rreq_retry.insert(std::make_pair (i->first, 1));
                //Update new time done in void ScheduleRreqRetry(uint8_t dst)
                send_rreq(i->first); //First resend the RREQ
                }//if
            else
            {
                //it is not empty so we need to find if it is in 
                auto element=m_rreq_retry.find(i->first);
                if (element->first==i->first)
                {
                    //find returns end() if not found. So then element differs
                    //check if what was found is the same then update else add to map
                    if(element->second>RREQ_RETRIES)
                    {
                        //drops exceed the limit thus link error
                        //Also remove it from both lists
                        std::cout<<"The route to destination "<<element->first<<" could not be found "<<endl;
                        ScheduleRreqRetry(element->first);
                        delete_list.push_back(element->first);
                        }
                    else
                    {
                        //update element
                        element->second+=1;
                        // Set new time based on exponential is done in void ScheduleRreqRetry(uint8_t dst)
                        send_rreq(element->first); //First resend the RREQ
                        }
                }
                else
                {
                    //it is not actually in yet so insert it
                    m_rreq_retry.insert(std::make_pair (i->first, 1));
                    //Update new time is done in void ScheduleRreqRetry(uint8_t dst)
                    send_rreq(element->first); //First resend the RREQ
                    }
                
                }//else
            
            }//if
            else
            {
             //If route is found I will remove it from list??   
                }
        }
                for (std::vector<uint8_t>::const_iterator i = delete_list.begin (); i != delete_list.end (); ++i)
        {
                std::cout<<"RREQ for destination "<<*i<<" being dropped line 1782"<<endl;
                m_addressReqTimer.erase(*i);//Deleting all entries after visited
                m_rreq_retry.erase(*i);
                //All packets from message queue should be removed
                message_request_queue.DropPacketWithDst(*i);
                std::cout<<"Deleting route entry for "<<*i<<" being dropped line 1869"<<endl;
                m_routing_table.DeleteRoute(*i);
        }
    }


    void ScheduleRreqRetry(uint8_t dst)
    {
        std::vector<RouteEntity> route_list;
        RoutingTableEntry rt = RoutingTableEntry(destination_ip_address,m_sequence,0,route_list,MY_ROUTE_TIMEOUT*CLOCKS_PER_SEC/1000,device_ip_address);
        m_routing_table.LookupRoute (dst, rt);
        clock_t retry;
        if (rt.GetHop () < NET_DIAMETER)
            {
            retry = 2 * NODE_TRAVERSAL_TIME * (rt.GetHop () + TIMEOUT_BUFFER) * CLOCKS_PER_SEC/1000 +clock();
            }
        else
            {
            uint16_t backoffFactor = rt.GetRreqCnt () - 1;
            std::cout<<"Applying binary exponential backoff factor "<<backoffFactor<<endl;
            retry = NODE_TRAVERSAL_TIME * (1 << backoffFactor) * CLOCKS_PER_SEC/1000 + clock();
            }

        logInfo("In ScheduleRreqRetry(uint8_t dst)");
        //First check if this has been added before
        if (m_addressReqTimer.empty())
        {
             m_addressReqTimer.insert(std::make_pair (dst, retry));
        }
        else {
        auto element=m_addressReqTimer.find(dst);
        if (element->first == dst)
        {
            //destination has been found update the scheduling now
            auto r_retry=m_rreq_retry.find(dst); //find the retires on this RREQ
            if (r_retry->second>RREQ_RETRIES)
            {
                //Remove this 
                std::cout<<"Erasing RREQ for destination "<<dst<<endl;
            }
            else {
                element->second = retry;
            }
        }
        else {
            //destination not been found add it to the queue
            m_addressReqTimer.insert(std::make_pair (dst, retry));

        }
        }

    }
#endif