#include "main.h"

// main() runs in its own thread in the OS
int main()
{
    pc.baud(9600);

    while (true) {
        ThisThread::sleep_for(2ms);
        uint8_t reading = RNG.getByte();
        std::cout<<reading;
    }
}

