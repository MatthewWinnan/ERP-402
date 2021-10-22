#ifndef AODV_ID_CACHE_H
#define AODV_ID_CACHE_H

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

///////////////////This class is needed for keeping track of doubles in the 
///////history of messages


class IdCache
 {
 private:
   struct UniqueId
   {
     uint8_t m_context;
     uint8_t m_id;
     clock_t m_expire;
   };
   struct IsExpired
   {
     bool operator() (const struct UniqueId & u) const
     {
       return (u.m_expire < clock());
     }
   };
   std::vector<UniqueId> m_idCache;
   clock_t m_lifetime;
   
 public:
   IdCache (clock_t lifetime) : m_lifetime (lifetime)
   {
   }
   bool IsDuplicate (uint8_t addr, uint8_t id);
   void Purge ();
   uint8_t GetSize ();
   void SetLifetime (clock_t lifetime)
   {
     m_lifetime = lifetime;
   }
   clock_t GetLifeTime () const
   {
     return m_lifetime;
   }
 };

#endif