#!/usr/bin/env python
#coding=utf-8
#################################
#   Copyright 2014.7.23
#       fly_video
#   @author: zhguixin@163.com
#################################
from gnuradio import audio
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio import filter
from gnuradio import vocoder
from gnuradio.filter import firdes
from optparse import OptionParser
import lte_sat

import wx
import wx.grid
import sys
import os
import threading
import multiprocessing
from multiprocessing import Queue
import socket,select
import json
import traceback,time
import ConfigParser
from wx.lib.pubsub import Publisher

import numpy as np

class eNB_ping_15prb_one65_video(gr.top_block):

    def __init__(self,**param):
        gr.top_block.__init__(self, "Enb Ping 15Prb One65 Video")

        ##################################################
        # Variables
        ##################################################
        try:
            if param['Bandwidth'] == '1.4':
                self.prbl = prbl = 6
                self.fftl = fftl = 128
            else:
                self.prbl = prbl = 15
                self.fftl = fftl = 256

            if param['mod_type_d'] == '16QAM':
                self.dl_mod_type = dl_mod_type = 2
            else:
                self.dl_mod_type = dl_mod_type = 1
            if param['mod_type_u'] == '16QAM':
                self.ul_mod_type = ul_mod_type = 2
            else:
                self.ul_mod_type = ul_mod_type = 1
            if param['samp_rate_G'] == '2M':
                self.samp_rate = samp_rate = 2e6 #2000000
            else:
                self.samp_rate = samp_rate = 4e6 #4000000
            # self.rnti = rnti = int(param['RNTI'])
            self.rnti = rnti = 65

            self.dl_rate = dl_rate = float(param['exp_code_rate_d_G'])
            self.ul_rate = ul_rate = float(param['exp_code_rate_u_G'])
            self.cell_id = cell_id = int(param['id_cell'])
            self.gain_r = gain_r = int(param['gain_r_G'])
            self.gain_s = gain_s = int(param['gain_s_G'])
            # self.samp_rate = samp_rate = 4e6
            self.ip = ip = param['ip']
            self.route = route = param['route']
            self.u_center_freq = u_center_freq = int(param['u_frequency_G'])
            self.d_center_freq = d_center_freq = int(param['d_frequency_G'])
            # self.mod_type = mod_type = 1
            # self.fftl = fftl = 256
            # self.prbl = prbl = 15
        except: print '变量初始化失败'

        print prbl,fftl,rnti,dl_mod_type,ul_mod_type,dl_rate,ul_rate,cell_id
        # 15 256 65 1 1 0.4 0.4 10
        print samp_rate
        print u_center_freq,d_center_freq
        # self.rnti = rnti = 65
        # self.prbl = prbl = 15
        # print ip,route
        print 'eNB_ping_15prb_one65_video'

        self.variable_ul_para_0 = variable_ul_para_0 = lte_sat.ul_parameter(rnti, prbl)
        self.variable_ul_para_0.set_cch_period(10, 4)
        self.variable_ul_para_0.set_srs_period(10, 5)
        self.variable_ul_para_0.set_sch_params(4, 2)
        self.variable_ul_para_0.set_srs_transmissionComb(1)
          
        # self.samp_rate = samp_rate = 4e6
        # self.mod_type = mod_type = 1
        # self.fftl = fftl = 256

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        # self.uhd_usrp_source_0.set_center_freq(40e6, 0)
        self.uhd_usrp_source_0.set_center_freq(u_center_freq*1e6, 0)
        self.uhd_usrp_source_0.set_gain(gain_r, 0)
        self.uhd_usrp_source_0.set_bandwidth(4e6, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        # self.uhd_usrp_sink_0.set_center_freq(20e6, 0)
        self.uhd_usrp_sink_0.set_center_freq(d_center_freq*1e6, 0)
        self.uhd_usrp_sink_0.set_gain(gain_s, 0)
        self.uhd_usrp_sink_0.set_bandwidth(4e6, 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=24,
                taps=None,
                fractional_bw=None,
        )
        self.lte_sat_ul_subframe_demapper_0 = lte_sat.ul_subframe_demapper(cell_id,prbl)
        self.lte_sat_ul_baseband_sync_0 = lte_sat.ul_baseband_sync(prbl,fftl,cell_id,0.5,False)
        self.lte_sat_layer2_0 = lte_sat.layer2(cell_id,prbl,dl_mod_type,dl_rate,ul_mod_type,ul_rate)
        self.lte_sat_layer2_0.create_logic_channel(rnti, 0, lte_sat.mode_um)
        
        self.lte_sat_eNB_config_0 = lte_sat.eNB_entity_config(False)
        self.lte_sat_eNB_config_0.set_leading_sched_b4_mapping(2, 5)
        self.lte_sat_eNB_config_0.set_leading_map_b4_sending(15)
        self.lte_sat_eNB_config_0.set_delay_sfc_for_pusch_after_usg(20)
        self.lte_sat_eNB_config_0.add_ul_param(variable_ul_para_0)
          
        self.lte_sat_dl_subframe_mapper_0_0 = lte_sat.dl_subframe_mapper(prbl,cell_id)
        self.lte_sat_dl_baseband_generator_0 = lte_sat.dl_baseband_generator(prbl, fftl)
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu("tun0", 100000)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.lte_sat_ul_baseband_sync_0, 0), (self.lte_sat_ul_subframe_demapper_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.lte_sat_ul_baseband_sync_0, 0))
        self.connect((self.lte_sat_ul_subframe_demapper_0, 0), (self.lte_sat_layer2_0, 0))
        self.connect((self.lte_sat_dl_baseband_generator_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.lte_sat_dl_subframe_mapper_0_0, 0), (self.lte_sat_dl_baseband_generator_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.blocks_tuntap_pdu_0, "pdus", self.lte_sat_layer2_0, "tx_data")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_ul_subframe_demapper_0, "sched_for_ul")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_ul_baseband_sync_0, "sched_for_ul")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_dl_subframe_mapper_0_0, "sched_info")
        self.msg_connect(self.lte_sat_layer2_0, "rx_data", self.blocks_tuntap_pdu_0, "pdus")
        self.msg_connect(self.lte_sat_ul_subframe_demapper_0, "SR", self.lte_sat_layer2_0, "sr_ta")
        self.msg_connect(self.lte_sat_ul_baseband_sync_0, "TA", self.lte_sat_layer2_0, "sr_ta")

    def get_status(self):
        status = {}
        status_temp = {}
        status_temp['rx_wrong_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_wrong_mac_pdu_count
        status_temp['rx_wrong_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_wrong_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_count
        status_temp['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_bps
        status_temp['rx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_count
        status_temp['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_bytes
        status_temp['rx_rlc_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_bps
        status_temp['rx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_count
        status_temp['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_bytes
        status_temp['rx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_bps
        status_temp['tx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_count
        status_temp['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_bytes
        status_temp['tx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_bps
        status_temp['tx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_pdu_count
        status_temp['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_pdu_bytes        
        
        status['stat_info_0'] = self.lte_sat_layer2_0.get_stat_string(0)
        status['stat_info_1'] = self.lte_sat_layer2_0.get_stat_string(1)
        status['ip'] = self.ip
        status['route'] = self.route
        status['u_freq'] = self.u_center_freq
        status['d_freq'] = self.d_center_freq

        status['rx_wrong_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_wrong_mac_pdu_count'])
        status['rx_wrong_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_wrong_mac_pdu_bytes'])
        status['rx_right_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_count'])
        status['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_bytes'])
        status['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_bps'])
        status['rx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_count'])
        status['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_bytes'])
        status['rx_rlc_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_bps'])
        status['rx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_count'])
        status['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_bytes'])
        status['rx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_bps'])
        status['tx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_count'])
        status['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_bytes'])
        status['tx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_bps'])
        status['tx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_pdu_count'])
        status['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_pdu_bytes'])
        status['rx_sr_num'] = self.lte_sat_layer2_0.get_stat_info().rx_sr_num
        status['rx_bsr_num'] = self.lte_sat_layer2_0.get_stat_info().rx_bsr_num
        return status

