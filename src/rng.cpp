#include "rng.h"

static uint8_t pool[16];
static AnalogIn e(PB_0),f(PB_1);
 
void Random::init()
{
    AnalogIn a(PC_1), b(PA_1), c(PA_4), d(PA_5);
    
    uint16_t tmp = a.read_u16();
    memcpy(pool, &tmp, 2);
    tmp = b.read_u16();
    memcpy(&pool[2], &tmp, 2);
    tmp = c.read_u16();
    memcpy(&pool[4], &tmp, 2);
    tmp = d.read_u16();
    memcpy(&pool[6], &tmp, 2);
    tmp = a.read_u16();
    memcpy(&pool[8], &tmp, 2);
    tmp = b.read_u16();
    memcpy(&pool[10], &tmp, 2);
    tmp = c.read_u16();
    memcpy(&pool[12], &tmp, 2);
    tmp = d.read_u16();
    memcpy(&pool[14], &tmp, 2);
}
 
uint8_t Random::getByte()
{
    uint8_t hash[16];
    MD5::computeHash(hash, pool, 16);
    uint8_t tmp = pool[hash[6]%16];
    memcpy(pool, hash, 16);
    pool[0] ^= (e.read_u16() & 0xff);
    return tmp ^ (f.read_u16() & 0xff);
}
 
void Random::getBytes(uint8_t *out, uint32_t length)
{
    for(int i = 0; i < length; ++i)
        out[i] = getByte();
}