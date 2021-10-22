#include "aodv_table.h"

#include <iostream>

#if ACTIVE_VERSION == AODV
  RouteEntity::RouteEntity(uint8_t next, uint8_t hop) {

     next_hop = next;
     hopcount = hop;

}

RouteEntity::~RouteEntity() {

}

uint8_t RouteEntity::get_next_hop() const {
    return next_hop;
}

uint8_t RouteEntity::get_hopcount() {
    return hopcount;
}

void RouteEntity::set_next_hop(uint8_t next) {
next_hop = next;
}

void RouteEntity::set_hopcount(uint8_t hop) {
hopcount = hop;
}

RouteFlags RouteEntity::get_status() const {
    return status;
}

void RouteEntity::set_status(RouteFlags sts) {
status = sts;
}



//bool m_validSeqNo;
//uint8_t m_seqNo;
//uint8_t m_advertised_hopcount;
//clock_t m_lifeTime;
//uint8_t m_destination;
//RouteFlags m_flag;
//clock_t m_routeRequestTimout;
//std::vector<RouteEntity> m_route_list;
//std::vector<uint8_t> m_precursorList;
//uint8_t m_reqCount;

//TODO add m_route_list handlers
RoutingTableEntry::RoutingTableEntry(uint8_t dst, uint8_t seqNo, uint8_t advertised_hopcount,
                                     std::vector<RouteEntity> route_list, clock_t expiration_timeout, uint8_t src) {
//    m_destination = dst;
    m_seqNo = seqNo;
    m_advertised_hopcount = advertised_hopcount;
    m_route_list = route_list;
    m_lifeTime = expiration_timeout + clock();
    m_flag = VALID;
    m_reqCount = 0;
    m_LoRa_route = LoRaRoute();
    m_LoRa_route.SetDestination(dst);
    m_LoRa_route.SetSource(src);
    m_validSeqNo = false;
}

RoutingTableEntry::~RoutingTableEntry() {

}

bool RoutingTableEntry::InsertPrecursor(uint8_t id) {
    if (!LookupPrecursor (id))
    {
        m_precursorList.push_back (id);
        return true;
    }
    else
    {
        return false;
    }
}

bool RoutingTableEntry::LookupPrecursor(uint8_t id) {
    for (std::vector<uint8_t>::const_iterator i = m_precursorList.begin (); i!= m_precursorList.end (); ++i)
    {
        if (*i == id)
        {
//            logInfo ("Precursor " << id << " found");
            std::cout << "Precursor" << id << " found"<< std::endl;
            return true;
        }
    }
//    logInfo ("Precursor " << id << " not found");
    std::cout << "Precursor" << id << " not found"<< std::endl;
    return false;
}

bool RoutingTableEntry::DeletePrecursor(uint8_t id) {
    std::vector<uint8_t>::iterator i = std::remove (m_precursorList.begin (),
                                                    m_precursorList.end (), id);
    if (i == m_precursorList.end ())
    {
//        logInfo ("Precursor " << id << " not found");
        std::cout << "Precursor" << id << " not found"<< std::endl;
        return false;
    }
    else
    {
//        logInfo ("Precursor " << id << " found");
        std::cout << "Precursor" << id << " found"<< std::endl;
        m_precursorList.erase (i, m_precursorList.end ());
    }
    return true;
}

void RoutingTableEntry::DeleteAllPrecursors() {
//    logInfo ("Clearing all precursors");
    std::cout << "Clearing all Precursor"<< std::endl;
    m_precursorList.clear ();
}

bool RoutingTableEntry::IsPrecursorListEmpty() const {
    return m_precursorList.empty ();
}

//Inserts precursors in output parameter prec if they do not yet exist in vector.
void RoutingTableEntry::GetPrecursors(std::vector<uint8_t> prec) const {
    if (IsPrecursorListEmpty ())
    {
        return;
    }
    for (std::vector<uint8_t>::const_iterator i = m_precursorList.begin (); i
                                                                            != m_precursorList.end (); ++i)
    {
        bool result = true;
        for (std::vector<uint8_t>::const_iterator j = prec.begin (); j
                                                                     != prec.end (); ++j)
        {
            if (*j == *i)
            {
                result = false;
            }
        }
        if (result)
        {
            prec.push_back (*i);
        }
    }
}

