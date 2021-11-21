#ifndef AODV_TABLE_H
#define AODV_TABLE_H

#include <stdint.h>
#include <cassert>
#include <map>
#include <chrono>
#include <time.h>
#include <vector>
#include <algorithm>
#include <iomanip>
#include <iostream>
#include "lora_route.h"
 #include "mbed.h"
#include "mDot.h"
#include "MTSLog.h"
#include "MTSText.h"
#include "network_config.h"

#if ACTIVE_VERSION == AODV 
enum RouteFlags
{
    VALID = 0,
    INVALID = 1,
    IN_SEARCH = 2,
};
//This is used to store the multi channel routing parameters
class RouteEntity
{
public:
    RouteEntity(uint8_t next, uint8_t hop);
    ~RouteEntity();

    uint8_t get_next_hop() const;
    uint8_t get_hopcount();
    RouteFlags get_status() const;

    void set_next_hop(uint8_t next);
    void set_hopcount(uint8_t  hop);
    void set_status (RouteFlags sts);

private:

    uint8_t next_hop;
    uint8_t hopcount;
    RouteFlags status;

};

//HERE is the actual entry container
class RoutingTableEntry
{

private:
    bool m_validSeqNo;
    uint8_t m_seqNo;
    uint8_t m_advertised_hopcount;
    clock_t m_lifeTime;
//    uint8_t m_destination;
    RouteFlags m_flag;
    clock_t m_routeRequestTimout;
    std::vector<RouteEntity> m_route_list;
    std::vector<uint8_t> m_precursorList;
    uint8_t m_reqCount;
    LoRaRoute m_LoRa_route; //defines current selected route

public:
     RoutingTableEntry (uint8_t dst, uint8_t seqNo , uint8_t advertised_hopcount , std::vector<RouteEntity> route_list, clock_t expiration_timeout ,uint8_t src);

    ~RoutingTableEntry ();

    //\{
    bool InsertPrecursor (uint8_t id);
    bool LookupPrecursor (uint8_t id);
    bool DeletePrecursor (uint8_t id);
    void DeleteAllPrecursors ();
    bool IsPrecursorListEmpty () const;
    void GetPrecursors (std::vector<uint8_t> prec) const;
    //\}

    void setRouteList(std::vector<RouteEntity> route_list)
    {
        m_route_list = route_list;
    }

    std::vector<RouteEntity> getRouteList() const {
        return m_route_list;
    }

    void addRoutingEntity (RouteEntity add)
    {
        m_route_list.push_back(add);
    }

    RouteEntity getRouteEntity(uint8_t index)
    {
        return m_route_list.at(index);
    }

    bool removeRouteEntity(uint8_t index)
    {
        if (index<m_route_list.size())
        {
            m_route_list.erase(m_route_list.begin()+index);
            return true;
        }
        else
        {
            return false;
        }
    }
    
    // Fields
    uint8_t GetDestination () const
    {
        return m_LoRa_route.GetDestination();
    }

    void SetDestination(uint8_t dest)
    {
        m_LoRa_route.SetDestination(dest);
    }

    LoRaRoute GetRoute () const
   {
     return m_LoRa_route;
   }
   void SetRoute (LoRaRoute r)
   {
       m_LoRa_route = r;
   }

    void SetRreqCnt (uint8_t n)
    {
        m_reqCount = n;
    }

    uint8_t GetRreqCnt () const
    {
        return m_reqCount;
    }
    
    void IncrementRreqCnt(void)
    {
        m_reqCount++;
        }
    

    void SetNextHop (uint8_t nextHop)
    {
        RouteEntity holder = RouteEntity( nextHop,  1);
        if (m_route_list.size()>0)
        {
         for (int i = 0; i<m_route_list.size(); i++)
         {
            if( m_route_list.at(i).get_next_hop()==nextHop)
            {
                return;
                }
            
            }   
            m_route_list.push_back(holder);
            }
            else
            {
                m_route_list.push_back(holder);
                }
        //Assuming made here it is new hop look at smallest hop best
        m_LoRa_route.SetNextHop(m_route_list.front().get_next_hop());
        for (int i = 1; i<m_route_list.size(); i++)
         {
          if  (m_LoRa_route.GetNextHop()>m_route_list.at(i).get_next_hop())
          {
            //This is smaller so make this next hop
            m_LoRa_route.SetNextHop(m_route_list.at(i).get_next_hop());
            }
        }  
    }

