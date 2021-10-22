#include "aodv_neighbours.h"
#include <iostream>

Neighbors::Neighbors(clock_t delay)   : m_ntimer (delay)
{
    //TODO here set up the check call for living neigh
//    m_ntimer.SetDelay (delay);
//    m_ntimer.SetFunction (&Neighbors::Purge, this);
//    m_txErrorCallback = MakeCallback (&Neighbors::ProcessTxError, this);
}

clock_t Neighbors::GetExpireTime(uint8_t addr) {
    Purge ();
    for (std::vector<Neighbor>::const_iterator i = m_nb.begin (); i
                                                                  != m_nb.end (); ++i)
    {
        if (i->m_neighborAddress == addr)
        {
            return (i->m_expireTime - clock());
        }
    }
    return 0;
}

bool Neighbors::IsNeighbor(uint8_t addr) {
    Purge ();
    for (std::vector<Neighbor>::const_iterator i = m_nb.begin ();
         i != m_nb.end (); ++i)
    {
        if (i->m_neighborAddress == addr)
        {
            return true;
        }
    }
    return false;
}

void Neighbors::Update(uint8_t addr, clock_t expire) {
    for (std::vector<Neighbor>::iterator i = m_nb.begin (); i != m_nb.end (); ++i)
    {
        if (i->m_neighborAddress == addr)
        {
            i->m_expireTime = std::max (expire + clock(), i->m_expireTime);
            return;
        }
    }

    Neighbor neighbor (addr, expire + clock());
    m_nb.push_back (neighbor);
    Purge ();
}
void Neighbors::RemoveNeighbour(uint8_t dst)
{
    Purge();
    int index = -1;
    for (int i = 0; i<m_nb.size(); i++)
    {
        if(m_nb.at(i).m_neighborAddress==dst)
        {
            index = i;
            i= m_nb.size();//end the loop
        }
    }
    if (index!=-1)
    {
        m_nb.erase(m_nb.begin()+index);
    }
    else
    {
    }
}
struct CloseNeighbor
{
    bool operator() (const Neighbors::Neighbor & nb) const
    {
        return ((nb.m_expireTime < clock()) || nb.close);
    }
};
void Neighbors::Purge() {
    if (m_nb.empty ())
    {
        return;
    }

    CloseNeighbor pred;
    m_nb.erase (std::remove_if (m_nb.begin (), m_nb.end (), pred), m_nb.end ());
    //TODO here reschedule the purge
//    m_ntimer.Cancel ();
//    m_ntimer.Schedule ();
}

void Neighbors::ScheduleTimer() {
//TODO here refresh the timer that checks for neighbours
}

void Neighbors::Print()
{
    Purge();
    for (std::vector<Neighbor>::iterator i = m_nb.begin (); i != m_nb.end (); ++i)
        {
    logInfo("Neighbor Address ------------- %lu", i->m_neighborAddress);
        }

    }