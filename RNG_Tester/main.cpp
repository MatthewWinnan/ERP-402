#include "main.h"
#include <cstdint>

// main() runs in its own thread in the OS
int main()
{
    pc.baud(9600);

    while (true) {
        ThisThread::sleep_for(2s);
        uint8_t reading = 0;
        uint8_t my_address = 100;
        uint8_t my_address_2 = 160;
        uint8_t neighbour_address_1 = 120;
        uint8_t neighbour_address_2 = 130;
        uint8_t neighbour_address_3 = 140;
        uint8_t reading_1 = 0;
        uint8_t reading_2 = 0;
        uint8_t destination_add_1 = 200;
        uint8_t destination_add_2 = 220;
        //Sending first type of packet
        while((reading!=0) && (reading!=13) && (reading!=10))
        {
            reading = RNG.getByte();
        }
        std::cout<<"ST"<<my_address<<"LD"<<reading<<endl;
        //Sending second type of packet
        //['Routing node address','P','S','Amount of Packets sent','N','D','Neighbour destination','R','A'........,'\n'],
        //Ensure that readings don't equal 0,endl or line feed
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1!=0) && (reading_1!=13) && (reading_1!=10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2!=0) && (reading_2!=13) && (reading_2!=10))
        {
            reading_2 = RNG.getByte();
        }
        std::cout<<my_address<<"ND"<<neighbour_address_1<<"PS"<<reading_1<<"RA"<<my_address<<"ND"<<neighbour_address_2<<"PS"<<reading_2<<endl;
        //Sending third type of packet
        //['Routing node address','N','S','Neighbour source','P','R','Amount of Packets received','R','A'........,'\n'],
                //Ensure that readings don't equal 0,endl or line feed
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1!=0) && (reading_1!=13) && (reading_1!=10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2!=0) && (reading_2!=13) && (reading_2!=10))
        {
            reading_2 = RNG.getByte();
        }
        std::cout<<my_address<<"NS"<<neighbour_address_1<<"PR"<<reading_1<<"RA"<<my_address<<"NS"<<neighbour_address_2<<"PR"<<reading_2<<endl;
        //Sending fourth type of packet
        //['Routing node address','N','S','Neighbour source','R','I','RSSI measurement','R','A'........,'\n']
                //Ensure that readings don't equal 0,endl or line feed
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1!=0) && (reading_1!=13) && (reading_1!=10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2!=0) && (reading_2!=13) && (reading_2!=10))
        {
            reading_2 = RNG.getByte();
        }
        std::cout<<my_address<<"NS"<<neighbour_address_1<<"RI"<<reading_1<<"RA"<<my_address<<"NS"<<neighbour_address_2<<"RI"<<reading_2<<endl;
        //Sending fifth type of packet 
        //['Routing node address','N','S','Neighbour source','S','N','SNR measurement','R','A'........,'\n'],
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1!=0) && (reading_1!=13) && (reading_1!=10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2!=0) && (reading_2!=13) && (reading_2!=10))
        {
            reading_2 = RNG.getByte();
        }
        std::cout<<my_address<<"NS"<<neighbour_address_1<<"SN"<<reading_1<<"RA"<<my_address<<"NS"<<neighbour_address_2<<"SN"<<reading_2<<endl;
        //Sending sixth type of packet
        //['Routing node address','D','A','Destination address','C','P', 'Next hop address','T','E','Next hop address','R','A'........, '\n']
        std::cout<<my_address<<"DA"<<destination_add_1<<"CP"<<neighbour_address_2<<"TE"<<neighbour_address_1<<"RA";
        std::cout<<my_address<<"DA"<<destination_add_1<<"CP"<<neighbour_address_2<<"TE"<<neighbour_address_3<<endl;

    }
}

