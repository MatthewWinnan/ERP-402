#ifndef __RNG_H__
#define __RNG_H__

#include "mbed.h"
#include "Crypto.h"
#include <algorithm>  
#include <cstdint>
#include <cmath>
#include <ctime>
#include <utility>

class Random
{
    public :
        
        static void init();
        static uint8_t getByte();
        static void getBytes(uint8_t *out, uint32_t length);
};


#endif