void RoutingTableEntry::Invalidate(clock_t badLinkLifetime , uint8_t index) {
    if (m_route_list.at(index).get_status() == INVALID)
    {
        return;
    }
    m_route_list.at(index).set_status(INVALID);
    m_reqCount = 0;
    m_lifeTime = badLinkLifetime + clock();
}

void RoutingTableEntry::Print() const {
    std::cout << "TODO PRINT ROUTING ENTRY INFO"<< std::endl;
}

void RoutingTableEntry::Invalidate(clock_t badLinkLifetime) {
    if (m_flag == INVALID)
    {
        return;
    }
    m_flag = INVALID;
    m_reqCount = 0;
    m_lifeTime = badLinkLifetime + clock();
}

RoutingTable::RoutingTable(clock_t t) {
m_badLinkLifetime = t;
}

bool RoutingTable::AddRoute(RoutingTableEntry &r , uint8_t index) {
    std::cout << "Adding a route " << std::endl;
    Purge ();
    if (r.GetFlag () != IN_SEARCH)
    {
        r.SetRreqCnt (0);
    }
    std::pair<std::map<uint8_t, RoutingTableEntry>::iterator, bool> result =
            m_LoRaAddressEntry.insert (std::make_pair (r.GetDestination (), r));
    return result.second;
}

bool RoutingTable::DeleteRoute(uint8_t dst) {
    std::cout << "Deleting route " << dst <<" from index "<< std::endl;
    Purge ();
    if (m_LoRaAddressEntry.erase (dst) != 0)
    {
        std::cout << "Success delete " << dst <<" from index "<<std::endl;
        return true;
    }
    std::cout << "Fail Delete " << dst <<" from index "<< std::endl;
    return false;
}

bool RoutingTable::DeleteRouteIndex(uint8_t dst, uint8_t index) {
    std::cout << "Deleting route " << dst <<" from index "<<index<< std::endl;
    Purge ();
    if (m_LoRaAddressEntry.at(dst).removeRouteEntity(index) != 0)
    {
        std::cout << "Success delete " << dst <<" from index "<<index<< std::endl;
        return true;
    }
    std::cout << "Fail Delete " << dst <<" from index "<<index<< std::endl;
    return false;
}

bool RoutingTable::LookupRoute(uint8_t dst, RoutingTableEntry &rt) {
    Purge ();
    if (m_LoRaAddressEntry.empty ())
    {
        std::cout<<"Route to " << dst << " not found; m_LoRaAddressEntry is empty"<<std::endl;
        return false;
    }
    std::map<uint8_t, RoutingTableEntry>::const_iterator i =
            m_LoRaAddressEntry.find (dst);
    if (i == m_LoRaAddressEntry.end ())
    {
        std::cout<<"Route to " << dst << " not found"<<std::endl;
        return false;
    }
    rt = i->second;
    std::cout<<"Route to " << dst << " found"<<std::endl;
    return true;
}

bool RoutingTable::LookupValidRoute(uint8_t id, RoutingTableEntry &rt) {
    if (!LookupRoute (id, rt))
    {
        std::cout<<"Route to " << id << " not found"<<std::endl;
        return false;
    }
    return (rt.GetFlag () == VALID);
}

bool RoutingTable::Update(RoutingTableEntry &rt) {
    std::map<uint8_t, RoutingTableEntry>::iterator i =
            m_LoRaAddressEntry.find (rt.GetDestination ());
    if (i == m_LoRaAddressEntry.end ())
    {
//        NS_LOG_LOGIC ("Route update to " << rt.GetDestination () << " fails; not found");
        return false;
    }
    i->second = rt;
    if (i->second.GetFlag () != IN_SEARCH)
    {
//        NS_LOG_LOGIC ("Route update to " << rt.GetDestination () << " set RreqCnt to 0");
        i->second.SetRreqCnt (0);
    }
    return true;
}

