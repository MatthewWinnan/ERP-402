#ifndef __MAIN_H__
#define __MAIN_H__

#include "mbed.h"
#include "rng.h"

#include <algorithm>  
#include <cstdint>
#include <vector>

#include <algorithm>
#include <ctime>
#include <iostream>
#include <string>
#include <vector>

EventQueue main_queue(32 * EVENTS_EVENT_SIZE); //this will call an event in IRQ so the process can be handled safely.
Thread main_thread; //Thread that handles the queue

Ticker send_rng_t;

void Send_RNG_Timer_Expire();
void Queue_Send_RNG_Timer_Expire();

void Rx_interrupt();
void read_line();

// Circular buffers for serial TX and RX data - used by interrupt routines
const int buffer_size = 255;
// might need to increase buffer size for high baud rates
char tx_buffer[buffer_size];
uint8_t rx_buffer[buffer_size];
// Circular buffer pointers
// volatile makes read-modify-write atomic
volatile int tx_in=0;
volatile int tx_out=0;
volatile int rx_in=0;
volatile int rx_out=0;
// Line buffers for sprintf and sscanf
//char tx_line[80];
uint8_t rx_line[80];
//Flags for events????
uint8_t rx_bit = 0;

//TX and RX handler
mbed::UnbufferedSerial pc(USBTX, USBRX);

Random RNG = Random();


#endif