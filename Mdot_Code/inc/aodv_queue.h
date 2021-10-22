 #ifndef AODV_QUEUE_H
 #define AODV_QUEUE_H
 #include <vector>
#include <chrono>
#include <time.h>
#include <algorithm>
#include <functional>
 #include "mbed.h"
#include "mDot.h"
#include "MTSLog.h"
#include "MTSText.h"
#include "network_config.h"

//For timing I am using clock cycles (Yep but can't get timer to work for needs case)
//Anyway the program runs at 100MHz thus one clock is 10^-8 seconds

class QueueEntry
{
private:
    std::vector<uint8_t> m_packet;
    clock_t time_entered_queue;
    clock_t expire_time;
public:
    QueueEntry (std::vector<uint8_t> packet, clock_t exp)
         : m_packet (packet),
       time_entered_queue (clock()),
       expire_time (clock()+exp)
    {
//        m_packet = packet;
//        time_entered_queue = clock();
//        expire_time = time_entered_queue + exp;
    }

    bool operator== (QueueEntry const & o) const
    {
        return ((m_packet == o.m_packet) && (expire_time == o.expire_time));
    }

    std::vector<uint8_t> GetPacket () const
    {
        return m_packet;
    }
    void SetPacket (std::vector<uint8_t> p)
    {
        m_packet = p;
    }
    void SetExpireTime (clock_t exp)
    {
        time_entered_queue = clock();
        expire_time = time_entered_queue + exp;
    }
    clock_t GetTimeTillExpire() const
    {
        return expire_time - clock();
    }
    clock_t GetExpireTime () const
    {
        return expire_time;
    }
};


class RequestQueue
{
private:

    void Purge ();
    void Drop (QueueEntry en, std::string reason);
    uint32_t m_maxLen;
    clock_t m_queueTimeout;

public:
    std::vector<QueueEntry> m_queue;
    RequestQueue (uint32_t maxLen, clock_t routeToQueueTimeout);
    bool Enqueue (QueueEntry & entry);
    bool Dequeue (uint8_t dst, QueueEntry & entry);
    bool DequeueFront (QueueEntry & entry);
    void DropPacketWithDst (uint8_t dst);
    bool Find (uint8_t dst);
    uint32_t GetSize ();

    // Fields
    uint32_t GetMaxQueueLen () const
    {
        return m_maxLen;
    }
    void SetMaxQueueLen (uint32_t len)
    {
        m_maxLen = len;
    }
    clock_t GetQueueTimeout () const
    {
        return m_queueTimeout;
    }
    void SetQueueTimeout (clock_t t)
    {
        m_queueTimeout = t+clock();
    }

};
  
  
  
 #endif /* AODV_RQUEUE_H */
