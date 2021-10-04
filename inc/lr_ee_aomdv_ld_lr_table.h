#ifndef AOMDV_LD_LR_TABLE_H
#define AOMDV_LD_LR_TABLE_H

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

#if ACTIVE_VERSION == LR_EE_AOMDV_LD_LR
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
    RouteEntity(uint8_t next, uint8_t hop, uint8_t n_s, uint32_t cetx, uint32_t cete, uint32_t mre);
    ~RouteEntity();

    uint8_t get_next_hop() const;
    uint8_t get_hopcount();
    uint8_t get_neighbour_source() const;
    uint32_t get_cetx() const;
    uint32_t get_cete() const;
    uint32_t get_mre() const;
    RouteFlags get_status() const;

    void set_next_hop(uint8_t next);
    void set_hopcount(uint8_t  hop);
    void set_neighbour_source(uint8_t n_s);
    void set_cetx(uint32_t cetx);
    void set_cete(uint32_t cete);
    void set_mre(uint32_t mre);
    void set_status (RouteFlags sts);

        //\{
    bool InsertPrecursor (uint8_t id);
    bool LookupPrecursor (uint8_t id);
    bool DeletePrecursor (uint8_t id);
    void DeleteAllPrecursors ();
    bool IsPrecursorListEmpty () const;
    void GetPrecursors (std::vector<uint8_t> prec) const;
    //\}

private:

    uint8_t next_hop;
    uint8_t hopcount;
    uint8_t neighbour_source;
    uint32_t m_cetx;
    uint32_t m_cete;
    uint32_t m_mre;
    RouteFlags status;
    std::vector<uint8_t> m_precursorList;

};

//HERE is the actual entry container
class RoutingTableEntry
{

private:
    bool m_validSeqNo;
    uint8_t m_seqNo;
    uint8_t m_advertised_hopcount;
    uint32_t m_advertised_cetx;
    uint32_t m_advertised_cete;
    uint32_t m_advertised_mre;
    clock_t m_lifeTime;
//    uint8_t m_destination;
    RouteFlags m_flag;
    clock_t m_routeRequestTimout;
    std::vector<RouteEntity> m_route_list;
    uint8_t m_reqCount;
    LoRaRoute m_LoRa_route; //defines current selected route

public:
     RoutingTableEntry (uint8_t dst, uint8_t seqNo , uint8_t advertised_hopcount , std::vector<RouteEntity> route_list, clock_t expiration_timeout ,uint8_t src);

    ~RoutingTableEntry ();


    /////////////////////////////////////////////////////////
    ///AOVDM SPECIFIC FUNCTIONS ///////////////////////////
    ///////////////////////////////////////////////////////
    std::vector<RouteEntity> get_entity_with_neigh_source(uint8_t neighbour_address)
    {
       std::vector<RouteEntity> output;
       for(int i=0;i<m_route_list.size();i++)
       {
           if(m_route_list.at(i).get_neighbour_source()==neighbour_address)
           {
               output.push_back(m_route_list.at(i));
           }
       } 
       return output;
    }

    void clear_route_list()
    {
        m_route_list.clear();
    }

    void update_advertise_parameters()
    {
        //Here every parameter is updated to the advertised version
        //On every sequence number update the advertised hopcount
        uint8_t max_hop = 0;
        uint32_t max_advertised_cetx = 0;
        uint32_t max_advertised_cete = 0;
        uint32_t max_advertised_mre = 2808348671;
        if (m_route_list.empty())
        {
            //It is empty so make next hop NET_DIAMETER
            max_hop = NET_DIAMETER;
        }
        else {
            for (std::vector<RouteEntity>::iterator i =m_route_list.begin (); i != m_route_list.end (); ++i)
            {
                if (i->get_hopcount()>max_hop)
                {
                    max_hop = i->get_hopcount(); 
                }
                if (i->get_cetx()>max_advertised_cetx)
                {
                    max_advertised_cetx = i->get_cetx();
                }
                if (i->get_cete()>max_advertised_cete)
                {
                    max_advertised_cete = i->get_cete();
                }
                if (i->get_mre()<max_advertised_mre)
                {
                    max_advertised_mre = i->get_mre();
                }
            }        
        }
    m_advertised_cetx = max_advertised_cetx;
    m_advertised_cete = max_advertised_cete;
    m_advertised_mre = max_advertised_mre;
    m_advertised_hopcount = max_hop;
    }

