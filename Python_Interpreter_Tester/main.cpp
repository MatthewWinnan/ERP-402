#include "main.h"
#include <cstdint>

// main() runs in its own thread in the OS
int main()
{
    pc.baud(9600);
    bool is_client = true;
    bool is_dst = true;
    while (true) {
        ThisThread::sleep_for(2s);
        uint8_t reading = 0;
        uint8_t my_address = 100;
        uint8_t neighbour_address_1 = 110;
        uint8_t neighbour_address_2 = 120;
        uint8_t reading_1 = 0;
        uint8_t reading_2 = 0;
        uint8_t ping_reading_1 = 0;
        uint8_t ping_reading_2 = 0;
        uint8_t destination_add_1 = 130;
        //Sending first type of packet
        while((reading==0) || (reading==13) || (reading==10))
        {
            reading = RNG.getByte();
        }
        std::cout<<"ST"<<my_address<<"LD"<<reading<<endl;
        //Sending second type of packet
        //['Routing node address','P','S','Amount of Packets sent','N','D','Neighbour destination','R','A'........,'\n'],
        //Ensure that readings don't equal 0,endl or line feed
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1==0) || (reading_1==13) || (reading_1==10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2==0) || (reading_2==13) || (reading_2==10))
        {
            reading_2 = RNG.getByte();
        }
        std::cout<<my_address<<"ND"<<neighbour_address_1<<"PS"<<reading_1<<"RA";
        std::cout<<my_address<<"ND"<<neighbour_address_2<<"PS"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"ND"<<my_address<<"PS"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"ND"<<my_address<<"PS"<<reading_1<<"RA";

        std::cout<<destination_add_1<<"ND"<<neighbour_address_1<<"PS"<<reading_1<<"RA";
        std::cout<<destination_add_1<<"ND"<<neighbour_address_2<<"PS"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"ND"<<destination_add_1<<"PS"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"ND"<<destination_add_1<<"PS"<<reading_1<<"RA";

        std::cout<<neighbour_address_2<<"ND"<<neighbour_address_1<<"PS"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"ND"<<neighbour_address_2<<"PS"<<reading_2<<endl;
        //Sending third type of packet
        //['Routing node address','N','S','Neighbour source','P','R','Amount of Packets received','R','A'........,'\n'],
                //Ensure that readings don't equal 0,endl or line feed
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1==0) || (reading_1==13) || (reading_1==10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2==0) || (reading_2==13) || (reading_2==10))
        {
            reading_2 = RNG.getByte();
        }
        //std::cout<<my_address<<"NS"<<neighbour_address_1<<"PR"<<reading_1<<"RA";
        //std::cout<<neighbour_address_1<<"NS"<<my_address<<"PR"<<reading_2<<endl;
        std::cout<<my_address<<"NS"<<neighbour_address_1<<"PR"<<reading_1<<"RA";
        std::cout<<my_address<<"NS"<<neighbour_address_2<<"PR"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<my_address<<"PR"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"NS"<<my_address<<"PR"<<reading_1<<"RA";

        std::cout<<destination_add_1<<"NS"<<neighbour_address_1<<"PR"<<reading_1<<"RA";
        std::cout<<destination_add_1<<"NS"<<neighbour_address_2<<"PR"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<destination_add_1<<"PR"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"NS"<<destination_add_1<<"PR"<<reading_1<<"RA";

        std::cout<<neighbour_address_2<<"NS"<<neighbour_address_1<<"PR"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<neighbour_address_2<<"PR"<<reading_2<<endl;

        //Sending fourth type of packet
        //['Routing node address','N','S','Neighbour source','R','I','RSSI measurement','R','A'........,'\n']
                //Ensure that readings don't equal 0,endl or line feed
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1==0) || (reading_1==13) || (reading_1==10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2==0) || (reading_2==13) || (reading_2==10))
        {
            reading_2 = RNG.getByte();
        }
        //std::cout<<my_address<<"NS"<<neighbour_address_1<<"RI"<<reading_1<<"RA"<<my_address<<"NS"<<neighbour_address_2<<"RI"<<reading_2<<endl;
                std::cout<<my_address<<"NS"<<neighbour_address_1<<"RI"<<reading_1<<"RA";
        std::cout<<my_address<<"NS"<<neighbour_address_2<<"RI"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<my_address<<"RI"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"NS"<<my_address<<"RI"<<reading_1<<"RA";

        std::cout<<destination_add_1<<"NS"<<neighbour_address_1<<"RI"<<reading_1<<"RA";
        std::cout<<destination_add_1<<"NS"<<neighbour_address_2<<"RI"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<destination_add_1<<"RI"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"NS"<<destination_add_1<<"RI"<<reading_1<<"RA";

        std::cout<<neighbour_address_2<<"NS"<<neighbour_address_1<<"RI"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<neighbour_address_2<<"RI"<<reading_2<<endl;

        //Sending fifth type of packet 
        //['Routing node address','N','S','Neighbour source','S','N','SNR measurement','R','A'........,'\n'],
        reading_1 = 0;
        reading_2 = 0;
        while((reading_1==0) || (reading_1==13) || (reading_1==10))
        {
            reading_1 = RNG.getByte();
        }
        while((reading_2==0) || (reading_2==13) || (reading_2==10))
        {
            reading_2 = RNG.getByte();
        }
       // std::cout<<my_address<<"NS"<<neighbour_address_1<<"SN"<<reading_1<<"RA"<<my_address<<"NS"<<neighbour_address_2<<"SN"<<reading_2<<endl;
        std::cout<<my_address<<"NS"<<neighbour_address_1<<"SN"<<reading_1<<"RA";
        std::cout<<my_address<<"NS"<<neighbour_address_2<<"SN"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<my_address<<"SN"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"NS"<<my_address<<"SN"<<reading_1<<"RA";

        std::cout<<destination_add_1<<"NS"<<neighbour_address_1<<"SN"<<reading_1<<"RA";
        std::cout<<destination_add_1<<"NS"<<neighbour_address_2<<"SN"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<destination_add_1<<"SN"<<reading_1<<"RA";
        std::cout<<neighbour_address_2<<"NS"<<destination_add_1<<"SN"<<reading_1<<"RA";

        std::cout<<neighbour_address_2<<"NS"<<neighbour_address_1<<"SN"<<reading_1<<"RA";
        std::cout<<neighbour_address_1<<"NS"<<neighbour_address_2<<"SN"<<reading_2<<endl;


        //Sending sixth type of packet
        //['Routing node address','D','A','Destination address','C','P', 'Next hop address','T','E','Next hop address','R','A'........, '\n']
        std::cout<<my_address<<"DA"<<destination_add_1<<"CP"<<neighbour_address_2<<"TE"<<neighbour_address_2<<"RA";
        std::cout<<neighbour_address_2<<"DA"<<destination_add_1<<"CP"<<destination_add_1<<"TE"<<destination_add_1<<"RA";
        std::cout<<neighbour_address_1<<"DA"<<destination_add_1<<"CP"<<destination_add_1<<"TE"<<destination_add_1<<"RA";
        std::cout<<destination_add_1<<"DA"<<destination_add_1<<"CP"<<destination_add_1<<"TE"<<destination_add_1<<endl;

        //Sending additional node specific data
        if (is_client)
        {
            reading_1 = 0;
            reading_2 = 0;
            while((reading_1==0) || (reading_1==13) || (reading_1==10))
            {
                reading_1 = RNG.getByte();
            }
            while((reading_2==0) || (reading_2==13) || (reading_2==10))
            {
                reading_2 = RNG.getByte();
            }
            //Sending 7'th packet type for client
            //['Source node address','D','A','Destination Address','M','S','Amount of messages sent','R','A',..........,'\n']
            std::cout<<my_address<<"DA"<<destination_add_1<<"MS"<<reading_1<<endl;
            // std::cout<<my_address<<"DA"<<destination_add_2<<"MS"<<reading_2<<endl;           
        }
        if (is_dst)
        {
            ping_reading_1 = 0;
            ping_reading_2 = 0;
            reading_1 = 0;
            reading_2 = 0;
            while((reading_1==0) || (reading_1==13) || (reading_1==10))
            {
                reading_1 = RNG.getByte();
            }
            while((reading_2==0) || (reading_2==13) || (reading_2==10))
            {
                reading_2 = RNG.getByte();
            }
            while((ping_reading_1==0) || (ping_reading_1==13) || (ping_reading_1==10))
            {
                ping_reading_1 = RNG.getByte();
            }
            while((ping_reading_2==0) || (ping_reading_2==13) || (ping_reading_2==10))
            {
                ping_reading_2 = RNG.getByte();
            }
            //Sending 7'th destination node specific packet
            //['Destination node address','C','N',Client address,'M','R','Amount of messages received','P','I','Ping','R','A',........,'\n']
            std::cout<<destination_add_1<<"CN"<<my_address<<"MR"<<reading_1<<"PI"<<ping_reading_2<<endl;
            //std::cout<<my_address<<"CN"<<destination_add_2<<"MR"<<reading_2<<"PI"<<ping_reading_1<<endl; 
        }

    }
}

