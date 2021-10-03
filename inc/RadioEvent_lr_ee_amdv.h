#include "dot_util.h"
#if ACTIVE_VERSION == LR_EE_AOMDV_LD_LR
#ifndef __RADIO_EVENT_LR_EE_AMDV_H__
#define __RADIO_EVENT_LR_EE_AMDV_H__

#include "mbed.h"
#include "mDotEvent.h"
#include "aodv_queue.h"
#include <iostream>

//Flag to indicate that radio is done or busy
//False means no change and can't access radio handler yet
//True means radio event sent new packet thus can process and potentially 
//transmit reply 
extern RequestQueue route_queue;
extern RequestQueue message_request_queue;
extern uint32_t m_rx_count; //keeps track of messages received per epoch count
extern std::map<uint8_t,uint32_t> neighbour_rx;
bool radio_is_busy;
std::vector<uint8_t> radio_data;

void add_rx_data_queue(LoRaMacEventInfo* data);

void Update_neighbour_rx(uint8_t neigh_address);

/////Declare some external variables here



class RadioEvent : public mDotEvent
{

public:
    RadioEvent() {}

    virtual ~RadioEvent() {}

    virtual void PacketRx(uint8_t port, uint8_t *payload, uint16_t size, int16_t rssi, int16_t snr, lora::DownlinkControl ctrl, uint8_t slot, uint8_t retries, uint32_t address, uint32_t fcnt, bool dupRx) {
        mDotEvent::PacketRx(port, payload, size, rssi, snr, ctrl, slot, retries, address, fcnt, dupRx);
    }

    /*!
     * MAC layer event callback prototype.
     *
     * \param [IN] flags Bit field indicating the MAC events occurred
     * \param [IN] info  Details about MAC events occurred
     */
    virtual void MacEvent(LoRaMacEventFlags* flags, LoRaMacEventInfo* info) {
        radio_is_busy = false;

        if (mts::MTSLog::getLogLevel() == mts::MTSLog::TRACE_LEVEL) {
            std::string msg = "OK";
            switch (info->Status) {
                case LORAMAC_EVENT_INFO_STATUS_ERROR:
                    msg = "ERROR";
                    break;
                case LORAMAC_EVENT_INFO_STATUS_TX_TIMEOUT:
                    msg = "TX_TIMEOUT";
                    break;
                case LORAMAC_EVENT_INFO_STATUS_RX_TIMEOUT:
                    msg = "RX_TIMEOUT";
                    break;
                case LORAMAC_EVENT_INFO_STATUS_RX_ERROR:
                    msg = "RX_ERROR";
                    break;
                case LORAMAC_EVENT_INFO_STATUS_JOIN_FAIL:
                    msg = "JOIN_FAIL";
                    break;
                case LORAMAC_EVENT_INFO_STATUS_DOWNLINK_FAIL:
                    msg = "DOWNLINK_FAIL";
                    break;
                case LORAMAC_EVENT_INFO_STATUS_ADDRESS_FAIL:
                    msg = "ADDRESS_FAIL";
                    break;
                case LORAMAC_EVENT_INFO_STATUS_MIC_FAIL:
                    msg = "MIC_FAIL";
                    break;
                default:
                    break;
            }
            // logTrace("Event: %s", msg.c_str());

            // logTrace("Flags Tx: %d Rx: %d RxData: %d RxSlot: %d LinkCheck: %d JoinAccept: %d",
            //          flags->Bits.Tx, flags->Bits.Rx, flags->Bits.RxData, flags->Bits.RxSlot, flags->Bits.LinkCheck, flags->Bits.JoinAccept);
            // logTrace("Info: Status: %d ACK: %d Retries: %d TxDR: %d RxPort: %d RxSize: %d RSSI: %d SNR: %d Energy: %d Margin: %d Gateways: %d",
            //          info->Status, info->TxAckReceived, info->TxNbRetries, info->TxDatarate, info->RxPort, info->RxBufferSize,
            //          info->RxRssi, info->RxSnr, info->Energy, info->DemodMargin, info->NbGateways);
        }

        if (flags->Bits.Rx) {

            logInfo("Rx %d bytes", info->RxBufferSize);

            if (info->RxBufferSize > 0) {
                //Print Contents
                for (int i =0;i<info->RxBufferSize;i++)
                {
                    std::cout << "Data at index " << i <<" is "<< info->RxBuffer[i]<<std::endl;
                    }
                //This is where I can see what data is being received.
                    add_rx_data_queue(info);
            }//end if rxbuffer
        }//if flags bits.rx
        radio_is_busy = true;
    }//end of lora mac event

};

//Adds the new rx data to be handled and then queued based on things
void add_rx_data_queue(LoRaMacEventInfo* data){
    if ( !radio_data.empty())
    {
        //First clear the old data
        radio_data.clear();
        }
    for (int i=0;i<data->RxBufferSize;i++)
    {
        //add every byte to rx vector
        radio_data.push_back(data->RxBuffer[i]);
        }
    //QueueEntry (std::vector<uint8_t> packet, clock_t exp)
    //Adds a new entry to the overall queue handler
    QueueEntry newEntry (radio_data,QUEUE_TIMEOUT*CLOCKS_PER_SEC/1000);
    Update_neighbour_rx(radio_data.at(2));//Updating receiving from neighbour
    if (radio_data.at(0)<6)
    {
        //Enter this into the message queue
                //Enter this into the request queue
        if(!route_queue.Enqueue(newEntry))
        {
            //This means was not successful for some reason
            //TODO find out what to do
            logInfo("ERROR did not enqueue");
            }
        else
        {
            logInfo("Entered the data line 130");
            }
        }
    else
    {
        //Enter this into the request queue
        if(!message_request_queue.Enqueue(newEntry))
        {
            //This means was not successful for some reason
            //TODO find out what to do
            logInfo("ERROR did not enqueue");
            }
            else
            {
                logInfo("Entered the data line 144");
                }
        }
    
}


void Update_neighbour_rx(uint8_t neigh_address)
{
//Can at the same time increase tx amount since the same
    m_rx_count++;
    if (neighbour_rx.empty())
    {
        //empty add a new entry
        neighbour_rx.insert(std::make_pair(neigh_address, 1));
    }
    else 
    {
        //Find if it is in the list
        auto entry = neighbour_rx.find(neigh_address);
        if (entry->first == neigh_address)
        {
            //entry found now update count
            entry->second++;
        }
        else {
        //insert a new element
        neighbour_rx.insert(std::make_pair(neigh_address, 1));
        }

    }
}

#endif
#endif