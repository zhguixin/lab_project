#!/usr/bin/env python
#coding=utf-8
#################################
#   Copyright 2014.6.23
#       fly_vedio 
#   @author: zhguixin@163.com
#################################
from gnuradio import audio
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio import filter
from gnuradio import vocoder
from gnuradio.eng_option import eng_option
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
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

from matplotlib.widgets import SpanSelector

#设置系统默认编码方式，不用下面两句，中文会乱码
reload(sys)
sys.setdefaultencoding("utf-8")

param = {}
test_data = ()

class ue65_ping_15prb_video(gr.top_block):

    def __init__(self,**param):
        gr.top_block.__init__(self, "Ue65 Ping 15Prb Video")

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

            if param['samp_rate_T'] == '2M':
                self.samp_rate = samp_rate = 2e6 #2000000
            else:
                self.samp_rate = samp_rate = 4e6 #4000000 

            self.threshold = threshold = float(param['Threshold'])
            self.gain_r = gain_r = int(param['gain_r_T'])
            self.gain_s = gain_s = int(param['gain_s_T'])
            self.rnti = rnti = int(param['RNTI'])
            self.multiply_const = multiply_const = 128.0
            self.ip = ip = param['IP']
            self.route = route = param['route']
            self.ul_center_freq = ul_center_freq = int(param['u_frequency_T'])
            self.dl_center_freq = dl_center_freq = int(param['d_frequency_T'])
        except: print '变量初始化失败'     
        print prbl,fftl,multiply_const,samp_rate,threshold,gain_r,gain_s,rnti

        print ul_center_freq,dl_center_freq

        self.variable_ul_para_0 = variable_ul_para_0 = lte_sat.ul_parameter(rnti, prbl)
        self.variable_ul_para_0.set_cch_period(10, 4)
        self.variable_ul_para_0.set_srs_period(10, 5)
        self.variable_ul_para_0.set_sch_params(4, 2)
        self.variable_ul_para_0.set_srs_transmissionComb(1)
        self.variable_ul_para_0.enable_bsr_persist(True)
          
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
        self.uhd_usrp_source_0.set_samp_rate(4e6)
        self.uhd_usrp_source_0.set_center_freq(dl_center_freq*1e6, 0)
        self.uhd_usrp_source_0.set_gain(gain_r, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(ul_center_freq*1e6, 0)
        self.uhd_usrp_sink_0.set_gain(gain_s, 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=24,
                taps=None,
                fractional_bw=None,
        )
        self.lte_sat_ul_subframe_mapper_0 = lte_sat.ul_subframe_mapper()
        self.lte_sat_ul_subframe_mapper_0.set_uplink_config(variable_ul_para_0)
          
        self.lte_sat_ul_baseband_generator_0 = lte_sat.ul_baseband_generator()
        self.lte_sat_layer2_ue_0 = lte_sat.layer2_ue(variable_ul_para_0)
        self.lte_sat_layer2_ue_0.create_logic_channel(lte_sat.mode_um,0,False)
          
        self.lte_sat_dl_subframe_demapper_0 = lte_sat.dl_subframe_demapper(rnti)
        self.lte_sat_dl_baseband_sync_0 = lte_sat.dl_baseband_sync(threshold, False)
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu("tun1", 10000)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((multiply_const, ))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.lte_sat_dl_subframe_demapper_0, 0), (self.lte_sat_layer2_ue_0, 0))
        self.connect((self.lte_sat_ul_subframe_mapper_0, 0), (self.lte_sat_ul_baseband_generator_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.lte_sat_dl_baseband_sync_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.lte_sat_dl_baseband_sync_0, 0), (self.lte_sat_dl_subframe_demapper_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.lte_sat_ul_baseband_generator_0, 0), (self.rational_resampler_xxx_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_ul_subframe_mapper_0, "sys_info")
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_dl_subframe_demapper_0, "sys_info")
        self.msg_connect(self.lte_sat_layer2_ue_0, "sched_from_l2", self.lte_sat_ul_subframe_mapper_0, "sched_from_l2")
        self.msg_connect(self.blocks_tuntap_pdu_0, "pdus", self.lte_sat_layer2_ue_0, "tx_data")
        self.msg_connect(self.lte_sat_layer2_ue_0, "rx_data", self.blocks_tuntap_pdu_0, "pdus")
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_ul_baseband_generator_0, "sys_info")
        self.msg_connect(self.lte_sat_dl_subframe_demapper_0, "usg", self.lte_sat_layer2_ue_0, "usg")

    def get_status(self):
        status = {}
        status_temp = {}
        status_temp['wrong_rx_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_count
        status_temp['wrong_rx_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_count
        status_temp['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bps
        status_temp['rx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_count
        status_temp['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_bytes
        status_temp['rx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_count
        status_temp['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_bytes

        status_temp['total_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().total_usg_num
        status_temp['discard_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().discard_usg_num

        status_temp['tx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_count
        status_temp['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_bytes
        status_temp['tx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_count
        status_temp['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_bytes        
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
        status['rnti'] = self.lte_sat_dl_subframe_demapper_0.get_rnti()

        status['pdu_sum'] = self.lte_sat_layer2_ue_0.get_mac_pdu_sum()
        status['layer2_ue_fer'] = self.lte_sat_layer2_ue_0.get_fer()

        status['ue_stat_info_0'] = self.lte_sat_layer2_ue_0.get_ue_stat_info_string(0)
        status['ue_stat_info_1'] = self.lte_sat_layer2_ue_0.get_ue_stat_info_string(1)

        status['ip'] = self.ip
        status['route'] = self.route
        status['u_freq'] = self.ul_center_freq
        status['d_freq'] = self.dl_center_freq
        status['wrong_rx_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_count'])
        status['wrong_rx_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_bytes'])
        status['rx_right_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_count'])
        status['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bytes'])
        status['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bps'])
        status['rx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_count'])
        status['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_bytes'])
        status['rx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_count'])
        status['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_bytes'])

        status['total_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['total_usg_num'])
        status['discard_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['discard_usg_num'])
        status['tx_sr_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_sr_num

        status['tx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_count'])
        status['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_bytes'])
        status['tx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_count'])
        status['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_bytes'])        
        return status

class ue65_ping_15prb_audio(gr.top_block):

    def __init__(self,**param):
        gr.top_block.__init__(self, "Ue65 Ping 15Prb Audio")

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

            if param['samp_rate_T'] == '2M':
                self.samp_rate = samp_rate = 2e6 #2000000
            else:
                self.samp_rate = samp_rate = 4e6 #4000000 

            self.threshold = threshold = float(param['Threshold'])
            self.gain_r = gain_r = int(param['gain_r_T'])
            self.gain_s = gain_s = int(param['gain_s_T'])
            self.rnti = rnti = int(param['RNTI'])
            self.multiply_const = multiply_const = 128.0
            self.ip = ip = param['IP']
            self.route = route = param['route']
            self.u_center_freq = u_center_freq = int(param['u_frequency_T'])
            self.d_center_freq = d_center_freq = int(param['d_frequency_T'])
        except: print '变量初始化失败'

        print 'ue65_ping_15prb_audio'

        self.variable_ul_para_0 = variable_ul_para_0 = lte_sat.ul_parameter(rnti, 6)
        self.variable_ul_para_0.set_cch_period(10, 4)
        self.variable_ul_para_0.set_srs_period(10, 5)
        self.variable_ul_para_0.set_sch_params(4, 2)
        self.variable_ul_para_0.set_srs_transmissionComb(1)
        self.variable_ul_para_0.enable_bsr_persist(True)
          
        # self.samp_rate = samp_rate = 4e6
        # self.prbl = prbl = 15
        # self.fftl = fftl = 256

        ##################################################
        # Blocks
        ##################################################
        self.vocoder_g721_encode_sb_0_0 = vocoder.g721_encode_sb()
        self.vocoder_g721_decode_bs_0 = vocoder.g721_decode_bs()
        self.uhd_usrp_source_0 = uhd.usrp_source(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        # self.uhd_usrp_source_0.set_samp_rate(4e6)
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(900e6, 0)
        self.uhd_usrp_source_0.set_gain(10, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(800e6, 0)
        self.uhd_usrp_sink_0.set_gain(10, 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=24,
                taps=None,
                fractional_bw=None,
        )
        self.lte_sat_ul_subframe_mapper_0 = lte_sat.ul_subframe_mapper()
        self.lte_sat_ul_subframe_mapper_0.set_uplink_config(variable_ul_para_0)
          
        self.lte_sat_ul_baseband_generator_0 = lte_sat.ul_baseband_generator()
        self.lte_sat_layer2_ue_0 = lte_sat.layer2_ue(variable_ul_para_0)
        self.lte_sat_layer2_ue_0.create_logic_channel(lte_sat.mode_um,0,0)
          
        self.lte_sat_dl_subframe_demapper_0 = lte_sat.dl_subframe_demapper(rnti)
        self.lte_sat_dl_baseband_sync_0 = lte_sat.dl_baseband_sync(threshold, False)
        self.blocks_tagged_stream_to_pdu_0_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, "packet_len")
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 1000, "packet_len")
        self.blocks_short_to_float_0 = blocks.short_to_float(1, 1024)
        self.blocks_pdu_to_tagged_stream_0_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, "packet_len")
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((128.0, ))
        self.blocks_float_to_short_0_0 = blocks.float_to_short(1, 1024)
        self.audio_source_0_0 = audio.source(48000, "", True)
        self.audio_sink_0 = audio.sink(48000, "", True)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.lte_sat_ul_subframe_mapper_0, 0), (self.lte_sat_ul_baseband_generator_0, 0))
        self.connect((self.lte_sat_dl_subframe_demapper_0, 0), (self.lte_sat_layer2_ue_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.lte_sat_dl_baseband_sync_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.lte_sat_dl_baseband_sync_0, 0), (self.lte_sat_dl_subframe_demapper_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.blocks_tagged_stream_to_pdu_0_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.lte_sat_ul_baseband_generator_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.audio_source_0_0, 0), (self.blocks_float_to_short_0_0, 0))
        self.connect((self.blocks_float_to_short_0_0, 0), (self.vocoder_g721_encode_sb_0_0, 0))
        self.connect((self.vocoder_g721_encode_sb_0_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0_0, 0), (self.vocoder_g721_decode_bs_0, 0))
        self.connect((self.blocks_short_to_float_0, 0), (self.audio_sink_0, 0))
        self.connect((self.vocoder_g721_decode_bs_0, 0), (self.blocks_short_to_float_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.lte_sat_layer2_ue_0, "sched_from_l2", self.lte_sat_ul_subframe_mapper_0, "sched_from_l2")
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_dl_subframe_demapper_0, "sys_info")
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_ul_baseband_generator_0, "sys_info")
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_ul_subframe_mapper_0, "sys_info")
        self.msg_connect(self.blocks_tagged_stream_to_pdu_0_0, "pdus", self.lte_sat_layer2_ue_0, "tx_data")
        self.msg_connect(self.lte_sat_dl_subframe_demapper_0, "usg", self.lte_sat_layer2_ue_0, "usg")
        self.msg_connect(self.lte_sat_layer2_ue_0, "rx_data", self.blocks_pdu_to_tagged_stream_0_0, "pdus")

    def get_status(self):
        status = {}
        status_temp = {}
        status_temp['wrong_rx_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_count
        status_temp['wrong_rx_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_count
        status_temp['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bps
        status_temp['rx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_count
        status_temp['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_bytes
        status_temp['rx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_count
        status_temp['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_bytes

        status_temp['total_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().total_usg_num
        status_temp['discard_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().discard_usg_num

        status_temp['tx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_count
        status_temp['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_bytes
        status_temp['tx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_count
        status_temp['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_bytes

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
        status['rnti'] = self.lte_sat_dl_subframe_demapper_0.get_rnti()

        status['pdu_sum'] = self.lte_sat_layer2_ue_0.get_mac_pdu_sum()
        status['layer2_ue_fer'] = self.lte_sat_layer2_ue_0.get_fer()

        status['ue_stat_info_0'] = self.lte_sat_layer2_ue_0.get_ue_stat_info_string(0)
        status['ue_stat_info_1'] = self.lte_sat_layer2_ue_0.get_ue_stat_info_string(1)
        status['ip'] = self.ip
        status['route'] = self.route        
        status['u_freq'] = self.u_center_freq
        status['d_freq'] = self.d_center_freq

        status['wrong_rx_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_count'])
        status['wrong_rx_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_bytes'])
        status['rx_right_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_count'])
        status['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bytes'])
        status['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bps'])
        status['rx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_count'])
        status['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_bytes'])
        status['rx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_count'])
        status['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_bytes'])

        status['total_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['total_usg_num'])
        status['discard_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['discard_usg_num'])
        status['tx_sr_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_sr_num

        status['tx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_count'])
        status['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_bytes'])
        status['tx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_count'])
        status['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_bytes'])
        return status

class ue65_ping_15prb_data(gr.top_block):

    def __init__(self,**param):
        gr.top_block.__init__(self, "Ue65 Ping 15Prb Data")

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

            if param['samp_rate_T'] == '2M':
                self.samp_rate = samp_rate = 2e6 #2000000
            else:
                self.samp_rate = samp_rate = 4e6 #4000000 

            self.threshold = threshold = float(param['Threshold'])
            self.gain_r = gain_r = int(param['gain_r_T'])
            self.gain_s = gain_s = int(param['gain_s_T'])
            self.rnti = rnti = int(param['RNTI'])
            self.multiply_const = multiply_const = 128.0
            self.ip = ip = param['IP']
            self.route = route = param['route']
            self.ul_center_freq = ul_center_freq = int(param['u_frequency_T'])
            self.dl_center_freq = dl_center_freq = int(param['d_frequency_T'])
        except: print '变量初始化失败'     
        print prbl,fftl,multiply_const,samp_rate,threshold,gain_r,gain_s,rnti

        print ul_center_freq,dl_center_freq

        self.variable_ul_para_0 = variable_ul_para_0 = lte_sat.ul_parameter(rnti, prbl)
        self.variable_ul_para_0.set_cch_period(10, 4)
        self.variable_ul_para_0.set_srs_period(10, 5)
        self.variable_ul_para_0.set_sch_params(4, 2)
        self.variable_ul_para_0.set_srs_transmissionComb(1)
        self.variable_ul_para_0.enable_bsr_persist(True)
          
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
        self.uhd_usrp_source_0.set_samp_rate(4e6)
        self.uhd_usrp_source_0.set_center_freq(dl_center_freq*1e6, 0)
        self.uhd_usrp_source_0.set_gain(gain_r, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            device_addr="addr=192.168.10.2",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(ul_center_freq*1e6, 0)
        self.uhd_usrp_sink_0.set_gain(gain_s, 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=24,
                taps=None,
                fractional_bw=None,
        )
        self.lte_sat_ul_subframe_mapper_0 = lte_sat.ul_subframe_mapper()
        self.lte_sat_ul_subframe_mapper_0.set_uplink_config(variable_ul_para_0)
          
        self.lte_sat_ul_baseband_generator_0 = lte_sat.ul_baseband_generator()
        self.lte_sat_layer2_ue_0 = lte_sat.layer2_ue(variable_ul_para_0)
        self.lte_sat_layer2_ue_0.create_logic_channel(lte_sat.mode_um,0,False)
          
        self.lte_sat_dl_subframe_demapper_0 = lte_sat.dl_subframe_demapper(rnti)
        self.lte_sat_dl_baseband_sync_0 = lte_sat.dl_baseband_sync(threshold, False)
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu("tun1", 10000)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((multiply_const, ))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.lte_sat_dl_subframe_demapper_0, 0), (self.lte_sat_layer2_ue_0, 0))
        self.connect((self.lte_sat_ul_subframe_mapper_0, 0), (self.lte_sat_ul_baseband_generator_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.lte_sat_dl_baseband_sync_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.lte_sat_dl_baseband_sync_0, 0), (self.lte_sat_dl_subframe_demapper_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.lte_sat_ul_baseband_generator_0, 0), (self.rational_resampler_xxx_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_ul_subframe_mapper_0, "sys_info")
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_dl_subframe_demapper_0, "sys_info")
        self.msg_connect(self.lte_sat_layer2_ue_0, "sched_from_l2", self.lte_sat_ul_subframe_mapper_0, "sched_from_l2")
        self.msg_connect(self.blocks_tuntap_pdu_0, "pdus", self.lte_sat_layer2_ue_0, "tx_data")
        self.msg_connect(self.lte_sat_layer2_ue_0, "rx_data", self.blocks_tuntap_pdu_0, "pdus")
        self.msg_connect(self.lte_sat_dl_baseband_sync_0, "sys_info", self.lte_sat_ul_baseband_generator_0, "sys_info")
        self.msg_connect(self.lte_sat_dl_subframe_demapper_0, "usg", self.lte_sat_layer2_ue_0, "usg")

    def get_status(self):
        status = {}
        status_temp = {}
        status_temp['wrong_rx_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_count
        status_temp['wrong_rx_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_count
        status_temp['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bps
        status_temp['rx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_count
        status_temp['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_bytes
        status_temp['rx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_count
        status_temp['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_bytes

        status_temp['total_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().total_usg_num
        status_temp['discard_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().discard_usg_num

        status_temp['tx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_count
        status_temp['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_bytes
        status_temp['tx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_count
        status_temp['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_bytes        
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
        status['rnti'] = self.lte_sat_dl_subframe_demapper_0.get_rnti()

        status['pdu_sum'] = self.lte_sat_layer2_ue_0.get_mac_pdu_sum()
        status['layer2_ue_fer'] = self.lte_sat_layer2_ue_0.get_fer()

        status['ue_stat_info_0'] = self.lte_sat_layer2_ue_0.get_ue_stat_info_string(0)
        status['ue_stat_info_1'] = self.lte_sat_layer2_ue_0.get_ue_stat_info_string(1)

        status['ip'] = self.ip
        status['route'] = self.route
        status['u_freq'] = self.ul_center_freq
        status['d_freq'] = self.dl_center_freq
        status['wrong_rx_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_count'])
        status['wrong_rx_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_bytes'])
        status['rx_right_mac_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_count'])
        status['rx_right_mac_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bytes'])
        status['rx_right_mac_pdu_bps'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bps'])
        status['rx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_count'])
        status['rx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_bytes'])
        status['rx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_count'])
        status['rx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_bytes'])

        status['total_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['total_usg_num'])
        status['discard_usg_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['discard_usg_num'])
        status['tx_sr_num'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().tx_sr_num

        status['tx_rlc_sdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_count'])
        status['tx_rlc_sdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_bytes'])
        status['tx_rlc_pdu_count'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_count'])
        status['tx_rlc_pdu_bytes'] = self.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_bytes'])        
        return status

class MatplotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.figure = Figure()
        # self.axes = self.figure.add_subplot(1,1,1)
        # self.axes = self.figure.gca(projection='3d')
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.toolbar=NavigationToolbar2Wx(self.canvas)
        self.toolbar.AddLabelTool(5,'',wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (32,32)))

        self.toolbar.Realize()      

        self.cb_grid = wx.CheckBox(self, -1, 
            "显示网格",
            style=wx.ALIGN_RIGHT)
        # self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)

        self.button1 = wx.Button(self, -1, "信道幅频特性图")
        self.button2 = wx.Button(self, -1, "主同步星座图")
        self.button3 = wx.Button(self, -1, "均衡前星座图")
        self.button4 = wx.Button(self, -1, "均衡后星座图")
        self.button5 = wx.Button(self, -1, "时频资源图")
        self.button1.SetBackgroundColour('black')
        self.button1.SetForegroundColour('white')
        self.button2.SetBackgroundColour('black')
        self.button2.SetForegroundColour('white')
        self.button3.SetBackgroundColour('black')
        self.button3.SetForegroundColour('white')
        self.button4.SetBackgroundColour('black')
        self.button4.SetForegroundColour('white')
        self.button5.SetBackgroundColour('black')
        self.button5.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.draw,self.button1)
        self.Bind(wx.EVT_BUTTON,self.draw_scatter,self.button2)
        self.Bind(wx.EVT_BUTTON,self.draw_3d,self.button3)
        self.Bind(wx.EVT_BUTTON,self.draw_plot,self.button4)
        self.Bind(wx.EVT_BUTTON,self.draw_plot,self.button5)
        
        ########开始布局############
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(self.button1,1,wx.EXPAND)
        sizer1.Add(self.button2,1,wx.EXPAND)
        sizer1.Add(self.button3,1,wx.EXPAND)
        sizer1.Add(self.button4,1,wx.EXPAND)
        sizer1.Add(self.button5,1,wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(wx.StaticLine(self), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
        self.sizer.Add(sizer1, 0, wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
        self.sizer.Add(self.cb_grid,0,wx.ALIGN_RIGHT)
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

    def draw(self,event):
        global test_data
        print test_data

        self.figure.clear() 
        self.axes = self.figure.add_subplot(111)
        self.axes.clear() 
        self.axes.grid(self.cb_grid.IsChecked())

        t = np.arange(0.0, 3.0, 0.01)
        self.axes.plot(t)
        self.canvas.draw()
        # self.canvas.Refresh()

    def draw_scatter(self,event):
        self.figure.clear() 
        self.axes = self.figure.add_subplot(111)
        self.axes.clear()
        self.axes.grid(self.cb_grid.IsChecked())

        f = open ( '/home/zhguixin/test.dat' , 'rb' )
        x = np.fromfile ( f , dtype = np.float32 , count = 10000 )
        f.close()

        n = len ( x ) / 2

        """ break x into two arrays    """
        """ or reshape x to ( 2 , n )  """
        x = x.reshape ( 2 , n )

        """ Reconstruct the original complex array """
        wfc = np.zeros ( [ n ] , dtype = np.complex )
        wfc.real = x [ 0 ]
        wfc.imag = x [ 1 ]

        self.axes.scatter( wfc.real, wfc.imag, facecolor='blue' )
        self.canvas.draw()
        # plt.show()

    def draw_3d(self,event):
        self.figure.clear() 
        self.axes = self.figure.add_subplot(111)
        self.axes = self.figure.gca(projection='3d')
        self.axes.clear() 
        self.axes.grid(self.cb_grid.IsChecked())

        X = np.arange(-5, 5, 0.25)
        Y = np.arange(-5, 5, 0.25)
        X, Y = np.meshgrid(X, Y)
        R = np.sqrt(X**2 + Y**2)
        Z = np.sin(R)
        surf = self.axes.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                linewidth=0, antialiased=False)
        self.axes.set_zlim(-1.01, 1.01)

        self.axes.zaxis.set_major_locator(LinearLocator(10))
        self.axes.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

        self.figure.colorbar(surf, shrink=0.5, aspect=5)

        self.canvas.draw()

    def draw_plot(self,event):
        self.figure.clear() 
        self.axes = self.figure.add_subplot(211, axisbg='#FFFFCC')
        self.axes.clear()
        self.axes.grid(self.cb_grid.IsChecked())

        x = np.arange(0.0, 5.0, 0.01)
        y = np.sin(2*np.pi*x) + 0.5*np.random.randn(len(x))

        self.axes.plot(x, y, '-')
        self.axes.set_ylim(-2,2)
        self.axes.set_title('Press left mouse button and drag to test')

        self.axes2 = self.figure.add_subplot(212, axisbg='#FFFFCC')
        self.axes2.clear()
        self.axes2.grid(self.cb_grid.IsChecked())
        line2, = self.axes2.plot(x, y, '-')


        def onselect(xmin, xmax):
            indmin, indmax = np.searchsorted(x, (xmin, xmax))
            indmax = min(len(x)-1, indmax)

            thisx = x[indmin:indmax]
            thisy = y[indmin:indmax]
            line2.set_data(thisx, thisy)
            self.axes2.set_xlim(thisx[0], thisx[-1])
            self.axes2.set_ylim(thisy.min(), thisy.max())
            self.figure.canvas.draw()

        # set useblit True on gtkagg for enhanced performance
        self.span = SpanSelector(self.axes, onselect, 'horizontal', useblit=True,
                            rectprops=dict(alpha=0.5, facecolor='red') )

        self.figure.canvas.draw()
        # plt.show()

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

class MainFrame(wx.Frame):
    def __init__(self,parent,id):
        wx.Frame.__init__(self, None, title=u"终端界面", size=(1400,850))
        self.Centre()

        self.sp = wx.SplitterWindow(self)
        self.panel = wx.Panel(self.sp, style=wx.SP_3D)
        self.p1 = MatplotPanel(self.sp)
        self.sp.SplitVertically(self.panel,self.p1,650)

        self.panel.SetBackgroundColour("white")

        self.terminal_config = ConfigParser.ConfigParser()
        self.terminal_config.read("terminal.conf")
        
        #创建面板
        self.createframe()

        # 创建一个pubsub接收器,用于接收从子线程传递过来的消息
        Publisher().subscribe(self.updateDisplay, "update")

    def updateDisplay(self, msg):
        """
        从线程接收数据并且在界面更新显示
        """
        dict_status = msg.data

        # global test_data
        # test_data = dict_status['matplot_data']
        # print dict_status
        if dict_status['pss_status']:
            self.pss_status.state_green()
        else:
            self.pss_status.state_red()
        if dict_status['sss_status']:
            self.sss_status.state_green()
        else:
            self.sss_status.state_red()
        if dict_status['pbch_status']:
            self.pbch_status.state_green()
        else:
            self.pbch_status.state_red()
        if dict_status['process_state']==1:
            self.process_state.state_green()
        elif dict_status['process_state']==0:
            self.process_state.state_red()
        self.id_cell_t.SetLabel(str(dict_status['cell_id']))
        self.rnti_t.SetLabel(str(dict_status['rnti']))
        # self.virtual_ip_t.SetLabel(str(dict_status['ip']))
        # self.select_route_t.SetLabel(str(dict_status['route']))
        self.bandwidth_t.SetLabel(str(dict_status['prbl']))
        self.cfo.SetLabel(str(dict_status['cfo']))
        self.fte.SetLabel(str(dict_status['fte']))
        self.pss_pos.SetLabel(str(dict_status['pss_pos']))

        self.u_frequency.SetLabel(str(dict_status['u_freq']))
        self.d_frequency.SetLabel(str(dict_status['d_freq']))

        self.mac_pdu_value.SetLabel(str(dict_status['pdu_sum']))
        self.frame_error_rate_value.SetLabel(str(dict_status['fer']))
        self.fn.SetLabel(str(dict_status['fn']))
        self.sfn.SetLabel(str(dict_status['sfn']))

        rows = [('RX CRC错误总包数',dict_status['wrong_rx_mac_pdu_count']+' packet'),
        ('RX CRC错误字节数',dict_status['wrong_rx_mac_pdu_bytes']+' bytes'),
        ('RX CRC正确总包数',dict_status['rx_right_mac_pdu_count']+' packet'),
        ('RX CRC正确字节数',dict_status['rx_right_mac_pdu_bytes']+' bytes'),
        ('',dict_status['rx_right_mac_pdu_bps']),
        ('MAC==>RLC总包数',dict_status['rx_rlc_pdu_count']+' packet'),
        ('MAC==>RLC字节数',dict_status['rx_rlc_pdu_bytes']+' bytes'),
        ('RLC==>高层总包数',dict_status['rx_rlc_sdu_count']+' packet'),
        ('RLC==>高层字节数',dict_status['rx_rlc_sdu_bytes']+' bytes'),
        ('RX 丢弃调度数目',dict_status['total_usg_num']),
        ('RX 总调度的数目',dict_status['discard_usg_num']),
        ('TX 发送的SR数目',dict_status['tx_sr_num']),
        ('TX 高层==>RLC总包数',dict_status['tx_rlc_sdu_count']+' packet'),
        ('TX 高层==>RLC字节数',dict_status['tx_rlc_sdu_bytes']+' bytes'),
        ('TX RLC==>MAC总包数',dict_status['tx_rlc_pdu_count']+' packet'),
        ('TX RLC==>MAC字节数',dict_status['tx_rlc_pdu_bytes']+' bytes'),
        ]

        for index in range(len(rows)):
            self.list.SetStringItem(index, 1, str(rows[index][1]))

    def createframe(self):

        #绑定窗口的关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        # 小区ID
        id_cell = wx.StaticText(self.panel, -1, u'小区ID:')
        # self.id_cell_t = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.id_cell_t = wx.StaticText(self.panel, -1)

        # RNTI
        rnti = wx.StaticText(self.panel, -1, u'RNTI:')
        # self.rnti_t = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.rnti_t = wx.StaticText(self.panel, -1)

        # 系统带宽
        bandwidth = wx.StaticText(self.panel, -1, u'系统带宽:')
        # self.bandwidth_t = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.bandwidth_t = wx.StaticText(self.panel, -1)

        # 上下行中心频率
        u_frequency_st = wx.StaticText(self.panel, -1, u"上行中心频率(MHz):")
        # self.u_frequency = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.u_frequency = wx.StaticText(self.panel, -1)
        d_frequency_st = wx.StaticText(self.panel, -1, u"下行中心频率(MHz):")
        # self.d_frequency = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.d_frequency = wx.StaticText(self.panel, -1)

        #实时载波频率偏差值
        cfo_st = wx.StaticText(self.panel, -1, u"实时载波频率偏差:")
        # self.cfo = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.cfo = wx.StaticText(self.panel, -1)

        #实时细定时误差
        fte_st = wx.StaticText(self.panel, -1, u"实时细定时误差:")
        # self.fte = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.fte = wx.StaticText(self.panel, -1)

        #峰值位置
        pss_pos_st = wx.StaticText(self.panel, -1, u"峰值位置:")
        # self.pss_pos = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)
        self.pss_pos = wx.StaticText(self.panel, -1)

        # #虚拟ip地址
        # virtual_ip = wx.StaticText(self.panel, -1, u"虚拟ip地址:")
        # # self.virtual_ip_t = wx.TextCtrl(self.panel, -1, "192.168.200.11", style=wx.TE_READONLY)
        # self.virtual_ip_t = wx.StaticText(self.panel, -1, '192.168.200.11')

        # #选择路由
        # select_route = wx.StaticText(self.panel, -1, u"选择路由:")
        # # self.select_route_t = wx.TextCtrl(self.panel, -1, "192.168.200.3", style=wx.TE_READONLY)
        # self.select_route_t = wx.StaticText(self.panel, -1, '192.168.200.3')

        #主同步状态是否锁定
        pss_status_st = wx.StaticText(self.panel, -1, u"主同步状态:\t\t\t")
        self.pss_status = PanelOne(self.panel)

        #辅同步状态是否锁定
        sss_status_st = wx.StaticText(self.panel, -1, u"辅同步状态:\t\t\t")
        self.sss_status = PanelOne(self.panel)

        #pbch是否找到
        pbch_status_st = wx.StaticText(self.panel, -1, u"pbch是否找到:\t\t\t")
        self.pbch_status = PanelOne(self.panel)

        #当前处理状态
        process_state_st = wx.StaticText(self.panel, -1, u"处理状态(捕获／跟踪):\t\t\t")
        self.process_state = PanelOne(self.panel)

        # MAC_PDU个数、误帧率、帧号、子帧号
        # status_bar_lable = "MAC_PDU个数:\t\t\t误帧率:\t"
        # self.status_bar = wx.TextCtrl(self.panel, -1, status_bar_lable, style=wx.TE_READONLY)
        
        # 获取下行链路接收的mac_pdu的个数
        mac_pdu = wx.StaticText(self.panel, -1, u"mac_pdu的个数:")
        self.mac_pdu_value = wx.StaticText(self.panel, -1, '')

        frame_error_rate = wx.StaticText(self.panel, -1, u"误帧率:")
        self.frame_error_rate_value = wx.StaticText(self.panel, -1, '')

        fn_st = wx.StaticText(self.panel, -1, u"帧号:")
        self.fn = wx.StaticText(self.panel, -1, '')

        sfn_st = wx.StaticText(self.panel, -1, u"子帧号:")
        self.sfn = wx.StaticText(self.panel, -1, '')

        #详细显示按钮
        self.detail_button = wx.Button(self.panel, -1, u"详细显示")
        self.detail_button.SetBackgroundColour('black')
        self.detail_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Detail,self.detail_button)
        # self.detail_button.Disable()

        self.detail_button_grid = wx.Button(self.panel, -1, u"详细显示之二")
        self.detail_button_grid.SetBackgroundColour('black')
        self.detail_button_grid.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Detail_1,self.detail_button_grid)
        self.detail_button_grid.Disable()

        #连接按钮
        self.connect_button = wx.Button(self.panel, -1, u"连接")
        self.connect_button.SetBackgroundColour('black')
        self.connect_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)  
        # self.connect_button.SetDefault() 

        #设置连接服务器的IP地址和端口号
        self.terminal_config.read("terminal.conf")
        try: s_ip = self.terminal_config.get("address", "s_ip")
        except: s_ip = '192.168.139.180'

        try: s_port = self.terminal_config.get("address", "s_port")
        except: s_port = '7000'

        ip_st = wx.StaticText(self.panel, -1, u"IP地址 :")
        self.IPText = wx.TextCtrl(self.panel, -1, s_ip)
        port_st = wx.StaticText(self.panel, -1, u"端口号 :")  
        self.PortText = wx.TextCtrl(self.panel, -1, s_port)

        self.list = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT, size=(300,400))

        columns = ['名称','值']

        rows = [('RX CRC错误总包数','0'),
        ('RX CRC错误字节数','0'),
        ('RX CRC正确总包数','0'),
        ('RX CRC正确字节数','0'),
        ('','0'),
        ('MAC==>RLC总包数','0'),
        ('MAC==>RLC字节数','0'),
        ('RLC==>高层总包数','0'),
        ('RLC==>高层字节数','0'),
        ('RX 丢弃调度数目','0'),
        ('RX 总调度的数目','0'),
        ('TX 发送的SR数目','0'),
        ('TX 高层==>RLC总包数','0'),
        ('TX 高层==>RLC字节数','0'),
        ('TX RLC==>MAC总包数','0'),
        ('TX RLC==>MAC字节数','0'),
        ] 

        # Add some columns
        for col, text in enumerate(columns):
            self.list.InsertColumn(col, text)

        # add the rows
        for item in rows:
            index = self.list.InsertStringItem(sys.maxint, item[0])
            for col, text in enumerate(item[1:]):
                self.list.SetStringItem(index, col+1, text)

        # set the width of the columns in various ways
        self.list.SetColumnWidth(0, 180)
        # self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, 120)

        #上行中心频率
        u_frequency_list = ['20','800','900','1000','1200']
        u_frequency_st_param = wx.StaticText(self.panel, -1, u"上行中心频率(MHz):")
        self.u_frequency_param = wx.ComboBox(self.panel, -1, '20', wx.DefaultPosition,
         wx.DefaultSize, u_frequency_list, 0)
        # self.u_frequency = wx.TextCtrl(self.panel,-1,'20')

        #下行中心频率
        d_frequency_list = ['40','900','1000','1200']
        d_frequency_st_param = wx.StaticText(self.panel, -1, u"下行中心频率(MHz):")
        self.d_frequency_param = wx.ComboBox(self.panel, -1, '40', wx.DefaultPosition,
         wx.DefaultSize, d_frequency_list, 0)
        # self.d_frequency = wx.TextCtrl(self.panel,-1,'40')

        PRBList = ['1.4','3']
        prb_statictext = wx.StaticText(self.panel, -1, u"链路带宽(MHz):")
        self.prb_c = wx.ComboBox(self.panel, -1, '3', wx.DefaultPosition, wx.DefaultSize, PRBList, 0)

        #调制方式
        ModtypeList = ['QPSK','16QAM']
        modtype_st = wx.StaticText(self.panel, -1, u"调制方式:")
        self.modtype = wx.ComboBox(self.panel, -1, 'QPSK', wx.DefaultPosition, wx.DefaultSize, ModtypeList, 0)

        self.run_ue_audio_btn = wx.Button(self.panel, -1, u"音频业务演示")
        # self.run_ue_audio_btn.SetBackgroundColour('black')
        # self.run_ue_audio_btn.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnRunUE_Audio, self.run_ue_audio_btn)

        self.run_ue_video_btn = wx.Button(self.panel, -1, u"视频业务演示")
        # self.run_ue_video_btn.SetBackgroundColour('black')
        # self.run_ue_video_btn.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnRunUE_Video, self.run_ue_video_btn)

        self.run_ue_data_btn = wx.Button(self.panel, -1, u"数据业务演示")
        # self.run_ue_data_btn.SetBackgroundColour('black')
        # self.run_ue_data_btn.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnRunUE_Data, self.run_ue_data_btn)

        ###########开始布局############
        sizer1 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer1.AddGrowableCol(1)
        sizer1.AddGrowableCol(3)
        sizer1.Add(id_cell, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.id_cell_t, 0, wx.EXPAND)
        sizer1.Add(rnti, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.rnti_t, 0, wx.EXPAND)
        sizer1.Add(pss_pos_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.pss_pos, 0, wx.EXPAND)
        sizer1.Add(bandwidth, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.bandwidth_t, 0, wx.EXPAND)            
        sizer1.Add(fte_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.fte, 0, wx.EXPAND)
        sizer1.Add(cfo_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.cfo, 0, wx.EXPAND)
        sizer1.Add(u_frequency_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.u_frequency, 0, wx.EXPAND)
        sizer1.Add(d_frequency_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.d_frequency, 0, wx.EXPAND)
        # sizer1.Add(virtual_ip, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        # sizer1.Add(self.virtual_ip_t, 0, wx.EXPAND)
        # sizer1.Add(select_route, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        # sizer1.Add(self.select_route_t, 0, wx.EXPAND)

        sizer11 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer11.AddGrowableCol(1)
        sizer11.Add(pss_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.pss_status, 0, wx.EXPAND)
        sizer11.Add(sss_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.sss_status, 0, wx.EXPAND)
        sizer11.Add(pbch_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.pbch_status, 0, wx.EXPAND)
        sizer11.Add(process_state_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.process_state, 0, wx.EXPAND)

        sizer111 = wx.FlexGridSizer(cols=4, hgap=10, vgap=10)
        sizer111.AddGrowableCol(1)
        sizer111.AddGrowableCol(3)
        sizer111.Add(frame_error_rate, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer111.Add(self.frame_error_rate_value, 0, wx.EXPAND)
        sizer111.Add(mac_pdu, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer111.Add(self.mac_pdu_value, 0, wx.EXPAND)
        sizer111.Add(fn_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer111.Add(self.fn, 0, wx.EXPAND)
        sizer111.Add(sfn_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer111.Add(self.sfn, 0, wx.EXPAND)

        #高级按钮
        sizer_detail = wx.BoxSizer(wx.HORIZONTAL)
        sizer_detail.Add((10,10), 1)
        sizer_detail.Add(self.detail_button, 0, wx.ALIGN_RIGHT)
        sizer_detail.Add((10,10), 0)
        sizer_detail.Add(self.detail_button_grid, 0, wx.ALIGN_RIGHT)

        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'状态显示'), wx.VERTICAL)
        sizer2.Add(sizer1, 0, wx.EXPAND | wx.ALL | wx.TOP, 10)
        sizer2.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,10)
        sizer2.Add(sizer11, 0, wx.EXPAND | wx.ALL, 10)
        sizer2.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,10)
        sizer2.Add(sizer111, 0, wx.EXPAND | wx.ALL, 10)
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
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL|wx.TOP, 0)
        box1.Add((20,20), 0)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)
        box1.Add((20,20), 0)
        box1.Add(sizer5,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)

        box2 = wx.BoxSizer(wx.VERTICAL)
        box2.Add(self.list,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box2.Add((20,20), 0)

        box_st1 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u''), wx.VERTICAL)
        box_st1.Add(box2,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)

        sizer_param = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        sizer_param.AddGrowableCol(1)
        sizer_param.Add(modtype_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.modtype, 0, wx.EXPAND)
        sizer_param.Add(prb_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.prb_c, 0, wx.EXPAND)
        sizer_param.Add(u_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.u_frequency_param, 0, wx.EXPAND)
        sizer_param.Add(d_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.d_frequency_param, 0, wx.EXPAND)

        box_st_param = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'本地运行参数配置'), wx.VERTICAL)
        box_st_param.Add(sizer_param, 0, wx.ALIGN_CENTER)

        box_st2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'本地运行UE测试'), wx.HORIZONTAL)
        box_st2.Add(self.run_ue_data_btn, 0, wx.ALIGN_CENTER)
        box_st2.Add((20,20), 0)
        box_st2.Add(self.run_ue_audio_btn, 0, wx.ALIGN_CENTER)
        box_st2.Add((20,20), 0)
        box_st2.Add(self.run_ue_video_btn, 0, wx.ALIGN_CENTER)

        box3 = wx.BoxSizer(wx.VERTICAL)
        box3.Add(box_st1,0,wx.EXPAND | wx.ALL)
        box3.Add((20,20), 0)
        box3.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)
        box3.Add((20,20), 0)
        box3.Add(box_st_param,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box3.Add((26,26), 0)
        box3.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)
        box3.Add((20,20), 0)
        box3.Add(box_st2,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)

        box4 = wx.BoxSizer(wx.HORIZONTAL)
        box4.Add(box1,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box4.Add(box3,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)

        #自动调整界面尺寸
        self.panel.SetSizer(box4)

    def OnRunUE_Data(self,event):
        self.run_ue_data_btn.Disable()
        self.u_frequency_param.Disable()
        self.d_frequency_param.Disable()
        self.prb_c.Disable()
        self.modtype.Disable()
        
        self.p2 = threading.Thread(target = self.Run_UE_Data)
        self.p2.setDaemon(True)
        self.p2.start()   

    def Run_UE_Data(self):
        param_temp = {}
        param_temp[u'd_frequency_T'] = self.u_frequency_param.GetValue()
        param_temp[u'u_frequency_T'] = self.d_frequency_param.GetValue()
        param_temp[u'Bandwidth'] = self.prb_c.GetValue()
        param_temp[u'mod_type_u'] = self.modtype.GetValue()
        param_temp[u'mod_type_d'] = self.modtype.GetValue()

        param = {u'n_pucch': u'0', u'work_mod': u'1', u'DMRS1_T': u'4',
        u'Delta_ss_T': u'10', u'algorithm_T': u'Max_Log',
        u'samp_rate_T': u'4M',u'C_SRS': u'4', u'm_part': u'2', u'n_RRC': u'10',
        u'decision_type_T': u'soft', u'shift_T': u'1',u'IP': u'192.168.200.111',
        u'K_TC': u'0', u'n_SRS': u'4', u'SR_periodicity': u'10',
        u'RNTI': u'65', u'B_SRS': u'1', u't_advance': u'0', u'data_rules_T': u'1',
        u'M_part': u'2', u'route': u'192.168.200.333', u'gain_r_T': u'10',
        u'SRS_period': u'2',u'id_cell': 10, u'gain_s_T': u'10', u'iter_num_T': u'4',
        u'SR_offset': u'2',u'Threshold': u'0.5', u'SRS_offset': u'0'}
        
        param.update(param_temp)

        os.system('rm -rvf *.log *.dat *.test')
        # os.system('uhd_usrp_probe')
        time.sleep(2)
        self.tb = ue65_ping_15prb_data(**param)
        os.system('sudo ifconfig tun1 192.168.200.12')
        os.system('sudo route add 192.168.200.3 tun1')

        self.t_1 = threading.Thread(target = self.update_panel)
        self.t_1.setDaemon(True)
        self.t_1.start()

        self.tb.start()
        self.tb.wait()        

    def OnRunUE_Audio(self,event):
        self.run_ue_audio_btn.Disable()
        self.u_frequency_param.Disable()
        self.d_frequency_param.Disable()
        self.prb_c.Disable()
        self.modtype.Disable()
                
        self.p2 = threading.Thread(target = self.Run_UE_Audio)
        self.p2.setDaemon(True)
        self.p2.start()   

    def Run_UE_Audio(self):
        param_temp = {}
        param_temp[u'd_frequency_T'] = self.u_frequency_param.GetValue()
        param_temp[u'u_frequency_T'] = self.d_frequency_param.GetValue()
        param_temp[u'Bandwidth'] = self.prb_c.GetValue()
        param_temp[u'mod_type_u'] = self.modtype.GetValue()
        param_temp[u'mod_type_d'] = self.modtype.GetValue()        

        param = {u'n_pucch': u'0', u'work_mod': u'1', u'DMRS1_T': u'4',
        u'Delta_ss_T': u'10', u'algorithm_T': u'Max_Log',
        u'samp_rate_T': u'4M',u'C_SRS': u'4', u'm_part': u'2', u'n_RRC': u'10',
        u'decision_type_T': u'soft', u'shift_T': u'1',u'IP': u'192.168.200.111',
        u'K_TC': u'0', u'n_SRS': u'4', u'SR_periodicity': u'10',
        u'RNTI': u'65', u'B_SRS': u'1', u't_advance': u'0', u'data_rules_T': u'1',
        u'M_part': u'2', u'route': u'192.168.200.333', u'gain_r_T': u'10',
        u'SRS_period': u'2',u'id_cell': 10, u'gain_s_T': u'10', u'iter_num_T': u'4',
        u'SR_offset': u'2',u'Threshold': u'0.5', u'SRS_offset': u'0'}
        
        param.update(param_temp)

        os.system('rm -rvf *.log *.dat *.test')
        # os.system('uhd_usrp_probe')
        time.sleep(2)
        self.tb = ue65_ping_15prb_audio(**param)
        
        self.t_1 = threading.Thread(target = self.update_panel)
        self.t_1.setDaemon(True)
        self.t_1.start()

        self.tb.start()
        self.tb.wait()

    def OnRunUE_Video(self,event):

        self.run_ue_video_btn.Disable()
        self.u_frequency_param.Disable()
        self.d_frequency_param.Disable()
        self.prb_c.Disable()
        self.modtype.Disable()        
        
        self.p2 = threading.Thread(target = self.Run_UE_Video)
        self.p2.setDaemon(True)
        self.p2.start()

    def Run_UE_Video(self):
        param_temp = {}
        param_temp[u'd_frequency_T'] = self.u_frequency_param.GetValue()
        param_temp[u'u_frequency_T'] = self.d_frequency_param.GetValue()
        param_temp[u'Bandwidth'] = self.prb_c.GetValue()
        param_temp[u'mod_type_u'] = self.modtype.GetValue()
        param_temp[u'mod_type_d'] = self.modtype.GetValue()        

        param = {u'n_pucch': u'0', u'work_mod': u'2', u'DMRS1_T': u'4', u'Delta_ss_T': u'10',
        u'SRS_offset': u'0', u'algorithm_T': u'Max_Log',
        u'gain_s_T': u'10', u'samp_rate_T': u'4M', u'C_SRS': u'4', u'IP': u'192.168.200.111',
        u'RNTI': u'65', u'decision_type_T': u'soft', u'shift_T': u'1',
        u'm_part': u'2', u'K_TC': u'0', u'n_SRS': u'4', u'SR_periodicity': u'10',
        u'n_RRC': u'10', u'B_SRS': u'1', u't_advance': u'0', u'data_rules_T': u'1', u'M_part': u'2',
        u'gain_r_T': u'10', u'SRS_period': u'2', u'id_cell': 10,
        u'iter_num_T': u'4', u'SR_offset': u'2', u'Threshold': u'0.5', u'route': u'192.168.200.333'}
        
        param.update(param_temp)

        print param
        os.system('rm -rvf *.log *.dat *.test')
        # os.system('uhd_usrp_probe')
        time.sleep(2)
        self.tb = ue65_ping_15prb_video(**param)
        os.system('sudo ifconfig tun1 192.168.200.12')
        os.system('sudo route add 192.168.200.3 tun1')

        self.t_1 = threading.Thread(target = self.update_panel)
        self.t_1.setDaemon(True)
        self.t_1.start()

        self.tb.start()
        self.tb.wait()

    def update_panel(self):
        while True:
            wx.CallAfter(Publisher().sendMessage, "update", self.tb.get_status())
            time.sleep(1)

    def Detail_1(self,event):
        self.detail_dlg = Detail_Dialog(None)
        self.detail_dlg.Bind(wx.EVT_CLOSE, self.OnCloseWindowDetail_1)
        self.detail_dlg.Show()
        self.detail_button_grid.Disable()
    
    def Detail(self,event):
        self.detaildialog = DetailDialog_Display(None)
        self.detaildialog.Bind(wx.EVT_CLOSE, self.OnCloseWindowDetail)
        self.detaildialog.Show()
        self.detail_button.Disable()
    
    def OnCloseWindowDetail(self,event):
        self.detail_button.Enable()
        self.detaildialog.Destroy()

    def OnCloseWindowDetail_1(self,event):
        self.detail_button_grid.Enable()
        self.detail_dlg.Destroy()        

    def OnConnect(self, event):
        self.IPText.Disable()
        self.PortText.Disable()
        self.connect_button.Disable()
        self.terminal_config.read("terminal.conf")
        if "address" not in self.terminal_config.sections():
            self.terminal_config.add_section("address")

        #address
        self.terminal_config.set("address", "s_ip", self.IPText.GetValue())
        self.terminal_config.set("address", "s_port", self.PortText.GetValue())

        #写入配置文件
        param_file = open("terminal.conf","w")
        self.terminal_config.write(param_file)
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
        self.status['terminal'] = 'true'

        self.t2 = threading.Thread(target = self.monitor_update)
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
                data = s.recv(2048)

                # print data
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
                        param = json.loads(data)
                        # A readable client socket has data  
                        print param
                        print 'received param from ', s.getpeername() 
                        try:
                            if self.p1.is_alive():
                                #GNURadio模块运行过程中修改参数
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
    
    def monitor_update(self): 
        while True:
            try:
                if self.p1.is_alive():
                    self.status.update(self.q.get())
                    wx.CallAfter(Publisher().sendMessage, "update", self.status)
            except:
                # pass
                print 'self.p1..dead'
            time.sleep(1)

    # start_monitor函数分别向本地界面、远程界面传递状态信息
    def start_monitor(self):
        while True:
            self.send_status = self.status
            if self.send_status.has_key('matplot_data'):
                del self.send_status['matplot_data']
            data_status = json.dumps(self.send_status)
            self.client.send(data_status)
            time.sleep(1)
            if self.send_status.has_key('terminal'):
                del self.send_status['terminal']

    #子进程
    def start_top_block(self):
        os.system('sudo rm  *.dat *.log')
        global param 
        if param['work_mod'] == '2': 
            time.sleep(2)
            self.tb = ue65_ping_15prb_video(**param)
            os.system('sudo ifconfig tun1 192.168.200.12')
            os.system('sudo route add 192.168.200.3 tun1')

            # self.p_play = multiprocessing.Process(name='start_play',
            #     target=self.start_play)
            # self.p_play = threading.Thread(target=self.start_play)
            # self.p_play.daemon = True
            # self.p_play.start()

        elif param['work_mod'] == '0':
            self.tb = ue65_ping_15prb_data(**param)
        elif param['work_mod'] == '1':
            time.sleep(2)
            self.tb = ue65_ping_15prb_audio(**param)
            # os.system('sudo ifconfig tun1 192.168.200.12')
            # os.system('sudo route add 192.168.200.3 tun1')

        self.t1 = threading.Thread(target = self.monitor_forever)
        self.t1.setDaemon(True)
        self.t1.start()

        self.tb.start()
        self.tb.wait()

    def monitor_forever(self):
        
        while True:
            #从控制界面获取参数，动态改变
            # self.tb.set_threshold(self.q.get())

            #获取Gnuradio模块中的状态信息，传递至界面
            self.q.put(self.tb.get_status())

            time.sleep(1) 

    def stop_top_block(self):
        self.p1.terminate()
        # self.p_play.terminate()

        self.pss_status.state_red()
        self.sss_status.state_red()
        self.pbch_status.state_red()
        self.process_state.state_red()
        self.cfo.SetLabel('0')
        self.fte.SetLabel('0')
        self.pss_pos.SetLabel('0')
        # self.virtual_ip_t.SetLabel('192.168.200.11')
        # self.select_route_t.SetLabel('192.168.200.3')
        self.id_cell_t.SetLabel('0')
        self.rnti_t.SetLabel('0')
        self.bandwidth_t.SetLabel('0')
        print 'stop'

    def OnCloseWindow(self, event):
        try:
            self.status['terminal'] = 'false'
            data_status = json.dumps(self.status)
            self.client.send(data_status)
            self.client.close() 
            self.Destroy()
            if isinstance(self.detaildialog,DetailDialog_Display) == True:
                self.detaildialog.Destroy()
            if isinstance(self.detail_dlg,Detail_Dialog) == True:
                self.detail_dlg.Destroy()            
        except:
            self.Destroy()
            if isinstance(self.detaildialog,DetailDialog_Display) == True:
                self.detaildialog.Destroy()
            if isinstance(self.detail_dlg,Detail_Dialog) == True:
                self.detail_dlg.Destroy()                

    # def start_play(self):
    #     str_play = "vlc rtp://@:5004"
    #     print str_play
    #     os.system(str_play)

class DetailDialog_Display(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, title=u'详细显示界面',size=(550,500),
            style=wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU)
        self.Centre()
        # self.parent = parent
        self.panel = wx.Panel(self, style=wx.SP_3D)
        self.SetBackgroundColour("white")

        #创建面板
        self.DetailPanel()
        Publisher().subscribe(self.updateDisplay, "update")

    def updateDisplay(self, msg):
        """
        从线程接收数据并且在界面更新显示
        """
        dict_status = msg.data

        self.DisplayText.Clear()
        self.DisplayText.AppendText(str(dict_status['ue_stat_info_0']))
        self.DisplayText.AppendText(str(dict_status['ue_stat_info_1']))

        self.mac_pdu_value.SetLabel(str(dict_status['pdu_sum']))
        self.frame_error_rate_value.SetLabel(str(dict_status['fer']))
        self.fn.SetLabel(str(dict_status['fn']))
        self.sfn.SetLabel(str(dict_status['sfn']))

        self.virtual_ip_t.SetLabel(str(dict_status['ip']))
        self.select_route_t.SetLabel(str(dict_status['route']))  

    def DetailPanel(self):

        self.DisplayText = wx.TextCtrl(self.panel, -1, '',   
            size=(350, 300), style=wx.TE_MULTILINE | wx.TE_READONLY) 
        self.DisplayText.SetBackgroundColour('gray')

        # MAC_PDU个数、误帧率、帧号、子帧号
        mac_pdu = wx.StaticText(self.panel, -1, u"mac_pdu的个数:\t")
        self.mac_pdu_value = wx.StaticText(self.panel, -1, '')

        frame_error_rate = wx.StaticText(self.panel, -1, u"误帧率:\t")
        self.frame_error_rate_value = wx.StaticText(self.panel, -1, '')

        fn_st = wx.StaticText(self.panel, -1, u"帧号:\t")
        self.fn = wx.StaticText(self.panel, -1, '')

        sfn_st = wx.StaticText(self.panel, -1, u"子帧号:\t")
        self.sfn = wx.StaticText(self.panel, -1, '')

        #虚拟ip地址
        virtual_ip = wx.StaticText(self.panel, -1, u"虚拟ip地址:")
        self.virtual_ip_t = wx.StaticText(self.panel, -1, "192.168.200.11")

        #选择路由
        select_route = wx.StaticText(self.panel, -1, u"选择路由:")
        self.select_route_t = wx.StaticText(self.panel, -1, "192.168.200.3")

        sizer1 = wx.FlexGridSizer(cols=4, hgap=10, vgap=10)
        sizer1.AddGrowableCol(1)
        sizer1.AddGrowableCol(3)
        sizer1.Add(virtual_ip, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.virtual_ip_t, 0, wx.EXPAND)
        sizer1.Add(select_route, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.select_route_t, 0, wx.EXPAND)
        sizer1.Add(frame_error_rate, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.frame_error_rate_value, 0, wx.EXPAND)
        sizer1.Add(mac_pdu, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.mac_pdu_value, 0, wx.EXPAND)
        sizer1.Add(fn_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.fn, 0, wx.EXPAND)
        sizer1.Add(sfn_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.sfn, 0, wx.EXPAND)

        box1 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'详细显示'), wx.VERTICAL)
        box1.Add((10,10), 0)
        box1.Add(self.DisplayText, 0, wx.EXPAND | wx.ALL, 10)
        box1.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)


        hbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox1.Add((10,10), 0)
        hbox1.Add(box1, 0, wx.EXPAND | wx.ALL)

        self.panel.SetSizer(hbox1)
        self.panel.Fit()

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
        # self.update_button = wx.Button(self, -1, u"更新")
        # self.Bind(wx.EVT_BUTTON, self.OnConnect, self.update_button)

        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(16,3)

        attr1 = wx.grid.GridCellAttr()
        attr1.SetReadOnly(True)
        for row in range(4):
            self.grid.SetColAttr(row+1, attr1)

        attr2 = wx.grid.GridCellAttr()
        attr2.SetReadOnly(True)
        attr2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.grid.SetColAttr(0, attr2)

        self.grid.SetColSize(0, 170)
        self.grid.SetColSize(1, 150)
        self.grid.SetColSize(2, 320)

        list_variable = ['wrong_rx_mac_pdu_count','wrong_rx_mac_pdu_bytes',
        'rx_right_mac_pdu_count','rx_right_mac_pdu_bytes','rx_right_mac_pdu_bps',
        'rx_rlc_pdu_count','rx_rlc_pdu_bytes','rx_rlc_sdu_count','rx_rlc_sdu_bytes',
        'total_usg_num','discard_usg_num','tx_sr_num','tx_rlc_sdu_count',
        'tx_rlc_sdu_bytes','tx_rlc_pdu_count','tx_rlc_pdu_bytes']

        colLabels = ['名称','值','含义']

        list_meaning = ['RX CRC错误总包数',
        'RX CRC错误字节数',
        'RX CRC正确总包数',
        'RX CRC正确字节数',
        '',
        'MAC==>RLC总包数',
        'MAC==>RLC字节数',
        'RLC==>高层总包数',
        'RLC==>高层字节数',
        'RX 丢弃调度数目',
        'RX 总调度的数目',
        'TX 发送的SR数目',
        'TX 高层==>RLC总包数',
        'TX 高层==>RLC字节数',
        'TX RLC==>MAC总包数',
        'TX RLC==>MAC字节数']

        for row in range(len(colLabels)):
            self.grid.SetColLabelValue(row, colLabels[row])

        for row in range(len(list_variable)):
            self.grid.SetCellValue(row, 2, list_variable[row])

        # for row in range(len(list_value)):
        #     self.grid.SetCellValue(row, 1, str(list_value[row]))

        for row in range(len(list_meaning)):
            self.grid.SetCellValue(row, 0, list_meaning[row])

        # num_list = [0,1,2,5,6,36,37,38,39]
        num_list = range(16)
        for num in num_list:
            self.grid.SetRowSize(num, 40)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add((20,20), 0)
        sizer1.Add(self.grid, 0, wx.ALIGN_RIGHT)
        # sizer1.Add(self.update_button, 0, wx.ALIGN_RIGHT)

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

        list_value = [dict_status['wrong_rx_mac_pdu_count']+' packet',
        dict_status['wrong_rx_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_count']+' packet',
        dict_status['rx_right_mac_pdu_bytes']+' bytes',
        dict_status['rx_right_mac_pdu_bps'],
        dict_status['rx_rlc_pdu_count']+' packet',
        dict_status['rx_rlc_pdu_bytes']+' bytes',
        dict_status['rx_rlc_sdu_count']+' packet',
        dict_status['rx_rlc_sdu_bytes']+' bytes',
        dict_status['total_usg_num'],
        dict_status['discard_usg_num'],
        dict_status['tx_sr_num'],
        dict_status['tx_rlc_sdu_count']+' packet',
        dict_status['tx_rlc_sdu_bytes']+' bytes',
        dict_status['tx_rlc_pdu_count']+' packet',
        dict_status['tx_rlc_pdu_bytes']+' bytes']

        for row in range(len(list_value)):
            self.grid.SetCellValue(row, 1, str(list_value[row]))

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(parent=None, id=-1)
        self.frame.Show()
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