class eNB_ping_15prb_one65_audio(gr.top_block):

    def __init__(self,**param):
        gr.top_block.__init__(self, "Enb Ping 15Prb One65 Audio")

        ##################################################
        # Variables
        ##################################################
        try:
            if param['Bandwidth'] == '1.4':
                self.prbl = prbl = 6
                self.fftl = fftl = 128
            else:
                self.prbl = prbl = 15
                self.fftl = fftl = 256

            if param['mod_type_d'] == '16QAM':
                self.dl_mod_type = dl_mod_type = 2
            else:
                self.dl_mod_type = dl_mod_type = 1
            if param['mod_type_u'] == '16QAM':
                self.ul_mod_type = ul_mod_type = 2
            else:
                self.ul_mod_type = ul_mod_type = 1

            if param['samp_rate_G'] == '2M':
                self.samp_rate = samp_rate = 2e6
            else:
                self.samp_rate = samp_rate = 4e6  
            self.rnti = rnti = 65

            self.dl_rate = dl_rate = float(param['exp_code_rate_d_G'])
            self.ul_rate = ul_rate = float(param['exp_code_rate_u_G'])
            self.threshold = threshold = float(param['Threshold'])
            self.cell_id = cell_id = int(param['id_cell'])
            self.gain_r = gain_r = int(param['gain_r_G'])
            self.gain_s = gain_s = int(param['gain_s_G'])
            self.ip = ip = param['ip']
            self.route = route = param['route']
            self.u_center_freq = u_center_freq = int(param['u_frequency_G'])
            self.d_center_freq = d_center_freq = int(param['d_frequency_G'])
        except: print '变量初始化失败'

        print 'eNB_ping_15prb_one65_audio'
        # self.rnti = rnti = 65
        # self.prbl = prbl = 15
        self.variable_ul_para_0 = variable_ul_para_0 = lte_sat.ul_parameter(rnti, prbl)
        self.variable_ul_para_0.set_cch_period(10, 4)
        self.variable_ul_para_0.set_srs_period(10, 5)
        self.variable_ul_para_0.set_sch_params(4, 2)
        self.variable_ul_para_0.set_srs_transmissionComb(1)
        self.variable_ul_para_0.enable_bsr_persist(True)
        
        # self.samp_rate = samp_rate = 4e6
        # self.mod_type = mod_type = 1
        # self.fftl = fftl = 256

        ##################################################
        # Blocks
        ##################################################
        self.vocoder_g721_encode_sb_0 = vocoder.g721_encode_sb()
        self.vocoder_g721_decode_bs_0 = vocoder.g721_decode_bs()
        self.uhd_usrp_source_0 = uhd.usrp_source(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(800e6, 0)
        self.uhd_usrp_source_0.set_gain(10, 0)
        self.uhd_usrp_source_0.set_bandwidth(4e6, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(900e6, 0)
        self.uhd_usrp_sink_0.set_gain(10, 0)
        self.uhd_usrp_sink_0.set_bandwidth(4e6, 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=24,
                taps=None,
                fractional_bw=None,
        )
        self.lte_sat_ul_subframe_demapper_0 = lte_sat.ul_subframe_demapper(cell_id,prbl)
        self.lte_sat_ul_baseband_sync_0 = lte_sat.ul_baseband_sync(prbl,fftl,cell_id,threshold,False)
        self.lte_sat_tag_appender_1 = lte_sat.tag_appender(gr.sizeof_char, 1000)
        self.lte_sat_tag_appender_1.add_tag("dst_lcid", 0)
          
        self.lte_sat_tag_appender_0 = lte_sat.tag_appender(gr.sizeof_char, 1000)
        self.lte_sat_tag_appender_0.add_tag("dst_rnti", 65)
          
        self.lte_sat_layer2_0 = lte_sat.layer2(cell_id,prbl,dl_mod_type,dl_rate,ul_mod_type,ul_rate)
        self.lte_sat_layer2_0.create_logic_channel(rnti, 0, lte_sat.mode_um)
        
        self.lte_sat_eNB_config_0 = lte_sat.eNB_entity_config(False)
        self.lte_sat_eNB_config_0.set_leading_sched_b4_mapping(2, 5)
        self.lte_sat_eNB_config_0.set_leading_map_b4_sending(10)
        self.lte_sat_eNB_config_0.set_delay_sfc_for_pusch_after_usg(20)
        self.lte_sat_eNB_config_0.add_ul_param(variable_ul_para_0)
          
        self.lte_sat_dl_subframe_mapper_0_0 = lte_sat.dl_subframe_mapper(prbl,10)
        self.lte_sat_dl_baseband_generator_0 = lte_sat.dl_baseband_generator(prbl, fftl)
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, "packet_len")
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 1000, "packet_len")
        self.blocks_short_to_float_0 = blocks.short_to_float(1, 1024)
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, "packet_len")
        self.blocks_float_to_short_0 = blocks.float_to_short(1, 1024)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, "ul_demapper.dat", False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.audio_source_0 = audio.source(48000, "", True)
        self.audio_sink_0 = audio.sink(48000, "", True)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.lte_sat_tag_appender_0, 0))
        self.connect((self.lte_sat_dl_subframe_mapper_0_0, 0), (self.lte_sat_dl_baseband_generator_0, 0))
        self.connect((self.lte_sat_dl_baseband_generator_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.lte_sat_ul_baseband_sync_0, 0), (self.lte_sat_ul_subframe_demapper_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.lte_sat_ul_baseband_sync_0, 0))
        self.connect((self.lte_sat_ul_subframe_demapper_0, 0), (self.lte_sat_layer2_0, 0))
        self.connect((self.lte_sat_ul_subframe_demapper_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.vocoder_g721_encode_sb_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))
        self.connect((self.audio_source_0, 0), (self.blocks_float_to_short_0, 0))
        self.connect((self.blocks_float_to_short_0, 0), (self.vocoder_g721_encode_sb_0, 0))
        self.connect((self.blocks_short_to_float_0, 0), (self.audio_sink_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.vocoder_g721_decode_bs_0, 0))
        self.connect((self.vocoder_g721_decode_bs_0, 0), (self.blocks_short_to_float_0, 0))
        self.connect((self.lte_sat_tag_appender_1, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect((self.lte_sat_tag_appender_0, 0), (self.lte_sat_tag_appender_1, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_dl_subframe_mapper_0_0, "sched_info")
        self.msg_connect(self.blocks_tagged_stream_to_pdu_0, "pdus", self.lte_sat_layer2_0, "tx_data")
        self.msg_connect(self.lte_sat_ul_baseband_sync_0, "TA", self.lte_sat_layer2_0, "sr_ta")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_ul_subframe_demapper_0, "sched_for_ul")
        self.msg_connect(self.lte_sat_ul_subframe_demapper_0, "SR", self.lte_sat_layer2_0, "sr_ta")
        self.msg_connect(self.lte_sat_layer2_0, "rx_data", self.blocks_pdu_to_tagged_stream_0, "pdus")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_ul_baseband_sync_0, "sched_for_ul")

    def get_status(self):
        status = {}
        status_temp = {}
        status_temp['rx_wrong_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_wrong_mac_pdu_count
        status_temp['rx_wrong_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_wrong_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_count
        status_temp['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_bps
        status_temp['rx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_count
        status_temp['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_bytes
        status_temp['rx_rlc_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_bps
        status_temp['rx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_count
        status_temp['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_bytes
        status_temp['rx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_bps
        status_temp['tx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_count
        status_temp['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_bytes
        status_temp['tx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_bps
        status_temp['tx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_pdu_count
        status_temp['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().tx_rlc_pdu_bytes

        status['rx_wrong_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_wrong_mac_pdu_count'])
        status['rx_wrong_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_wrong_mac_pdu_bytes'])
        status['rx_right_mac_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_count'])
        status['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_bytes'])
        status['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_bps'])
        status['rx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_count'])
        status['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_bytes'])
        status['rx_rlc_pdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_bps'])
        status['rx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_count'])
        status['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_bytes'])
        status['rx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_bps'])
        status['tx_rlc_sdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_count'])
        status['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_bytes'])
        status['tx_rlc_sdu_bps'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_bps'])
        status['tx_rlc_pdu_count'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_pdu_count'])
        status['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_pdu_bytes'])
        status['rx_sr_num'] = self.lte_sat_layer2_0.get_stat_info().rx_sr_num
        status['rx_bsr_num'] = self.lte_sat_layer2_0.get_stat_info().rx_bsr_num
        # status['stat_info_0'] = self.lte_sat_layer2_0.get_stat_string(0)
        # status['stat_info_1'] = self.lte_sat_layer2_0.get_stat_string(1)
        status['ip'] = self.ip
        status['route'] = self.route
        status['u_freq'] = self.u_center_freq
        status['d_freq'] = self.d_center_freq

        return status

class dl_ber_test_send(gr.top_block):

    def __init__(self,**param):
        gr.top_block.__init__(self, "Dl Ber Test Send")

        print 'dl_ber_test_send'
        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 2000000
        self.prbl = prbl = 6
        self.fftl = fftl = 128

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(2.0e7, 0)
        self.uhd_usrp_sink_0.set_gain(10, 0)
        self.lte_sat_dl_subframe_mapper_0_0 = lte_sat.dl_subframe_mapper(prbl,
            10
           )
        self.lte_sat_dl_baseband_generator_0 = lte_sat.dl_baseband_generator(prbl, fftl, "addr=192.168.10.2")
        self.lte_sat_DL_mac_0 = lte_sat.DL_mac(100,prbl,10,2,1,0.4)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_char*1)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.lte_sat_DL_mac_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.lte_sat_dl_baseband_generator_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.lte_sat_dl_subframe_mapper_0_0, 0), (self.lte_sat_dl_baseband_generator_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.lte_sat_DL_mac_0, "sched_info", self.lte_sat_dl_subframe_mapper_0_0, "sched_info")

    # QT sink close method reimplementation
    def get_status(self):
        status = {}
        return status

class dl_test(gr.top_block):
    def __init__(self,**param):
        gr.top_block.__init__(self, "Dl Test")
        ##################################################
        # Variables
        ##################################################
        try:
            if param['Bandwidth'] == '1.4':
                self.prbl = prbl = 6
                self.fftl = fftl = 128
                self.multiply_const = multiply_const = 128.0
            else:
                self.prbl = prbl = 15
                self.fftl = fftl = 256
                self.multiply_const = multiply_const = 256.0

            if param['samp_rate_G'] == '2M':
                self.samp_rate = samp_rate = 2000000
            else:
                self.samp_rate = samp_rate = 4000000 
            self.sacle = sacle = 1024
            self.gain_s = gain_s = int(param['gain_s_G'])
            self.cell_id = cell_id = int(param['id_cell'])

            if param['mod_type_d'] == '16QAM':
                self.dl_mod_type = dl_mod_type = 2
            else:
                self.dl_mod_type = dl_mod_type = 1
            if param['mod_type_u'] == '16QAM':
                self.ul_mod_type = ul_mod_type = 2
            else:
                self.ul_mod_type = ul_mod_type = 1                
            self.dl_rate = dl_rate = float(param['exp_code_rate_d_G'])
            self.ul_rate = ul_rate = float(param['exp_code_rate_u_G'])

        except: print '变量初始化失败'

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(160e6, 0)
        self.uhd_usrp_sink_0.set_gain(gain_s, 0)
        self.rational_resampler_xxx_0_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=24,
                taps=None,
                fractional_bw=None,
        )

        self.lte_sat_layer2_0 = lte_sat.layer2(cell_id,prbl,dl_mod_type,dl_rate,ul_mod_type,ul_rate)
        # self.lte_sat_layer2_0 = lte_sat.layer2(10,prbl,2,0.4,2,0.4)
        self.lte_sat_layer2_0.create_logic_channel(61, 10, lte_sat.mode_um)
        
        self.lte_sat_dl_subframe_mapper_0_0 = lte_sat.dl_subframe_mapper(prbl,cell_id)
        self.lte_sat_dl_baseband_generator_0 = lte_sat.dl_baseband_generator(prbl, fftl)
        self.blocks_tagged_stream_to_pdu_0_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, "packet_len")
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, "packet_len")
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 1000, "packet_len")
        self.blocks_pdu_to_tagged_stream_0_0_1 = blocks.pdu_to_tagged_stream(blocks.byte_t, "packet_len")
        self.blocks_null_source_0 = blocks.null_source(gr.sizeof_char*1)
        self.blocks_null_sink_0_1 = blocks.null_sink(gr.sizeof_char*1)
        self.blocks_float_to_char_0 = blocks.float_to_char(1, sacle)
        self.audio_source_0 = audio.source(48000, "", True)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.lte_sat_dl_subframe_mapper_0_0, 0), (self.lte_sat_dl_baseband_generator_0, 0))
        self.connect((self.blocks_null_source_0, 0), (self.blocks_tagged_stream_to_pdu_0_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0_0_1, 0), (self.blocks_null_sink_0_1, 0))
        self.connect((self.lte_sat_dl_baseband_generator_0, 0), (self.rational_resampler_xxx_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_null_source_0, 0), (self.lte_sat_layer2_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect((self.audio_source_0, 0), (self.blocks_float_to_char_0, 0))
        self.connect((self.blocks_float_to_char_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.blocks_tagged_stream_to_pdu_0_0, "pdus", self.lte_sat_dl_subframe_mapper_0_0, "sched_info")
        self.msg_connect(self.blocks_tagged_stream_to_pdu_0_0, "pdus", self.lte_sat_layer2_0, "sr_ta")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_dl_subframe_mapper_0_0, "sched_info")
        self.msg_connect(self.blocks_tagged_stream_to_pdu_0, "pdus", self.lte_sat_layer2_0, "tx_data")
        self.msg_connect(self.lte_sat_layer2_0, "rx_data", self.blocks_pdu_to_tagged_stream_0_0_1, "pdus")

    def get_status(self):
        status = {}
        status['cell_id'] = self.lte_sat_dl_baseband_sync_0.get_cell_id()
        status['prbl'] = self.lte_sat_dl_baseband_sync_0.get_prbl()
        status['pss_status'] = self.lte_sat_dl_baseband_sync_0.get_pss_status()
        status['sss_status'] = self.lte_sat_dl_baseband_sync_0.get_sss_status()
        status['pbch_status'] = self.lte_sat_dl_baseband_sync_0.get_pbch_status()
        status['process_state'] = self.lte_sat_dl_baseband_sync_0.get_process_state()
        status['cfo'] = self.lte_sat_dl_baseband_sync_0.get_cfo()
        status['fte'] = self.lte_sat_dl_baseband_sync_0.get_fte()
        status['pss_pos'] = self.lte_sat_dl_baseband_sync_0.get_pss_pos()

        status['fn'] = self.lte_sat_dl_subframe_demapper_0.get_fn()
        status['sfn'] = self.lte_sat_dl_subframe_demapper_0.get_sfn()
        status['fer'] = self.lte_sat_dl_subframe_demapper_0.get_fer()

        status['pdu_sum'] = self.lte_sat_layer2_ue_0.get_mac_pdu_sum()
        return status                

class eNB_ping_15prb_one61(gr.top_block):

    def __init__(self,**param):
        # grc_wxgui.top_block_gui.__init__(self, title="Enb Ping 15Prb One61")
        gr.top_block.__init__(self, "Enb Ping 15Prb One61")

        ##################################################
        # Variables
        ##################################################
        try:
            if param['Bandwidth'] == '1.4':
                self.prbl = prbl = 6
                self.fftl = fftl = 128
            else:
                self.prbl = prbl = 15
                self.fftl = fftl = 256

            if param['mod_type_d'] == '16QAM':
                self.dl_mod_type = dl_mod_type = 2
            else:
                self.dl_mod_type = dl_mod_type = 1
            if param['mod_type_u'] == '16QAM':
                self.ul_mod_type = ul_mod_type = 2
            else:
                self.ul_mod_type = ul_mod_type = 1                
            self.dl_rate = dl_rate = float(param['exp_code_rate_d_G'])
            self.ul_rate = ul_rate = float(param['exp_code_rate_u_G'])
            self.cell_id = cell_id = int(param['id_cell'])          
            self.samp_rate = samp_rate = 4e6
            self.mod_type = mod_type = 1
            # self.fftl = fftl = 256
            # self.prbl = prbl = 15            
        except: print '变量初始化失败'

        print prbl,fftl,dl_mod_type,ul_mod_type,dl_rate,ul_rate,cell_id
        # 15 256 2 2 0.45 0.45 10

        self.variable_ul_para_0 = variable_ul_para_0 = lte_sat.ul_parameter(61, prbl)
        self.variable_ul_para_0.set_cch_period(10, 2)
        self.variable_ul_para_0.set_srs_period(10, 0)
        self.variable_ul_para_0.set_sch_params(4, 2)

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	device_addr="addr=192.168.10.2",
        	stream_args=uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(800e6, 0)
        self.uhd_usrp_source_0.set_gain(10, 0)
        self.uhd_usrp_source_0.set_bandwidth(4e6, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	device_addr="addr=192.168.10.2",
        	stream_args=uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(900e6, 0)
        self.uhd_usrp_sink_0.set_gain(10, 0)
        self.uhd_usrp_sink_0.set_bandwidth(4e6, 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=24,
                taps=None,
                fractional_bw=None,
        )
        # int N_cell_id, int N_ul_rb
        self.lte_sat_ul_subframe_demapper_0 = lte_sat.ul_subframe_demapper(10,prbl)
        # int prbl, int fftl, int cell_id, float srs_threshold = 0.7, bool ul_test_only = false
        self.lte_sat_ul_baseband_sync_0 = lte_sat.ul_baseband_sync(prbl,fftl,10,0.5,False)
        # int cell_id,prbl,dl_mod_type,float dl_rate,ul_mod_type,ul_rate
        self.lte_sat_layer2_0 = lte_sat.layer2(10,prbl,mod_type,0.4,mod_type,0.4)
        self.lte_sat_layer2_0.create_logic_channel(61, 10, lte_sat.mode_um)
        
        # with_usrp 是否为测试模式
        self.lte_sat_eNB_config_0 = lte_sat.eNB_entity_config(False)
        self.lte_sat_eNB_config_0.set_leading_sched_b4_mapping(2, 5)
        self.lte_sat_eNB_config_0.set_leading_map_b4_sending(15)
        self.lte_sat_eNB_config_0.set_delay_sfc_for_pusch_after_usg(20)
        self.lte_sat_eNB_config_0.add_ul_param(variable_ul_para_0)
        
        # uint32 N_rb_dl, uint32 N_cell_id
        self.lte_sat_dl_subframe_mapper_0_0 = lte_sat.dl_subframe_mapper(prbl,10)
        # uint32 N_rb_dl, uint32 fft_size
        self.lte_sat_dl_baseband_generator_0 = lte_sat.dl_baseband_generator(prbl, fftl)
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu("tun0", 100000)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.lte_sat_ul_baseband_sync_0, 0), (self.lte_sat_ul_subframe_demapper_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.lte_sat_ul_baseband_sync_0, 0))
        self.connect((self.lte_sat_ul_subframe_demapper_0, 0), (self.lte_sat_layer2_0, 0))
        self.connect((self.lte_sat_dl_baseband_generator_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.lte_sat_dl_subframe_mapper_0_0, 0), (self.lte_sat_dl_baseband_generator_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.lte_sat_ul_baseband_sync_0, "TA_info", self.lte_sat_ul_subframe_demapper_0, "TA_inf")
        self.msg_connect(self.blocks_tuntap_pdu_0, "pdus", self.lte_sat_layer2_0, "tx_data")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_ul_subframe_demapper_0, "sched_for_ul")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_ul_baseband_sync_0, "sched_for_ul")
        self.msg_connect(self.lte_sat_ul_subframe_demapper_0, "sr_ta", self.lte_sat_layer2_0, "sr_ta")
        self.msg_connect(self.lte_sat_layer2_0, "sched_info", self.lte_sat_dl_subframe_mapper_0_0, "sched_info")
        self.msg_connect(self.lte_sat_layer2_0, "rx_data", self.blocks_tuntap_pdu_0, "pdus")

class PanelOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.state = ['Red']
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.SetBrush(wx.Brush(self.state[0]))
        dc.DrawCircle(8, 8, 8)

    def state_green(self):
        self.state=['green']
        self.Refresh()
    def state_red(self):
        self.state=['red']
        self.Refresh()

class Detail_Dialog(wx.Frame):

    def __init__(self,parent):
        wx.Frame.__init__(self, None, title=u'详细显示界面',
                          size=(760,600))
        self.Centre()
        self.parent = parent

        #创建面板
        self.DetailPanel()
        Publisher().subscribe(self.updateDisplay, "update")

    def DetailPanel(self):
        self.update_button = wx.Button(self, -1, u"更新")
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.update_button)

        list_variable = ['rx_wrong_mac_pdu_count',
        'rx_wrong_mac_pdu_bytes',
        'rx_right_mac_pdu_count',
        'rx_right_mac_pdu_bytes',
        'rx_right_mac_pdu_bps',
        'rx_rlc_pdu_count',
        'rx_rlc_pdu_bytes',
        'rx_rlc_pdu_bps',
        'rx_rlc_sdu_count',
        'rx_rlc_sdu_bytes',
        'rx_rlc_sdu_bps',
        'tx_rlc_sdu_count',
        'tx_rlc_sdu_bytes',
        'tx_rlc_sdu_bps',
        'rx_sr_num',
        'rx_bsr_num',
        'tx_rlc_pdu_count',
        'tx_rlc_pdu_bytes']

        list_meaning = ['RX CRC错误总包数',
        'RX CRC错误字节数',
        'RX CRC正确总包数',
        'RX CRC正确字节数',
        '',
        'MAC==>RLC总包数',
        'MAC==>RLC字节数',
        '',
        'RLC==>高层总包数',
        'RLC==>高层字节数',
        '',
        'TX 高层==>RLC总包数',
        'TX 高层==>RLC字节数',
        '',
        'eNB检测到的SR数',
        'eNB检测到的BSR数',
        'TX RLC==>MAC总包数',
        'TX RLC==>MAC字节数'
        ]

        colLabels = ['名称','值','含义']

        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(len(list_variable),len(colLabels))

        attr1 = wx.grid.GridCellAttr()
        attr1.SetReadOnly(True)
        for row in range(4):
            self.grid.SetColAttr(row+1, attr1)

        attr2 = wx.grid.GridCellAttr()
        attr2.SetReadOnly(True)
        attr2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        # attr2.SetTextColour("navyblue")
        # attr2.SetBackgroundColour("pink")
        self.grid.SetColAttr(0, attr2)

        self.grid.SetColSize(0, 100)
        self.grid.SetColSize(1, 150)
        self.grid.SetColSize(2, 320)


        for row in range(len(colLabels)):
            self.grid.SetColLabelValue(row, colLabels[row])

        for row in range(len(list_variable)):
            self.grid.SetCellValue(row, 1, list_variable[row])

        # for row in range(len(list_value)):
        #     self.grid.SetCellValue(row, 1, str(list_value[row]))

        for row in range(len(list_meaning)):
            self.grid.SetCellValue(row, 3, list_meaning[row])

        # num_list = [0,1,2,5,6,36,37,38,39]
        num_list = range(len(list_variable))
        for num in num_list:
            self.grid.SetRowSize(num, 40)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add((20,20), 0)
        sizer1.Add(self.grid, 0, wx.ALIGN_RIGHT)
        sizer1.Add(self.update_button, 0, wx.ALIGN_RIGHT)

        self.SetSizer(sizer1)
        self.Fit()

    def OnConnect(self,event):
        list_value = [1,1,1,1,'ff','ll']
        for row in range(len(list_value)):
            self.grid.SetCellValue(row, 1, str(list_value[row]))

    def updateDisplay(self, msg):
        """
        从线程接收数据并且在界面更新显示
        """
        dict_status = msg.data

        list_value = [dict_status['rx_wrong_mac_pdu_count']+' packet',
        dict_status['rx_wrong_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_count']+' packet',
        dict_status['rx_right_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_bps'],
        dict_status['rx_rlc_pdu_count']+' packet',
        dict_status['rx_rlc_pdu_bytes']+' bytes',
        dict_status['rx_rlc_pdu_bps'],
        dict_status['rx_rlc_sdu_count']+' packet',
        dict_status['rx_rlc_sdu_bytes']+' bytes',
        dict_status['rx_rlc_sdu_bps'],
        dict_status['tx_rlc_sdu_count']+' packet',
        dict_status['tx_rlc_sdu_bytes']+' bytes',
        dict_status['tx_rlc_sdu_bps'],
        dict_status['rx_sr_num'],
        dict_status['rx_bsr_num'],
        dict_status['tx_rlc_pdu_count']+' packet',
        dict_status['tx_rlc_pdu_bytes']+' bytes']

        for row in range(len(list_value)):
            self.grid.SetCellValue(row, 1, str(list_value[row]))

