#include "aodv_id_cache.h"


 bool
 IdCache::IsDuplicate (uint8_t addr, uint8_t id)
 {
   Purge ();
   for (std::vector<UniqueId>::const_iterator i = m_idCache.begin ();
        i != m_idCache.end (); ++i)
     {
       if (i->m_context == addr && i->m_id == id)
         {
           return true;
         }
     }
   struct UniqueId uniqueId =
   {
     addr, id, m_lifetime + clock() 
     };
   m_idCache.push_back (uniqueId);
   return false;
 }
 void
 IdCache::Purge ()
 {
   m_idCache.erase (remove_if (m_idCache.begin (), m_idCache.end (),
                               IsExpired ()), m_idCache.end ());
 }
  
 uint8_t
 IdCache::GetSize ()
 {
   Purge ();
   return m_idCache.size ();
 }