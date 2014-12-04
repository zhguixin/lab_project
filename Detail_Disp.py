#!/usr/bin/env python
#coding=utf-8
from gnuradio import blocks
from gnuradio import audio
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio import vocoder
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes

import wx
import sys
import os,time
import threading
import ConfigParser
import multiprocessing
from multiprocessing import Queue
import socket,select
import json
from wx.lib.pubsub import Publisher

from eNB_ping_15prb_two import eNB_ping_15prb_two as run_eNB_packet
# from eNB_ping_15prb_one65 import eNB_ping_15prb_one65 as run_eNB_packet
# from eNB_ping_15prb_one61 import eNB_ping_15prb_one61 as run_eNB_packet
from Audio_eNB import Audio_eNB as run_eNB_audio

# from eNB_ping_15prb_one65_video import *
# from eNB_ping_15prb_one65_audio import *

#设置系统默认编码方式，不用下面两句，中文会乱码
reload(sys)  
sys.setdefaultencoding("utf-8")

class Detail_Disp(wx.Panel):

    def __init__(self,parent):
        wx.Panel.__init__(self, parent,style = wx.TAB_TRAVERSAL)
        self.Centre()
        self.parent = parent
        self.SetBackgroundColour("white")
        
        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        # 参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_modtype = self.param_config.get("Gateway_station", "s_modtype")
        except: s_modtype = 'QPSK'
        try: s_prb_c = self.param_config.get("Gateway_station", "s_prb_c")
        except: s_prb_c = '1.4'
        try: s_id_sc = self.param_config.get("Gateway_station", "s_id_sc")
        except: s_id_sc = '10'        
        try: s_u_frequency = self.param_config.get("Gateway_station", "s_u_frequency")
        except: s_u_frequency = '800'
        try: s_d_frequency = self.param_config.get("Gateway_station", "s_d_frequency")
        except: s_d_frequency = '900'    
        try: s_log_level = self.param_config.get("Gateway_station", "s_log_level")
        except: s_log_level = 'debug'
        try: s_log_type = self.param_config.get("Gateway_station", "s_log_type")
        except: s_log_type = '内存日志'
        try: s_ip = self.param_config.get("Gateway_station", "s_ip")
        except: s_ip = '192.168.200.3'
        try: s_route_1 = self.param_config.get("Gateway_station", "s_route_1")
        except: s_route_1 = '192.168.200.11'
        try: s_route_2 = self.param_config.get("Gateway_station", "s_route_2")
        except: s_route_2 = '192.168.200.12'
        try: s_work_mod = self.param_config.get("Gateway_station", "s_work_mod")
        except: s_work_mod = 0
        try: s_ip_remote = self.param_config.get("Address", "s_ip_remote")
        except: s_ip_remote = '192.168.139.180'
        try: s_port = self.param_config.get("Address", "s_port")
        except: s_port = '7000'

        #上行中心频率
        u_frequency_list = ['20','800','900','1000','1200']
        u_frequency_st_param = wx.StaticText(self, -1, u"上行中心频率(MHz):")
        self.u_frequency_param = wx.ComboBox(self, -1, s_u_frequency, wx.DefaultPosition,
         wx.DefaultSize, u_frequency_list, 0)

        #下行中心频率
        d_frequency_list = ['40','900','1000','1200']
        d_frequency_st_param = wx.StaticText(self, -1, u"下行中心频率(MHz):")
        self.d_frequency_param = wx.ComboBox(self, -1, s_d_frequency, wx.DefaultPosition,
         wx.DefaultSize, d_frequency_list, 0)

        PRBList = ['1.4','3']
        prb_statictext = wx.StaticText(self, -1, u"链路带宽(MHz):")
        self.prb_c = wx.ComboBox(self, -1, s_prb_c, wx.DefaultPosition, wx.DefaultSize, PRBList, 0)

        #小区ID
        id_statictext = wx.StaticText(self, -1, u"小区ID:")
        self.id_sc = wx.SpinCtrl(self, -1, s_id_sc, (-1, -1))
        self.id_sc.SetRange(0,503)

        #调制方式
        ModtypeList = ['QPSK','16QAM']
        modtype_st = wx.StaticText(self, -1, u"调制方式:")
        self.modtype = wx.ComboBox(self, -1, s_modtype, wx.DefaultPosition, wx.DefaultSize, ModtypeList, 0)

        log_type_list = [u"文件日志",u"内存日志"]
        log_type_st = wx.StaticText(self, -1, u"日志类型:")
        self.log_type = wx.ComboBox(self, -1, s_log_type,
         wx.DefaultPosition, wx.DefaultSize, log_type_list, 0)      

        log_level_list = ["debug","info" ,"notice" ,"warn" ,"error"]
        log_level_st = wx.StaticText(self, -1, u"日志级别:")
        self.log_level = wx.ComboBox(self, -1, s_log_level, wx.DefaultPosition,
         wx.DefaultSize, log_level_list, 0)

        ip_list = ["192.168.200.3"]
        ip_st = wx.StaticText(self, -1, u"配置IP:")
        self.ip = wx.ComboBox(self, -1, s_ip, wx.DefaultPosition,
         wx.DefaultSize, ip_list, 0)

        route_list = ["192.168.200.11", "192.168.200.12"]
        route_st_1 = wx.StaticText(self, -1, u"配置UE1 Route:")
        self.route_1 = wx.ComboBox(self, -1, s_route_1, wx.DefaultPosition,
         wx.DefaultSize, route_list, 0)
        route_st_2 = wx.StaticText(self, -1, u"配置UE2 Route:")
        self.route_2 = wx.ComboBox(self, -1, s_route_2, wx.DefaultPosition,
         wx.DefaultSize, route_list, 0)

        work_mod_list = [u"分组业务演示",u"音频实时交互演示"]
        work_mod_st = wx.StaticText(self, -1, u"演示模式选择:")
        self.work_mod = wx.ComboBox(self, -1, s_work_mod, wx.DefaultPosition,
         wx.DefaultSize, work_mod_list, 0)

        self.start_eNB_btn = wx.Button(self, -1, u"启动运行")
        # self.start_eNB_btn.SetBackgroundColour('black')
        # self.start_eNB_btn.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnStartENB, self.start_eNB_btn)

        self.stop_eNB_btn = wx.Button(self, -1, u"停止运行")
        self.Bind(wx.EVT_BUTTON, self.OnStopENB, self.stop_eNB_btn)
        self.stop_eNB_btn.Disable()

        # 友情提示控件
        hint_st = wx.StaticText(self, -1, u"温馨提示：\n分组业务演示包含数据与视频的测试，" + 
            "\n音频通过话筒采样实现接、听")
        hint_st.SetForegroundColour('black')
        hint_st.SetBackgroundColour('white')
        font = wx.Font(10, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)
        hint_st.SetFont(font)

        ip_st_remote = wx.StaticText(self, -1, u"IP地址 :")
        self.IPText = wx.TextCtrl(self, -1, s_ip_remote)
        self.IPText.SetBackgroundColour('#c2e6f8')
        self.IPText.SetForegroundColour('black')        
        port_st = wx.StaticText(self, -1, u"端口号 :")  
        self.PortText = wx.TextCtrl(self, -1, s_port)
        self.PortText.SetBackgroundColour('#c2e6f8')
        self.PortText.SetForegroundColour('black')        

        self.connect_button = wx.Button(self, -1, u"连接")
        self.connect_button.SetBackgroundColour('black')
        self.connect_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)

        #######开始布局############

        sizer2 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer2.AddGrowableCol(1)
        sizer2.Add(u_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.u_frequency_param, 0, wx.EXPAND)
        sizer2.Add(d_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.d_frequency_param, 0, wx.EXPAND)
        sizer2.Add(prb_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.prb_c, 0, wx.EXPAND)
        sizer2.Add(id_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.id_sc, 0, wx.EXPAND)
        sizer2.Add(modtype_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.modtype, 0, wx.EXPAND)
        sizer2.Add(log_type_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.log_type, 0, wx.EXPAND)        
        sizer2.Add(log_level_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.log_level, 0, wx.EXPAND)    
        sizer2.Add(ip_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.ip, 0, wx.EXPAND)  
        sizer2.Add(route_st_1, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.route_1, 0, wx.EXPAND)
        sizer2.Add(route_st_2, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.route_2, 0, wx.EXPAND)

        sizer_st_param = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'本地运行参数配置'), wx.VERTICAL)
        sizer_st_param.Add(sizer2,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 5)


        sizer_work_mod = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer_work_mod.Add(work_mod_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_work_mod.Add(self.work_mod, 0, wx.EXPAND)

        sizer_stop = wx.BoxSizer(wx.HORIZONTAL)
        sizer_stop.Add(self.start_eNB_btn, 0, wx.ALIGN_CENTER)  
        sizer_stop.Add((20,20), 0)
        sizer_stop.Add(self.stop_eNB_btn, 0, wx.ALIGN_CENTER)  
        sizer_stop.Add((20,20), 0)

        box_st2 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'本地运行eNB测试'), wx.VERTICAL)   
        box_st2.Add((10,10), 0)
        box_st2.Add(sizer_work_mod, 0, wx.ALIGN_CENTER)
        box_st2.Add((10,10), 0)
        box_st2.Add(sizer_stop, 0, wx.ALIGN_CENTER)
        box_st2.Add((5,5), 0)
        box_st2.Add(hint_st, 0)
        
        sizer3 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer3.AddGrowableCol(1)
        sizer3.Add(ip_st_remote, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.IPText, 3, wx.EXPAND)
        sizer3.Add(port_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.PortText, 1, wx.EXPAND)

        #连接按钮
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add((20,20), 1)
        sizer4.Add(self.connect_button, 0, wx.ALIGN_RIGHT)

        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'远程连接服务器'), wx.VERTICAL)
        sizer5.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)
        sizer5.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        sizer_st = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u''), wx.VERTICAL)
        sizer_st.Add(wx.StaticLine(self), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)
        sizer_st.Add(sizer_st_param,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 5)
        sizer_st.Add(box_st2,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 5)
        sizer_st.Add(sizer5,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 5)

        self.SetSizer(sizer_st)
        self.Fit()   

    def status_process(self):
        status = {}
        status_temp = {}
        status_temp['rx_wrong_mac_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_wrong_mac_pdu_count
        status_temp['rx_wrong_mac_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_wrong_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_count
        status_temp['rx_right_mac_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_right_mac_pdu_bps
        status_temp['rx_rlc_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_count
        status_temp['rx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_bytes
        status_temp['rx_rlc_pdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_rlc_pdu_bps
        status_temp['rx_rlc_sdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_count
        status_temp['rx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_bytes
        status_temp['rx_rlc_sdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_rlc_sdu_bps
        status_temp['tx_rlc_sdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_count
        status_temp['tx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_bytes
        status_temp['tx_rlc_sdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().tx_rlc_sdu_bps
        status_temp['tx_rlc_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().tx_rlc_pdu_count
        status_temp['tx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().tx_rlc_pdu_bytes
        status_temp['tx_usg_count'] = self.tb.lte_sat_layer2_0.get_stat_info().tx_usg_count
        status_temp['rx_real_time_ta_rnti61'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_real_time_ta_rnti61        
        status_temp['rx_real_time_ta_rnti65'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_real_time_ta_rnti65        
        status_temp['detected_ta_num_rnti61'] = self.tb.lte_sat_layer2_0.get_stat_info().detected_ta_num_rnti61        
        status_temp['detected_ta_num_rnti65'] = self.tb.lte_sat_layer2_0.get_stat_info().detected_ta_num_rnti65        
        status_temp['sync_subf_num'] = self.tb.lte_sat_layer2_0.get_stat_info().sync_subf_num        
        status_temp['dempper_suf_num'] = self.tb.lte_sat_layer2_0.get_stat_info().dempper_suf_num        
        
        status_temp['tx_2rlc'] = self.tb.lte_sat_layer2_0.get_stat_info().get_tx_2rlc()      
        status_temp['tx_rlc2mac'] = self.tb.lte_sat_layer2_0.get_stat_info().get_tx_rlc2mac()
        status_temp['rx_crc_right'] = self.tb.lte_sat_layer2_0.get_stat_info().get_rx_crc_right()
        status_temp['rx_mac2rlc'] = self.tb.lte_sat_layer2_0.get_stat_info().get_rx_mac2rlc()
        status_temp['rx_rlc2'] = self.tb.lte_sat_layer2_0.get_stat_info().get_rx_rlc2()

        status['rx_wrong_mac_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_wrong_mac_pdu_count'])
        status['rx_wrong_mac_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_wrong_mac_pdu_bytes'])
        status['rx_right_mac_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_count'])
        status['rx_right_mac_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_bytes'])
        status['rx_right_mac_pdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_right_mac_pdu_bps'])
        status['rx_rlc_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_count'])
        status['rx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_bytes'])
        status['rx_rlc_pdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_pdu_bps'])
        status['rx_rlc_sdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_count'])
        status['rx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_bytes'])
        status['rx_rlc_sdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc_sdu_bps'])
        status['tx_rlc_sdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_count'])
        status['tx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_bytes'])
        status['tx_rlc_sdu_bps'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_sdu_bps'])
        status['tx_rlc_pdu_count'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_pdu_count'])
        status['tx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc_pdu_bytes'])
        status['tx_usg_count'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_usg_count'])
        status['detected_ta_num_rnti61'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['detected_ta_num_rnti61'])
        status['detected_ta_num_rnti65'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['detected_ta_num_rnti65'])
        status['sync_subf_num'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['sync_subf_num'])
        status['dempper_suf_num'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['dempper_suf_num'])
        
        status['tx_2rlc'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_2rlc'])
        status['tx_rlc2mac'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['tx_rlc2mac'])
        status['rx_crc_right'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_crc_right'])
        status['rx_mac2rlc'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_mac2rlc'])
        status['rx_rlc2'] = self.tb.lte_sat_layer2_0.get_stat_info().data_convert(status_temp['rx_rlc2'])

        status['rate_record_time'] = self.tb.lte_sat_layer2_0.get_stat_info().rate_record_time
        status['rx_real_time_ta_rnti61'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_real_time_ta_rnti61
        status['rx_real_time_ta_rnti65'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_real_time_ta_rnti65
        status['rx_sr_num'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_sr_num
        status['rx_bsr_num'] = self.tb.lte_sat_layer2_0.get_stat_info().rx_bsr_num
        status['rx_crc_wrong_rate'] = self.tb.lte_sat_layer2_0.get_stat_info().get_rx_wrong_pdu()

        return status

    def write_param(self):
        self.u_frequency_param.Disable()
        self.d_frequency_param.Disable()
        self.prb_c.Disable()
        self.modtype.Disable()
        self.id_sc.Disable()
        self.log_level.Disable()
        self.log_type.Disable()
        self.stop_eNB_btn.Enable()
        self.ip.Disable()
        self.route_1.Disable()
        self.route_2.Disable()

        #将设置好的参数写入配置文件
        self.param_config.read("param.conf")

        if "Gateway_station" not in self.param_config.sections():
            self.param_config.add_section("Gateway_station")

        self.param_config.set("Gateway_station", "s_prb_c", self.prb_c.GetValue())
        self.param_config.set("Gateway_station", "s_id_sc", self.id_sc.GetValue())
        self.param_config.set("Gateway_station", "s_modtype", self.modtype.GetValue())
        self.param_config.set("Gateway_station", "s_u_frequency", self.u_frequency_param.GetValue())
        self.param_config.set("Gateway_station", "s_d_frequency", self.d_frequency_param.GetValue())
        self.param_config.set("Gateway_station", "s_log_level", self.log_level.GetValue())
        self.param_config.set("Gateway_station", "s_log_type", self.log_type.GetValue())
        self.param_config.set("Gateway_station", "s_ip", self.ip.GetValue())
        self.param_config.set("Gateway_station", "s_route_1", self.route_1.GetValue())
        self.param_config.set("Gateway_station", "s_route_2", self.route_2.GetValue())
        self.param_config.set("Gateway_station", "s_work_mod", self.work_mod.GetValue())
        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

    def setup_param(self):
        print 'in setup_param...'
        param_temp = {}
        param_temp[u'd_frequency_G'] = self.u_frequency_param.GetValue()
        param_temp[u'u_frequency_G'] = self.d_frequency_param.GetValue()
        param_temp[u'Bandwidth'] = self.prb_c.GetValue()
        param_temp[u'mod_type_d'] = self.modtype.GetValue()
        param_temp[u'mod_type_u'] = self.modtype.GetValue()
        param_temp[u'log_level'] = str(self.log_level.GetValue())

        if self.log_type.GetValue() == u'内存日志':
            param_temp[u'log_type'] = True
        else:
            param_temp[u'log_type'] = False        

        param = {u'Threshold': u'0.7', u'ip': u'192.168.200.11', u'work_mod': u'1',
        u'exp_code_rate_d_G': u'0.4', u'decision_type_G': u'soft', 
        u'Delta_ss_G': u'10', u'algorithm_G': u'Max_Log',
        u'm_part': u'2', u'shift_G': u'1',u'iter_num_G': u'4',
        u'exp_code_rate_u_G': u'0.4', u'gain_s_G': u'10', 
        u'M_part': u'2', u'route': u'192.168.200.3', u'samp_rate_G': u'4M',
        u'data_rules_G': u'1', u'gain_r_G': u'10',
        u'DMRS2_G': u'4', u'id_cell': 10}

        param.update(param_temp)
        return param

    def setup_route(self):
        tun0 = self.ip.GetValue()
        route_1 = self.route_1.GetValue()
        route_2 = self.route_2.GetValue()
        
        os.system('sudo ifconfig tun0 '+tun0)
        os.system('sudo echo "1">/proc/sys/net/ipv4/ip_forward')
        os.system('sudo route add '+route_1+' dev tun0')
        os.system('sudo route add '+route_2+' dev tun0')

    def OnStartENB(self,event):
        print '########################'
        print 'start...'
        self.start_eNB_btn.Disable()
        self.stop_eNB_btn.Enable()
        self.write_param()

        self.t_1 = threading.Thread(target = self.update_panel)
        self.t_1.setDaemon(True)
        self.t_1.start()
        
        self.q = Queue()
        self.p_1 = multiprocessing.Process(name='Run_ENB',
                                target=self.Run_ENB)
        self.p_1.daemon = True
        self.p_1.start()

    def Run_ENB(self):
        os.system('rm -rvf *.log *.dat *.test')
        time.sleep(2)

        param = self.setup_param()

        if self.work_mod.GetValue() == u'分组业务演示':
            self.tb = run_eNB_packet(**param)
            self.setup_route()
        else:
            self.tb = run_eNB_audio(**param)
            # self.setup_route()

        self.t_1 = threading.Thread(target = self.put_data)
        self.t_1.setDaemon(True)
        self.t_1.start()

        self.tb.start()
        self.tb.wait()

    def update_panel(self):
        while True:
            try:
                if self.p_1.is_alive():
                    wx.CallAfter(Publisher().sendMessage, "update", self.q.get())
            except:
                # pass
                print 'self.p1..dead'
            time.sleep(1)

    def put_data(self):
        while True:
            self.q.put(self.status_process())
            time.sleep(1)

    def OnStopENB(self,event):
        self.p_1.terminate()
        print 'stop...'

        self.u_frequency_param.Enable()
        self.d_frequency_param.Enable()
        self.prb_c.Enable()
        self.modtype.Enable()
        self.id_sc.Enable()
        self.log_level.Enable()
        self.log_type.Enable()
        self.ip.Enable()
        self.route_1.Enable()
        self.route_2.Enable()

        self.stop_eNB_btn.Disable()
        self.start_eNB_btn.Enable()

    def OnConnect(self, event):
        self.IPText.Disable()
        self.PortText.Disable()
        self.connect_button.Disable()
        self.param_config.read("param.conf")
        if "Address" not in self.param_config.sections():
            self.param_config.add_section("Address")

        #Address
        self.param_config.set("Address", "s_ip_remote", self.IPText.GetValue())
        self.param_config.set("Address", "s_port", self.PortText.GetValue())

        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
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
                    self.status.update(self.q.get())
                    wx.CallAfter(Publisher().sendMessage, "update", self.status)
            
            except:#pass
                print 'self.p1...dead'
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
            self.tb = run_eNB_audio()
            # os.system('sudo ifconfig tun0 192.168.200.3')
            # os.system('sudo route add 192.168.200.12 dev tun0')
        elif param['work_mod'] == '0':
            self.tb = run_eNB_packet()
            self.setup_route()
            # os.system('sudo ifconfig tun0 192.168.200.3')
            # os.system('sudo route add 192.168.200.12 dev tun0')
        elif param['work_mod'] == '2':
            self.tb = run_eNB_packet()
            self.setup_route()
            # os.system('sudo ifconfig tun0 192.168.200.3')
            # os.system('sudo route add 192.168.200.12 dev tun0')

        self.t1 = threading.Thread(target = self.monitor_forever)
        self.t1.setDaemon(True)
        self.t1.start()

        self.tb.start()
        self.tb.wait()

    def monitor_forever(self):
        
        while True:
            # 从控制界面获取参数，动态改变
            # self.tb.set_threshold(self.q.get())

            # 获取Gnuradio模块中的状态信息，传递至界面

            self.q.put(self.status_process())

            time.sleep(1)

    def stop_top_block(self):
        self.p1.terminate()
        print 'stop'