class Detail_Dialog_SP(wx.Panel):

    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.Centre()
        self.parent = parent

        #创建面板
        self.DetailPanel()
        Publisher().subscribe(self.updateDisplay, "update")

    def DetailPanel(self):
        self.update_button = wx.Button(self, -1, u"更新")
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.update_button)

        list_variable = ['rx_wrong_mac_pdu_count',
        'rx_wrong_mac_pdu_bytes',
        'rx_right_mac_pdu_count',
        'rx_right_mac_pdu_bytes',
        'rx_right_mac_pdu_bps',
        'rx_rlc_pdu_count',
        'rx_rlc_pdu_bytes',
        'rx_rlc_pdu_bps',
        'rx_rlc_sdu_count',
        'rx_rlc_sdu_bytes',
        'rx_rlc_sdu_bps',
        'tx_rlc_sdu_count',
        'tx_rlc_sdu_bytes',
        'tx_rlc_sdu_bps',
        'rx_sr_num',
        'rx_bsr_num',
        'tx_rlc_pdu_count',
        'tx_rlc_pdu_bytes']

        list_meaning = ['RX CRC错误总包数',
        'RX CRC错误字节数',
        'RX CRC正确总包数',
        'RX CRC正确字节数',
        '',
        'MAC==>RLC总包数',
        'MAC==>RLC字节数',
        '',
        'RLC==>高层总包数',
        'RLC==>高层字节数',
        '',
        'TX 高层==>RLC总包数',
        'TX 高层==>RLC字节数',
        '',
        'eNB检测到的SR数',
        'eNB检测到的BSR数',
        'TX RLC==>MAC总包数',
        'TX RLC==>MAC字节数'
        ]

        colLabels = ['名称','值','含义']

        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(len(list_variable),len(colLabels))

        attr1 = wx.grid.GridCellAttr()
        attr1.SetReadOnly(True)
        for row in range(4):
            self.grid.SetColAttr(row+1, attr1)

        attr2 = wx.grid.GridCellAttr()
        attr2.SetReadOnly(True)
        attr2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        # attr2.SetTextColour("navyblue")
        # attr2.SetBackgroundColour("pink")
        self.grid.SetColAttr(0, attr2)

        self.grid.SetColSize(0, 100)
        self.grid.SetColSize(1, 150)
        self.grid.SetColSize(2, 320)


        for row in range(len(colLabels)):
            self.grid.SetColLabelValue(row, colLabels[row])

        for row in range(len(list_variable)):
            self.grid.SetCellValue(row, 1, list_variable[row])

        # for row in range(len(list_value)):
        #     self.grid.SetCellValue(row, 1, str(list_value[row]))

        for row in range(len(list_meaning)):
            self.grid.SetCellValue(row, 3, list_meaning[row])

        # num_list = [0,1,2,5,6,36,37,38,39]
        num_list = range(len(list_variable))
        for num in num_list:
            self.grid.SetRowSize(num, 40)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add((20,20), 0)
        sizer1.Add(self.grid, 0, wx.ALIGN_RIGHT)
        sizer1.Add(self.update_button, 0, wx.ALIGN_RIGHT)

        self.SetSizer(sizer1)
        self.Fit()

    def OnConnect(self,event):
        list_value = [1,1,1,1,'ff','ll']
        for row in range(len(list_value)):
            self.grid.SetCellValue(row, 1, str(list_value[row]))

    def updateDisplay(self, msg):
        """
        从线程接收数据并且在界面更新显示
        """
        dict_status = msg.data

        list_value = [dict_status['rx_wrong_mac_pdu_count']+' packet',
        dict_status['rx_wrong_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_count']+' packet',
        dict_status['rx_right_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_bps'],
        dict_status['rx_rlc_pdu_count']+' packet',
        dict_status['rx_rlc_pdu_bytes']+' bytes',
        dict_status['rx_rlc_pdu_bps'],
        dict_status['rx_rlc_sdu_count']+' packet',
        dict_status['rx_rlc_sdu_bytes']+' bytes',
        dict_status['rx_rlc_sdu_bps'],
        dict_status['tx_rlc_sdu_count']+' packet',
        dict_status['tx_rlc_sdu_bytes']+' bytes',
        dict_status['tx_rlc_sdu_bps'],
        dict_status['rx_sr_num'],
        dict_status['rx_bsr_num'],
        dict_status['tx_rlc_pdu_count']+' packet',
        dict_status['tx_rlc_pdu_bytes']+' bytes']

        for row in range(len(list_value)):
            self.grid.SetCellValue(row, 1, str(list_value[row]))            