bool RoutingTable::SetEntryState(uint8_t dst, RouteFlags state) {
    std::map<uint8_t, RoutingTableEntry>::iterator i =
            m_LoRaAddressEntry.find (dst);
    if (i == m_LoRaAddressEntry.end ())
    {
        return false;
    }
    i->second.SetFlag (state);
    i->second.SetRreqCnt (0);
    return true;
}

void RoutingTable::GetListOfDestinationWithNextHop(uint8_t nextHop, std::map<uint8_t , uint32_t> & unreachable) {
    Purge ();
    unreachable.clear ();
    for (std::map<uint8_t, RoutingTableEntry>::const_iterator i =
            m_LoRaAddressEntry.begin (); i != m_LoRaAddressEntry.end (); ++i)
    {
        for (int j = 0; j<i->second.getRouteList().size();j++)
        if (i->second.GetNextHop (j) == nextHop)
        {
            unreachable.insert (std::make_pair (i->first, i->second.GetSeqNo ()));
        }
    }
}

void RoutingTable::Purge() {
    if (m_LoRaAddressEntry.empty ())
    {
        return;
    }
    for (std::map<uint8_t , RoutingTableEntry>::iterator i =
            m_LoRaAddressEntry.begin (); i != m_LoRaAddressEntry.end (); )
    {
        //SHould it be <=0 or <0 also is int how clock is represented
        if (i->second.GetLifeTime () <clock())
        {
            if (i->second.GetFlag () == INVALID)
            {
                std::map<uint8_t, RoutingTableEntry>::iterator tmp = i;
                ++i;
                m_LoRaAddressEntry.erase (tmp);
            }
            else if (i->second.GetFlag () == VALID)
            {
                i->second.Invalidate (m_badLinkLifetime);
                ++i;
            }
            else
            {
                ++i;
            }
        }
        else
        {
            ++i;
        }
    }
}

void RoutingTable::InvalidateRoutesWithDst(const std::map<uint8_t, uint32_t> &unreachable) {
    Purge ();
    for (std::map<uint8_t, RoutingTableEntry>::iterator i =
            m_LoRaAddressEntry.begin (); i != m_LoRaAddressEntry.end (); ++i)
    {
        for (std::map<uint8_t, uint32_t>::const_iterator j =
                unreachable.begin (); j != unreachable.end (); ++j)
        {
            if ((i->first == j->first) && (i->second.GetFlag () == VALID))
            {
                i->second.Invalidate (m_badLinkLifetime);
            }
        }
    }
}

void RoutingTable::Print()  {
    Purge ();
    std::cout<<"----ROUTING TABLE HAS THE CONTENTS------"<<endl;
        for (std::map<uint8_t, RoutingTableEntry>::const_iterator i =
            m_LoRaAddressEntry.begin (); i != m_LoRaAddressEntry.end (); ++i)
    {
        if (i->second.GetFlag()==VALID)
        {
            std::cout<<"Destination :"<<i->first<<" has a VALID path"<<endl;
        }
        else  if (i->second.GetFlag()==IN_SEARCH)
        {
            std::cout<<"Destination :"<<i->first<<" has a IN_SEARCH path"<<endl;
        }
        else {
        std::cout<<"Destination :"<<i->first<<" has a INVALID path"<<endl;
        }
        //TODO print all paths in entry
        std::cout<<"Next hop: "<<i->second.GetNextHop(0)<<endl;
        std::cout<<"Hop Count: "<<i->second.GetHop()<<endl;
        std::cout<<"Sequence number: "<<i->second.GetSeqNo()<<endl;

    }
    
}

void RoutingTable::Purge(std::map<uint8_t, RoutingTableEntry> &table) const {
    if (table.empty ())
    {
        return;
    }
    for (std::map<uint8_t, RoutingTableEntry>::iterator i =
            table.begin (); i != table.end (); )
    {
        if (i->second.GetLifeTime () < clock())
        {
            if (i->second.GetFlag () == INVALID)
            {
                std::map<uint8_t, RoutingTableEntry>::iterator tmp = i;
                ++i;
                table.erase (tmp);
            }
            else if (i->second.GetFlag () == VALID)
            {

                i->second.Invalidate (m_badLinkLifetime);
                ++i;
            }
            else
            {
                ++i;
            }
        }
        else
        {
            ++i;
        }
    }
}

#endif
  
 