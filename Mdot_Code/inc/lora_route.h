#ifndef LORA_ROUTE_H
#define LORA_ROUTE_H
#include <list>
#include <map>
#include <ostream>
#include <iostream>
 #include "mbed.h"
#include "mDot.h"
#include "MTSLog.h"
#include "MTSText.h"
#include "network_config.h"

class LoRaRoute
{
public:
    LoRaRoute ();

    void SetDestination (uint8_t dest);
    uint8_t GetDestination () const;

    void SetSource (uint8_t src);
    uint8_t GetSource (void) ;
    //next hop address
    void SetNextHop (uint8_t gw);
    uint8_t GetNextHop (void) ;

private:
    uint8_t m_dest;
    uint8_t m_source;
    uint8_t m_nexthop;
};

std::ostream& operator<< (std::ostream& os, LoRaRoute const& route);

#endif //ALGORITHMS_LORA_ROUTE_H