class MainFrame(wx.Frame):
    def __init__(self,parent,id):
        # wx.Frame.__init__(self, None, title=u"信关站界面", size=(580,700))
        wx.Frame.__init__(self, None, title=u"信关站界面", size=(1000,780))
        self.Centre()
        # self.SetBackgroundColour("white")

        # self.sp = wx.SplitterWindow(self)
        self.panel = wx.Panel(self, style=wx.SP_3D)
        # self.p1 = Detail_Dialog_SP(self.sp)
        # self.sp.SplitVertically(self.panel,self.p1,400)

        self.panel.SetBackgroundColour("white")

        self.gateway_config = ConfigParser.ConfigParser()
        self.gateway_config.read("gateway.conf")
        
        #创建面板
        self.createframe()

        # 创建一个pubsub接收器,用于接收从子线程传递过来的消息
        Publisher().subscribe(self.updateDisplay, "update")
    
    def updateDisplay(self, msg): 
        """
        从线程接收数据并且在界面更新显示
        """
        dict_status = msg.data
        # print str(dict_status['stat_info'])

        self.DisplayText.Clear()
        # self.virtual_ip_t.SetValue(str(dict_status['ip']))
        self.virtual_ip_t.SetLabel(str(dict_status['ip']))
        # self.select_route_t.SetValue(str(dict_status['route']))
        self.select_route_t.SetLabel(str(dict_status['route']))
        # self.DisplayText.AppendText(str(dict_status['stat_info_0']))
        # self.DisplayText.AppendText(str(dict_status['stat_info_1']))
        list_value = [dict_status['rx_wrong_mac_pdu_count']+' packet',
        dict_status['rx_wrong_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_count']+' packet',
        dict_status['rx_right_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_bps'],
        dict_status['rx_rlc_pdu_count']+' packet',
        dict_status['rx_rlc_pdu_bytes']+' bytes',
        dict_status['rx_rlc_pdu_bps'],
        dict_status['rx_rlc_sdu_count']+' packet',
        dict_status['rx_rlc_sdu_bytes']+' bytes',
        dict_status['rx_rlc_sdu_bps'],
        dict_status['tx_rlc_sdu_count']+' packet',
        dict_status['tx_rlc_sdu_bytes']+' bytes',
        dict_status['tx_rlc_sdu_bps'],
        dict_status['rx_sr_num'],
        dict_status['rx_bsr_num'],
        dict_status['tx_rlc_pdu_count']+' packet',
        dict_status['tx_rlc_pdu_bytes']+' bytes']

        for row in range(len(list_value)):
            self.grid.SetCellValue(row, 2, str(list_value[row]))        

    def createframe(self):

        #绑定窗口的关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        self.DisplayText = wx.TextCtrl(self.panel, -1, '', size=(100,250), style=wx.TE_MULTILINE | wx.TE_READONLY) 
        self.DisplayText.SetBackgroundColour('gray')

        #虚拟ip地址
        virtual_ip = wx.StaticText(self.panel, -1, u"虚拟ip地址:")
        # self.virtual_ip_t = wx.TextCtrl(self.panel, -1, "192.168.200.11", style=wx.TE_READONLY)
        self.virtual_ip_t = wx.StaticText(self.panel, -1, '192.168.200.11')

        #选择路由
        select_route = wx.StaticText(self.panel, -1, u"选择路由:")
        # self.select_route_t = wx.TextCtrl(self.panel, -1, "192.168.200.3", style=wx.TE_READONLY)
        self.select_route_t = wx.StaticText(self.panel, -1, '192.168.200.3')

        # 上下行中心频率
        u_frequency_st = wx.StaticText(self.panel, -1, u"上行中心频率(MHz):")
        # self.u_frequency = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.u_frequency = wx.StaticText(self.panel, -1, '0')
        d_frequency_st = wx.StaticText(self.panel, -1, u"下行中心频率(MHz):")
        self.d_frequency = wx.StaticText(self.panel, -1, '0')

        #详细显示按钮
        self.detail_button = wx.Button(self.panel, -1, u"详细显示")
        self.detail_button.SetBackgroundColour('black')
        self.detail_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Detail,self.detail_button)

        #连接按钮
        self.connect_button = wx.Button(self.panel, -1, u"连接")
        self.connect_button.SetBackgroundColour('black')
        self.connect_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)  
        # self.connect_button.SetDefault() 

        #设置连接服务器的IP地址和端口号
        self.gateway_config.read("gateway.conf")
        try: s_ip = self.gateway_config.get("address", "s_ip")
        except: s_ip = '192.168.139.180'

        try: s_port = self.gateway_config.get("address", "s_port")
        except: s_port = '7000'

        ip_st = wx.StaticText(self.panel, -1, u"IP地址 :")
        self.IPText = wx.TextCtrl(self.panel, -1, s_ip)
        port_st = wx.StaticText(self.panel, -1, u"端口号 :")  
        self.PortText = wx.TextCtrl(self.panel, -1, s_port)

        list_variable = ['rx_wrong_mac_pdu_count',
        'rx_wrong_mac_pdu_bytes',
        'rx_right_mac_pdu_count',
        'rx_right_mac_pdu_bytes',
        'rx_right_mac_pdu_bps',
        'rx_rlc_pdu_count',
        'rx_rlc_pdu_bytes',
        'rx_rlc_pdu_bps',
        'rx_rlc_sdu_count',
        'rx_rlc_sdu_bytes',
        'rx_rlc_sdu_bps',
        'tx_rlc_sdu_count',
        'tx_rlc_sdu_bytes',
        'tx_rlc_sdu_bps',
        'rx_sr_num',
        'rx_bsr_num',
        'tx_rlc_pdu_count',
        'tx_rlc_pdu_bytes']

        list_meaning = ['RX CRC错误总包数',
        'RX CRC错误字节数',
        'RX CRC正确总包数',
        'RX CRC正确字节数',
        '',
        'MAC==>RLC总包数',
        'MAC==>RLC字节数',
        '',
        'RLC==>高层总包数',
        'RLC==>高层字节数',
        '',
        'TX 高层==>RLC总包数',
        'TX 高层==>RLC字节数',
        '',
        'eNB检测到的SR数',
        'eNB检测到的BSR数',
        'TX RLC==>MAC总包数',
        'TX RLC==>MAC字节数'
        ]

        colLabels = ['层面','名称','值']#,'含义']


        self.grid = wx.grid.Grid(self.panel)
        self.grid.CreateGrid(len(list_variable),len(colLabels))

        attr1 = wx.grid.GridCellAttr()
        attr1.SetReadOnly(True)
        for row in range(4):
            self.grid.SetColAttr(row+1, attr1)

        attr2 = wx.grid.GridCellAttr()
        attr2.SetReadOnly(True)
        attr2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        # attr2.SetTextColour("navyblue")
        # attr2.SetBackgroundColour("pink")
        self.grid.SetColAttr(0, attr2)

        self.grid.SetCellSize(0, 0, 5, 1)
        self.grid.SetCellSize(5, 0, 13, 1)

        self.grid.SetCellValue(0, 0, "\n\n\n\n\nMAC")
        self.grid.SetCellValue(5, 0, "\n\n\n\n\n\n\n\n\n\nRLC")

        self.grid.SetColSize(0, 100)
        self.grid.SetColSize(1, 150)
        self.grid.SetColSize(2, 150)


        for row in range(len(colLabels)):
            self.grid.SetColLabelValue(row, colLabels[row])

        for row in range(len(list_meaning)):
            self.grid.SetCellValue(row, 1, list_meaning[row])

        # for row in range(len(list_value)):
        #     self.grid.SetCellValue(row, 1, str(list_value[row]))

        for row in range(len(list_meaning)):
            self.grid.SetCellValue(row, 3, list_meaning[row])

        # num_list = [0,1,2,5,6,36,37,38,39]
        num_list = range(len(list_variable))
        for num in num_list:
            self.grid.SetRowSize(num, 40)

        ###########开始布局############
        sizer1 = wx.FlexGridSizer(cols=4, hgap=10, vgap=10)
        sizer1.AddGrowableCol(1)
        sizer1.AddGrowableCol(3)
        sizer1.Add(virtual_ip, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.virtual_ip_t, 0, wx.EXPAND)
        sizer1.Add(u_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.u_frequency, 0, wx.EXPAND)
        sizer1.Add(select_route, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.select_route_t, 0, wx.EXPAND)
        sizer1.Add(d_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.d_frequency, 0, wx.EXPAND)        

        #详细显示按钮
        sizer_detail = wx.BoxSizer(wx.HORIZONTAL)
        sizer_detail.Add((10,10), 1)
        sizer_detail.Add(self.detail_button, 0, wx.ALIGN_RIGHT)

        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'状态显示'), wx.VERTICAL)
        sizer2.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)
        sizer2.Add(self.DisplayText, 0, wx.EXPAND | wx.ALL, 10)
        sizer2.Add(sizer_detail, 0, wx.EXPAND | wx.ALL, 10)

        sizer3 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer3.AddGrowableCol(1)
        sizer3.Add(ip_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.IPText, 3, wx.EXPAND)
        sizer3.Add(port_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.PortText, 1, wx.EXPAND)

        #连接按钮
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add((20,20), 1)
        sizer4.Add(self.connect_button, 0, wx.ALIGN_RIGHT)

        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'连接服务器'), wx.VERTICAL)
        sizer5.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)
        sizer5.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL, 25)
        # box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)
        box1.Add(sizer5,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 25)

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(self.grid,0,wx.EXPAND | wx.ALL, 10)
        box2.Add(box1,0,wx.EXPAND | wx.ALL, 10)

        # 自动调整界面尺寸
        self.panel.SetSizer(box2)

    def Detail(self,event):
        self.detail_dlg = Detail_Dialog(None)
        self.detail_dlg.Bind(wx.EVT_CLOSE, self.OnCloseWindowDetail)
        self.detail_dlg.Show()
        self.detail_button.Disable()

    def OnCloseWindowDetail(self,event):
        self.detail_button.Enable()
        self.detail_dlg.Destroy()

    def OnConnect(self, event):
        self.IPText.Disable()
        self.PortText.Disable()
        self.connect_button.Disable()
        self.gateway_config.read("gateway.conf")
        if "address" not in self.gateway_config.sections():
            self.gateway_config.add_section("address")

        #address
        self.gateway_config.set("address", "s_ip", self.IPText.GetValue())
        self.gateway_config.set("address", "s_port", self.PortText.GetValue())

        #写入配置文件
        param_file = open("gateway.conf","w")
        self.gateway_config.write(param_file)
        param_file.close()

        self.port = int(self.PortText.GetValue())  
        self.host = str(self.IPText.GetValue()) 
        self.t_gateway = threading.Thread(target = self.client_gateway,args = (self.host,self.port))
        self.t_gateway.setDaemon(True)
        self.t_gateway.start()

    def client_gateway(self,host,port):
        self.host = host
        self.port = port 

        self.status = {}
        self.status['gateway'] = "true"

        self.t2 = threading.Thread(target = self.start_monitor_for_panel)
        self.t2.setDaemon(True)
        self.t2.start()

        self.start_client()

    def start_client(self):
        server_address = (self.host,self.port)
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.client.connect(server_address)
        except:
            self.dlg = wx.MessageDialog(self,'\n请确认是否成功连接至服务器','警告',wx.ICON_ERROR)
            self.dlg.ShowModal()
            self.IPText.Enable()
            self.PortText.Enable()
            self.connect_button.Enable()

        self.t3 = threading.Thread(target = self.start_monitor)
        self.t3.setDaemon(True)
        self.t3.start()

        # self.client.send('data_status')
        # 读socket
        self.inputs = [ self.client ]

        # 写socket
        outputs = []

        # 消息队列
        self.message_queues = {}

        while self.inputs:
            readable, writable, exceptional = select.select(self.inputs, outputs, self.inputs)  
              
            #处理input
            for s in readable:  
                try:
                	data = s.recv(4096) 
                except:
                	print '输入正确的IP地址和端口号'
                	sys.exit()

                if data: 
                    if data == 'start_block':
                        self.q = Queue()
                        self.p1 = multiprocessing.Process(name='start_top_block',
                                target=self.start_top_block)
                        self.p1.daemon = True
                        self.p1.start()
                    elif data == 'stop_block':
                        self.stop_top_block() 
                    else:
                        global param 
                        # print data  
                        param = json.loads(data)
                        print param
                        # A readable client socket has data  
                        print 'received param from ', s.getpeername() 
                        try:
                            if self.p1.is_alive():
                                # GNURadio模块运行过程中修改参数
                                self.threshold = float(param['Threshold'])
                                # self.tb.set_threshold(self.threshold)
                                self.q.put(self.threshold)
                        except:pass

                else:  
                    print 'closing after reading no data'
                    if s in outputs:
                        outputs.remove(s)  
                    self.inputs.remove(s)
                    s.close()  
                    # Remove message queue  
                    del self.message_queues[s]

            # Handle outputs  
            for s in writable:  
                try:  
                    next_msg = self.message_queues[s].get_nowait()  
                except Queue.Empty:  
                    # No messages waiting so stop checking for writability.  
                    print 'output queue for', s.getpeername(), 'is empty'  
                    outputs.remove(s)  
                else:  
                    print 'sending "%s" to %s' % (next_msg, s.getpeername())  
                    s.send(next_msg)  
            # Handle "exceptional conditions"  
            for s in exceptional:
                print 'handling exceptional condition for', s.getpeername()    
                # Stop listening for input on the connection  
                self.inputs.remove(s)  
                if s in outputs:  
                    outputs.remove(s)  
                s.close()  
                # Remove message queue  
                del self.message_queues[s]   
    
    # start_monitor函数的代码有两个作用，一个是通过callafter函数向gateway界面传递状态信息，
    # 另一个是通过socket.client向控制界面传递状态信息。
    def start_monitor_for_panel(self): 
        while True:
            try:
                if self.p1.is_alive():
                    # print 'self.p1...alive'
                    self.status.update(self.q.get())
                    wx.CallAfter(Publisher().sendMessage, "update", self.status)
            
            except:pass
                # print 'self.p1...dead'
            time.sleep(1)

    def start_monitor(self):
        while True:
            data_status = json.dumps(self.status)
            try:
            	self.client.send(data_status)
            except:
                print '连接尚未建立!请核对IP地址和端口号,重新建立连接'
                sys.exit()

            time.sleep(1)
            if self.status.has_key('gateway'):
                del self.status['gateway']

    #子进程
    def start_top_block(self):
        global param 
        os.system('rm -rvf *.log *.dat *.test')
        os.system('uhd_usrp_probe')
        if param['work_mod'] == '1':
            # self.tb = eNB_ping(**param)
            # self.tb = dl_test(**param)
            self.tb = eNB_ping_15prb_one65_audio(**param)
            # os.system('sudo ifconfig tun0 192.168.200.3')
            # os.system('sudo route add 192.168.200.12 dev tun0')
        elif param['work_mod'] == '0':
            self.tb = dl_ber_test_send(**param)
        elif param['work_mod'] == '2':
            self.tb = eNB_ping_15prb_one65_video(**param)
            os.system('sudo ifconfig tun0 192.168.200.3')
            # os.system('sudo route add default metric 10 dev tun0')
            os.system('sudo route add 192.168.200.12 dev tun0')

            # self.p_stream = multiprocessing.Process(name='start_streaming',
            #     target=self.start_streaming)
            self.p_stream = threading.Thread(target=self.start_streaming)
            self.p_stream.daemon = True
            self.p_stream.start()

        self.t1 = threading.Thread(target = self.monitor_forever)
        self.t1.setDaemon(True)
        self.t1.start()

        self.tb.start()
        # os.system('sudo ifconfig tun0 192.168.200.3')
        # os.system('sudo route add 192.168.200.11 dev tun0')
        self.tb.wait()

    def monitor_forever(self):
        
        while True:
            # 从控制界面获取参数，动态改变
            # self.tb.set_threshold(self.q.get())

            # 获取Gnuradio模块中的状态信息，传递至界面

            self.q.put(self.tb.get_status())

            time.sleep(1)

    def stop_top_block(self):
        self.p1.terminate()
        # self.p_stream.terminate()
        self.virtual_ip_t.SetValue('192.168.200.11')
        self.select_route_t.SetValue('192.168.200.3')
        print 'stop'

    def OnCloseWindow(self, event):
        # try:
        #     self.status['gateway']="false"
        #     data_status = json.dumps(self.status)
        #     self.client.send(data_status)
        #     self.client.close() 
        #     self.Destroy()
        # except:
        try:
            self.Destroy()
            if isinstance(self.detail_dlg,Detail_Dialog) == True:
                self.detail_dlg.Destroy()
        except:
            self.Destroy()

    def start_streaming(self):
        str_streming = "vlc -vvv file:///home/lh/Bunny_HD_15Mbps.h264 --sout '#transcode{vcodec=h264,vb=0,scale=0,acodec=none}:duplicate{dst=rtp{dst=127.0.0.1,port=5004,mux=ts,ttl=1},dst=display}'"
        # os.system(str_streming)
        print str_streming

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(parent=None, id=-1)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

if __name__ == "__main__":
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"
    app = MyApp()
    app.MainLoop()
