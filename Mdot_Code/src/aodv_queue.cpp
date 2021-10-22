#include "aodv_queue.h"
#include <iostream>
#include <string>
RequestQueue::RequestQueue(uint32_t maxLen, clock_t routeToQueueTimeout)
        : m_maxLen (maxLen),
          m_queueTimeout (routeToQueueTimeout+clock())
{
}
  
uint32_t RequestQueue::GetSize ()
{
    Purge ();
    return m_queue.size ();
}

bool
RequestQueue::Enqueue (QueueEntry & entry)
{
    //Adds packets to the queue
    //First removes all out of data packets
    Purge ();
    //Checks for dublicates
    for (std::vector<QueueEntry>::const_iterator i = m_queue.begin (); i
                                                                       != m_queue.end (); ++i)
    {
        //TODO set up where unique ID will go essentially
        //Compares unique ID, type and destination to see if packets are effectively the same
                switch (i->GetPacket()[0])
                {
                    case ROUTE_REQUEST:
                        //Handle RREQ messages
                if ((i->GetPacket ()[RREQ_PACKET_RREQ_ID] == entry.GetPacket ()[RREQ_PACKET_RREQ_ID])&& (i->GetPacket()[RREQ_PACKET_DESTINATION_IP]== entry.GetPacket()[RREQ_PACKET_DESTINATION_IP]) && (i->GetPacket ()[0] == entry.GetPacket ()[0]))
                        {
                            return false;
                        }
                        break;
                    case ROUTE_REPLY:
                        //Handle RREP messages
                if ((i->GetPacket ()[RREP_PACKET_DESTINATION_IP] == entry.GetPacket ()[RREP_PACKET_DESTINATION_IP])&& (i->GetPacket()[RREP_PACKET_LIFETIME]== entry.GetPacket()[RREP_PACKET_LIFETIME]) && (i->GetPacket ()[0] == entry.GetPacket ()[0]))
                        {
                            return false;
                        }
                        break;
                    case ROUTE_ERROR:
                        //Handle RERR Messages
                if ((i->GetPacket ()[RRER_PACKET_RECIPIENT] == entry.GetPacket ()[RRER_PACKET_RECIPIENT])&& (i->GetPacket()[RRER_PACKET_DESTCOUNT]== entry.GetPacket()[RRER_PACKET_DESTCOUNT]) && (i->GetPacket ()[0] == entry.GetPacket ()[0]))
                        {
                            return false;
                        }
                        break;
                    case ROUTE_REPLY_ACK:
                        //Handle RRER-ACK messages
                if ((i->GetPacket ()[4] == entry.GetPacket ()[4])&& (i->GetPacket()[5]== entry.GetPacket()[5]) && (i->GetPacket ()[0] == entry.GetPacket ()[0]))
                        {
                            return false;
                        }
                        break;
                    case HALLO_MESSAGE:
                if ((i->GetPacket ()[RREP_PACKET_SENDER] == entry.GetPacket ()[RREP_PACKET_SENDER])&& (i->GetPacket()[RREP_PACKET_LIFETIME]== entry.GetPacket()[RREP_PACKET_LIFETIME]) && (i->GetPacket ()[0] == entry.GetPacket ()[0]))
                        {
                            return false;
                        }
                        break;
                    default:
                                    if ((i->GetPacket ()[4] == entry.GetPacket ()[4])&& (i->GetPacket()[5]== entry.GetPacket()[5]) && (i->GetPacket ()[0] == entry.GetPacket ()[0]))
                        {
                            return false;
                        }
                        break;
                }
    }
    //Sets expire time and checks queue size dequeue if too big
    entry.SetExpireTime (m_queueTimeout+entry.GetTimeTillExpire());
    if (m_queue.size () == m_maxLen)
    {
        Drop (m_queue.front (), "Drop the most aged packet"); // Drop the most aged packet
        m_queue.erase (m_queue.begin ());
    }
    //Adds the packet to the queue
    m_queue.push_back (entry);
    // std::cout<<"Pushed back entry with dead time "<<std::to_string(entry.GetExpireTime())<<" current time is"<<std::to_string(entry.GetExpireTime())<<endl;
    // std::cout<<"m_queueTimeout is "<<std::to_string(m_queueTimeout)<<endl;
    return true;
}

void
RequestQueue::DropPacketWithDst (uint8_t dst)
{
    //Drops all packets with a certain destination
//    logInfo("Dropping packet");
    Purge ();
    for (std::vector<QueueEntry>::iterator i = m_queue.begin (); i
                                                                 != m_queue.end (); ++i)
    {
        if (i->GetPacket()[MESSAGE_PACKET_DESTINATION] == dst)
        {
           Drop (*i, "DropPacketWithDst ");
        }
    }
    auto new_end = std::remove_if (m_queue.begin (), m_queue.end (),
                                   [&](const QueueEntry& en) { return en.GetPacket()[2] == dst; });
    m_queue.erase (new_end, m_queue.end ());
}

bool RequestQueue::Dequeue (uint8_t dst, QueueEntry & entry)
{
    Purge ();
    for (std::vector<QueueEntry>::iterator i = m_queue.begin (); i != m_queue.end (); ++i)
    {
        if (i->GetPacket()[MESSAGE_PACKET_DESTINATION] == dst)
        {
            entry = *i;
            m_queue.erase (i);
            return true;
        }
    }
    return false;
}

bool RequestQueue::DequeueFront (QueueEntry & entry)
{
    Purge ();
    if (m_queue.size () ==0)
    {
        return false;
        }
    else
    {
     std::vector<QueueEntry>::iterator i = m_queue.begin ();
     entry = *i;
     m_queue.erase (i);
     return true;   
        }
    
    }


bool
RequestQueue::Find (uint8_t dst)
{
    for (std::vector<QueueEntry>::const_iterator i = m_queue.begin (); i
                                                                       != m_queue.end (); ++i)
    {
        if (i->GetPacket()[MESSAGE_PACKET_DESTINATION] == dst)
        {
            return true;
        }
    }
    return false;
}

struct IsExpired
{
    bool
    operator() (QueueEntry const & e) const
    {
        return (e.GetExpireTime () < clock());
    }
};

void
RequestQueue::Purge ()
{
    IsExpired pred;
    for (std::vector<QueueEntry>::iterator i = m_queue.begin (); i
                                                                 != m_queue.end (); ++i)
    {
        if (pred (*i))
        {
            Drop (*i, "Drop outdated packet");
        }
    }
    m_queue.erase (std::remove_if (m_queue.begin (), m_queue.end (), pred),
                   m_queue.end ());
}

void
// TODO PLEASE MAKE THIS PRINT ACTUAL DROP INFO
//RequestQueue::Drop (QueueEntry en, std::string reason)
RequestQueue::Drop (QueueEntry en, std::string reason)
{
    std::cout<<"Dropped packet to "<<en.GetPacket().at(MESSAGE_PACKET_DESTINATION)<<": "<<reason<<endl;
    std::cout<<"Packet dies at "<<std::to_string(en.GetExpireTime())<<" the current time is "<<std::to_string(clock())<<endl;
    std::cout<<" Time to expire "<<std::to_string(en.GetTimeTillExpire())<<endl;

    return;
}

