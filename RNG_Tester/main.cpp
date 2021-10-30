#include "main.h"
#include <cstdint>

// main() runs in its own thread in the OS
int main()
{
    pc.baud(9600);

    while (true) {
        ThisThread::sleep_for(1s);
        uint8_t reading = RNG.getByte();
        uint8_t my_address = 100;
        uint8_t my_address_2 = 150;
        uint8_t neighbour_address_1 = 120;
        uint8_t neighbour_address_2 = 130;
        //Sending first type of packet
        std::cout<<"ST"<<my_address<<"LD"<<reading<<endl;
        //Sending second type of packet
        //['Routing node address','P','S','Amount of Packets sent','N','D','Neighbour destination','R','A'........,'\n'],
        std::cout<<my_address<<"ND"<<neighbour_address_1<<"PS"<<RNG.getByte()<<"RA"<<my_address<<"ND"<<neighbour_address_2<<"PS"<<RNG.getByte()<<endl;

        ThisThread::sleep_for(1s);
        //Sending first type of packet different user
        std::cout<<"ST"<<my_address_2<<"LD"<<reading<<endl;
        //Sending second type of packet
        //['Routing node address','P','S','Amount of Packets sent','N','D','Neighbour destination','R','A'........,'\n'],
        std::cout<<my_address_2<<"ND"<<neighbour_address_1<<"PS"<<RNG.getByte()<<"RA"<<my_address<<"ND"<<neighbour_address_2<<"PS"<<RNG.getByte()<<endl;

        //Repeat test but now missing a neighbour node
        ThisThread::sleep_for(1s);
        //Sending first type of packet
        std::cout<<"ST"<<my_address<<"LD"<<reading<<endl;
        //Sending second type of packet
        //['Routing node address','P','S','Amount of Packets sent','N','D','Neighbour destination','R','A'........,'\n'],
        std::cout<<my_address<<"ND"<<neighbour_address_1<<"PS"<<RNG.getByte()<<"RA"<<my_address<<"ND"<<neighbour_address_1<<"PS"<<RNG.getByte()<<endl;
        
        ThisThread::sleep_for(1s);
        //Sending first type of packet different user
        std::cout<<"ST"<<my_address_2<<"LD"<<reading<<endl;
        //Sending second type of packet
        //['Routing node address','P','S','Amount of Packets sent','N','D','Neighbour destination','R','A'........,'\n'],
        std::cout<<my_address_2<<"ND"<<neighbour_address_1<<"PS"<<RNG.getByte()<<"RA"<<my_address<<"ND"<<neighbour_address_2<<"PS"<<RNG.getByte()<<endl;


    }
}

