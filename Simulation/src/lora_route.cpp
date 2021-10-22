#include "lora_route.h"

LoRaRoute::LoRaRoute() {

}

void LoRaRoute::SetDestination(uint8_t dest) {
    std::cout << "Destination for route set " << dest << std::endl;
m_dest = dest;
}

uint8_t LoRaRoute::GetDestination() const {
    return m_dest;
}

void LoRaRoute::SetSource(uint8_t src) {
    std::cout << "Source for route set " << src << std::endl;
    m_source = src;
}

uint8_t LoRaRoute::GetSource(void)  {
    return m_source;
}

void LoRaRoute::SetNextHop(uint8_t gw) {
    std::cout << "Next Hop for route set " << gw << std::endl;
m_nexthop = gw;
}

uint8_t LoRaRoute::GetNextHop(void)  {
    return m_nexthop;
}
