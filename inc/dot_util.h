#ifndef __DOT_UTIL_H__
#define __DOT_UTIL_H__

#include "mbed.h"
#include "mDot.h"
#include "ChannelPlans.h"
#include "MTSLog.h"
#include "MTSText.h"
#include "example_config.h"
# include "network_config.h"

extern mDot* dot;

lora::ChannelPlan* create_channel_plan();

void display_config();

void update_ota_config_name_phrase(std::string network_name, std::string network_passphrase, uint8_t frequency_sub_band, lora::NetworkType network_type, uint8_t ack);

void update_ota_config_id_key(uint8_t *network_id, uint8_t *network_key, uint8_t frequency_sub_band, lora::NetworkType public_network, uint8_t ack);

void update_manual_config(uint8_t *network_address, uint8_t *network_session_key, uint8_t *data_session_key, uint8_t frequency_sub_band, lora::NetworkType network_type, uint8_t ack);

void update_peer_to_peer_config(uint8_t *network_address, uint8_t *network_session_key, uint8_t *data_session_key, uint32_t tx_frequency, uint8_t tx_datarate, uint8_t tx_power);

void update_network_link_check_config(uint8_t link_check_count, uint8_t link_check_threshold);

void join_network();

void sleep_wake_rtc_only(bool deepsleep);

void sleep_wake_interrupt_only(bool deepsleep);

void sleep_wake_rtc_or_interrupt(bool deepsleep);

void sleep_save_io();

void sleep_configure_io();

void sleep_restore_io();

int send_data(std::vector<uint8_t> data);

void connect_mesh();

int send_rreq(uint8_t source_add, uint8_t destination_add, uint8_t hop_count, uint8_t rreq_id, uint8_t dest_seq_num, uint8_t origin_seq_num);

int send_rrep(uint8_t source_add, uint8_t destination_add, uint8_t hop_count, uint8_t lifetime, uint8_t dest_seq_num, uint8_t origin_seq_num);





#endif
