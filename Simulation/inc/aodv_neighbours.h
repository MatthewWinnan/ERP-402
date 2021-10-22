#ifndef AODV_NEIGHBOURS_H
#define AODV_NEIGHBOURS_H


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

class Neighbors{
public:
    Neighbors (clock_t delay);
    struct Neighbor{
        uint8_t m_neighborAddress;
        clock_t m_expireTime;
        bool close;

                Neighbor (uint8_t ip, clock_t t)
                        : m_neighborAddress (ip),
                          m_expireTime (t),
                          close (false)
                {
                }
            };
    clock_t GetExpireTime (uint8_t addr);
            bool IsNeighbor (uint8_t addr);
            void Update (uint8_t addr, clock_t expire);
            void Purge ();
            void ScheduleTimer ();
            void Clear ()
            {
                m_nb.clear ();
            }
            void Print();
            void RemoveNeighbour(uint8_t dst);
    std::vector<Neighbor> getListNeighbours()
    {
                return m_nb;
    }

        private:
        clock_t m_ntimer;
        std::vector<Neighbor> m_nb;
        };


#endif //ALGORITHMS_AODV_NEIGHBOURS_H