    uint8_t GetNextHop (uint8_t index) const
    {
        if (m_route_list.size()>index)
        {
         return  m_route_list.at(index).get_next_hop();   
            }
        return 0;
        
    }

    void SetValidSeqNo (bool s)
    {
        m_validSeqNo = s;
    }

    bool GetValidSeqNo () const
    {
        return m_validSeqNo;
    }

    void SetSeqNo (uint8_t sn)
    {
        m_seqNo = sn;
    }

    uint8_t GetSeqNo () const
    {
        return m_seqNo;
    }

    void SetHop (uint8_t hop)
    {
        m_advertised_hopcount = hop;
    }
    uint8_t GetHop () const
    {
        return m_advertised_hopcount;
    }

    void SetLifeTime (clock_t lt)
    {
        m_lifeTime = lt + clock();
    }
    clock_t GetLifeTime () const
    {
//        std::cout<<"m_lifetime "<< m_lifeTime <<" clock "<<clock()<<std::endl;
        return m_lifeTime;
    }
    //TODO expand this into multiple routes table
    void SetFlag (RouteFlags flag )
    {
//        m_route_list.at(index).set_status(flag);
m_flag = flag;
    }
    RouteFlags GetFlag () const
    {
//         m_route_list.at(index).get_status();
            return m_flag;
    }
    clock_t m_ackTimer;
    //Print the info I guess??
    void Print () const;

    void Invalidate(clock_t badLinkLifetime, uint8_t index);
    void Invalidate(clock_t badLinkLifetime);
};

class RoutingTable
{

private:
    std::map<uint8_t, RoutingTableEntry> m_LoRaAddressEntry;
    clock_t m_badLinkLifetime;
    void Purge (std::map<uint8_t, RoutingTableEntry> &table) const;

public:
    RoutingTable (clock_t t);
    //\{
    clock_t GetBadLinkLifetime () const
    {
        return m_badLinkLifetime;
    }
    void SetBadLinkLifetime (clock_t t)
    {
        m_badLinkLifetime = t;
    }
    //\}
    bool AddRoute (RoutingTableEntry &r , uint8_t index);
    //Deletes complete entry if dst is unreachable
    bool DeleteRoute(uint8_t dst);
    //Deletes one path if that path doesnt work
    bool DeleteRouteIndex (uint8_t dst, uint8_t index);
    bool LookupRoute (uint8_t dst, RoutingTableEntry & rt);
    bool LookupValidRoute (uint8_t id, RoutingTableEntry & rt);
    bool Update (RoutingTableEntry & rt);
    bool SetEntryState (uint8_t dst, RouteFlags state);
    void GetListOfDestinationWithNextHop (uint8_t nextHop, std::map<uint8_t, uint32_t> & unreachable);
    void InvalidateRoutesWithDst (std::map<uint8_t, uint32_t> const & unreachable);
    //void InvalidateRoutesWithDst (uint8_t dest);
//   void DeleteAllRoutesFromInterface (Ipv4InterfaceAddress iface);
    void Clear ()
    {
        m_LoRaAddressEntry.clear ();
    }
    void Purge ();
//   bool MarkLinkAsUnidirectional (Ipv4Address neighbor, clock_t blacklistTimeout);
//TODO ADD PRINT FUNCTIONALITY
    void Print () ;


};

#endif
#endif //ALGORITHMS_AODV_TABLE_H
  

  






///////////////////////////////////
//USELESS CODE??????
//   void SetRreqCnt (uint8_t n)
//   {
//     m_reqCount = n;
//   }
//   uint8_t GetRreqCnt () const
//   {
//     return m_reqCount;
//   }
//   void IncrementRreqCnt ()
//   {
//     m_reqCount++;
//   }
//   void SetUnidirectional (bool u)
//   {
//     m_blackListState = u;
//   }
//   bool IsUnidirectional () const
//   {
//     return m_blackListState;
//   }
//   void SetBlacklistTimeout (Time t)
//   {
//     m_blackListTimeout = t;
//   }
//   Time GetBlacklistTimeout () const
//   {
//     return m_blackListTimeout;
//   }
//      bool operator== (Ipv4Address const  dst) const
//   {
//     return (m_ipv4Route->GetDestination () == dst);
//   }