    void update_LoRa_path() //Used to update what path sould be chosen. For now forward to path with the smallest hop
    {
        //Assuming made here it is new hop look at smallest hop best
        m_LoRa_route.SetNextHop(m_route_list.front().get_next_hop());
        for (int i = 1; i<m_route_list.size(); i++)
         {
          if  (m_LoRa_route.GetNextHop()>m_route_list.at(i).get_next_hop())
          {
            //This is smaller so make this next hop
            std::cout<<"Smallest hop set "<<m_route_list.at(i).get_next_hop()<<" in line 166"<<endl;
            m_LoRa_route.SetNextHop(m_route_list.at(i).get_next_hop());
            }
        }         
    }

///////////////////////////////////////////////
    void getPrecursorsEntry(std::vector<uint8_t> output)
    {
        //Gives all precursors as RRER is sent when no other alternative route so then notify all that relies on destination
        for (int i=0 ;i<m_route_list.size();i++)
        {
            if (!m_route_list.at(i).IsPrecursorListEmpty ())
            {
            std::vector<uint8_t> holder;
            m_route_list.at(i).GetPrecursors(holder);
            for (std::vector<uint8_t>::const_iterator i = holder.begin (); i
                                                                                    != holder.end (); ++i)
            {
                bool result = true;
                for (std::vector<uint8_t>::const_iterator j = output.begin (); j
                                                                            != output.end (); ++j)
                {
                    if (*j == *i)
                    {
                        result = false;
                    }
                }
                if (result)
                {
                    output.push_back (*i);
                }
            }
            }
        }
    }
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

struct IsNeigh
{
    uint8_t neighbor;
    bool
    operator() (RouteEntity const & e) const
    {
        return (e.get_next_hop()==neighbor);
    }
};
    bool removeSpecificEntity(RouteEntity rid)
    {
        IsNeigh pred {rid.get_next_hop()};
        std::vector<uint8_t> indexing;
        if (m_route_list.size()==0)
        {
            return false;
        }
        else 
        {
    m_route_list.erase (std::remove_if (m_route_list.begin (), m_route_list.end (), pred),
                   m_route_list.end ());
        return true;
        }
    }

    bool isRouteListEmpty()
    {
        return m_route_list.empty();
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
    

    void SetNextHop ()
    {
        //AOMDV changed so the next hop is merely updated
        update_LoRa_path();
    }

    uint8_t GetNextLoRaHop()
    {
        update_LoRa_path();
        return m_LoRa_route.GetNextHop();
    }
    std::vector<uint8_t> GetNextHop (uint8_t neighbour_address) const
    {
        //AOMDV now gives a vector of next hops
        std::vector<uint8_t> output;
        for (std::vector<RouteEntity>::const_iterator i = m_route_list.begin (); i!= m_route_list.end ();i++ )
        {
            if (i->get_neighbour_source() == neighbour_address)
            {
                output.push_back(i->get_next_hop());
            }
        }
        return output;
    }

    std::vector<uint8_t> GetEveryHop() 
    {
        std::vector<uint8_t> output;
        for (std::vector<RouteEntity>::const_iterator i = m_route_list.begin (); i!= m_route_list.end ();i++ )
        {
            output.push_back(i->get_next_hop());
        }
        return output;        
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

    uint32_t GetCetx() const
    {
        return m_advertised_cetx;
    }

    uint32_t GetCete() const
    {
        return m_advertised_cete;
    }

    uint32_t GetMre() const
    {
        return m_advertised_mre;
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
    void GetListOfDestinationWithNextHopAOMDV (uint8_t nextHop, std::map<uint8_t, uint32_t> & unreachable);
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