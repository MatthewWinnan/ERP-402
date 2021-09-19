# ERP-402
Final year project programming a routing system using LoRa as a medium. The program is built on the MbedOS and the LoRaMAC and LoRaPHY stacks included in MbedOS. 

Currently doing reasearch on AOMDV, LR-EE-AOMDV to help with improving path selection metrics, Adaptive backup routing for ad-hoc networks to help the AODV protocol form a more mesh
like structure during route discovery. This will be added to the AOMDV as AODV-ABR helps more with creating a more natural mesh repear system. Currently during link breaking 
AODV will flood the network which for mesh networks is undesirable as I want to minimize link breakages during my link checking stages.

Further I am studying Ad hoc on-demand distance vector multipath routing protocol with path selection entropy "AODVM-PSE" as this is a more probabilistic route selection 
tool that has a natural load balancing scheme as it takes ETA, packet overhead, packet wait times etc into account when calculating the probility of the packet arriving under 
acceptable QoS. This also seems to minimize energy costs which if a node has a high load I am expecting the energy cost to deleiver a packet to go up. Currently I don't have to paper I 
have applied for permission to receive it since the library doesn't have access to it.

1) Done with send_rreq
