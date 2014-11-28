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

from MatplotPanel import MatplotPanel
# from StatusPanel import StatusPanel

from ue61_ping_15prb import ue61_ping_15prb as run_ue_packet
# from ue65_ping_15prb import ue65_ping_15prb as run_ue_packet
from Audio_ue import Audio_ue as run_ue_audio

#设置系统默认编码方式，不用下面两句，中文会乱码
reload(sys)
sys.setdefaultencoding("utf-8")

param = {}
# test_data = ()

class PanelOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent,style = wx.TAB_TRAVERSAL)
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
        self.panel = wx.Panel(self.sp, style=wx.SP_3D| wx.TAB_TRAVERSAL)
        self.p1 = MatplotPanel(self.sp)
        # self.p1 = StatusPanel(self.sp)
        # self.sp.SplitVertically(self.panel,self.p1,350)
        self.sp.SplitVertically(self.panel,self.p1,700)

        self.panel.SetBackgroundColour("white")

        self.terminal_config = ConfigParser.ConfigParser()
        self.terminal_config.read("terminal.conf")
        
        #绑定窗口的关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
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
        self.bandwidth_t.SetLabel(str(dict_status['prbl']))
        self.cfo.SetLabel(str(dict_status['cfo']))
        self.fte.SetLabel(str(dict_status['fte']))
        self.pss_pos.SetLabel(str(dict_status['pss_pos']))

        # self.u_frequency.SetLabel(str(dict_status['u_freq']))
        # self.d_frequency.SetLabel(str(dict_status['d_freq']))

    def create_list(self):
        self.list_rx = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT, size=(320,450))
        self.list_tx = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT, size=(320,350))

        columns = ['名称','值']

        rows_tx = [
        ('TX 发送的SR数目','0'),
        ('TX 预补偿归一化频偏','0'),
        ('',''),
        ('TX 高层==>RLC总包数','0'),
        ('TX 高层==>RLC字节数','0'),
        ('TX 高层==>RLC字节速率','0'),
        ('',''),
        ('TX RLC==>MAC总包数','0'),
        ('TX RLC==>MAC字节数','0'),
        ('TX RLC==>MAC字节速率','0'),
        ('',''),
        ('UE端丢弃调度数目 ','0'),
        ('UE端总调度的数目 ','0'),
        ]

        rows_rx = [
        ('sync递交子帧数目 ','0'),
        ('下行DEMUX子帧数目 ','0'),
        ('',''),
        ('RX CRC错误总包数','0'),
        ('RX CRC错误字节数','0'),
        ('RX CRC正确总包数','0'),
        ('RX CRC正确字节数','0'),
        ('RX CRC正确速率 ','0'),
        ('',''),
        ('MAC==>RLC总包数','0'),
        ('MAC==>RLC字节数','0'),
        ('MAC==>RLC字节速率','0'),
        ('',''),
        ('RLC==>高层总包数','0'),
        ('RLC==>高层字节数','0'),
        ('RLC==>高层字节速率','0'),
        # ('',''),
        # ('RX 丢弃调度数目','0'),
        # ('RX 总调度的数目','0'),
        ('',''),
        ('统计数据间隔为 ','0'),
        ] 

        # Add some columns
        for col, text in enumerate(columns):
            self.list_tx.InsertColumn(col, text)
            self.list_rx.InsertColumn(col, text)

        # add the rows
        for item in rows_tx:
            index = self.list_tx.InsertStringItem(sys.maxint, item[0])
            for col, text in enumerate(item[1:]):
                self.list_tx.SetStringItem(index, col+1, text)

        for item in rows_rx:
            index = self.list_rx.InsertStringItem(sys.maxint, item[0])
            for col, text in enumerate(item[1:]):
                self.list_rx.SetStringItem(index, col+1, text)

        # set the width of the columns in various ways
        self.list_tx.SetColumnWidth(0, 200)
        self.list_tx.SetColumnWidth(1, 120)

        self.list_rx.SetColumnWidth(0, 200)
        self.list_rx.SetColumnWidth(1, 120)

    def createframe(self):
        self.create_list()

        # 参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_prb_c = self.terminal_config.get("Terminal", "s_prb_c")
        except: s_prb_c = '1.4'
        try: s_id_sc = self.terminal_config.get("Terminal", "s_id_sc")
        except: s_id_sc = '10'
        try: s_u_frequency = self.terminal_config.get("Terminal", "s_u_frequency")
        except: s_u_frequency = '800'
        try: s_d_frequency = self.terminal_config.get("Terminal", "s_d_frequency")
        except: s_d_frequency = '900'
        try: s_log_level = self.terminal_config.get("Terminal", "s_log_level")
        except: s_log_level = 'debug'
        try: s_log_type = self.terminal_config.get("Terminal", "s_log_type")
        except: s_log_type = u'文件日志'
        try: s_ip = self.terminal_config.get("Terminal", "s_ip")
        except: s_ip = '192.168.200.11'
        try: s_route = self.terminal_config.get("Terminal", "s_route")
        except: s_route = '192.168.200.3'
        try: s_route_next = self.terminal_config.get("Terminal", "s_route_next")
        except: s_route_next = '192.168.200.12'
        try: s_work_mod = self.terminal_config.get("Terminal", "s_work_mod")
        except: s_work_mod = u'分组业务演示'

        # 小区ID
        id_cell = wx.StaticText(self.panel, -1, u'小区ID:')
        self.id_cell_t = wx.StaticText(self.panel, -1)

        # RNTI
        rnti = wx.StaticText(self.panel, -1, u'RNTI:')
        self.rnti_t = wx.StaticText(self.panel, -1)

        # 系统带宽
        bandwidth = wx.StaticText(self.panel, -1, u'系统带宽:')
        self.bandwidth_t = wx.StaticText(self.panel, -1)

        #峰值位置
        pss_pos_st = wx.StaticText(self.panel, -1, u"峰值位置:")
        self.pss_pos = wx.StaticText(self.panel, -1)

        # # 上下行中心频率
        # u_frequency_st = wx.StaticText(self.panel, -1, u"上行中心频率(MHz):")
        # self.u_frequency = wx.StaticText(self.panel, -1)
        # d_frequency_st = wx.StaticText(self.panel, -1, u"下行中心频率(MHz):")
        # self.d_frequency = wx.StaticText(self.panel, -1)

        #实时载波频率偏差值
        cfo_st = wx.StaticText(self.panel, -1, u"实时载波频率偏差:")
        self.cfo = wx.StaticText(self.panel, -1)

        #实时细定时误差
        fte_st = wx.StaticText(self.panel, -1, u"实时细定时误差:")
        self.fte = wx.StaticText(self.panel, -1)

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

        #连接按钮
        self.connect_button = wx.Button(self.panel, -1, u"连接")
        self.connect_button.SetBackgroundColour('black')
        self.connect_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)  
        # self.connect_button.SetDefault() 

        #设置连接服务器的IP地址和端口号
        self.terminal_config.read("terminal.conf")
        try: s_ip_remote = self.terminal_config.get("address", "s_ip_remote")
        except: s_ip_remote = '192.168.139.180'

        try: s_port = self.terminal_config.get("address", "s_port")
        except: s_port = '7000'

        ip_st = wx.StaticText(self.panel, -1, u"IP地址 :")
        self.IPText = wx.TextCtrl(self.panel, -1, s_ip_remote)
        self.IPText.SetBackgroundColour('#c2e6f8')
        self.IPText.SetForegroundColour('black')
        port_st = wx.StaticText(self.panel, -1, u"端口号 :")  
        self.PortText = wx.TextCtrl(self.panel, -1, s_port)
        self.PortText.SetBackgroundColour('#c2e6f8')
        self.PortText.SetForegroundColour('black')        

        #上行中心频率
        u_frequency_list = ['20','800','900','1000','1200']
        u_frequency_st_param = wx.StaticText(self.panel, -1, u"上行中心频率(MHz):")
        self.u_frequency_param = wx.ComboBox(self.panel, -1, s_u_frequency, wx.DefaultPosition,
         wx.DefaultSize, u_frequency_list, 0)

        #下行中心频率
        d_frequency_list = ['40','900','1000','1200']
        d_frequency_st_param = wx.StaticText(self.panel, -1, u"下行中心频率(MHz):")
        self.d_frequency_param = wx.ComboBox(self.panel, -1, s_d_frequency, wx.DefaultPosition,
         wx.DefaultSize, d_frequency_list, 0)
        
        PRBList = ['1.4','3']
        prb_statictext = wx.StaticText(self.panel, -1, u"链路带宽(MHz):")
        self.prb_c = wx.ComboBox(self.panel, -1, s_prb_c, wx.DefaultPosition, wx.DefaultSize, PRBList, 0)

        #小区ID
        id_statictext = wx.StaticText(self.panel, -1, u"小区ID:")
        self.id_sc = wx.SpinCtrl(self.panel, -1, s_id_sc, (-1, -1))
        self.id_sc.SetRange(0,503)

        log_type_list = ["文件日志","内存日志"]
        log_type_st = wx.StaticText(self.panel, -1, u"日志类型:")
        self.log_type = wx.ComboBox(self.panel, -1, s_log_type, wx.DefaultPosition,
         wx.DefaultSize, log_type_list, 0)      

        log_level_list = ["debug","info" ,"notice" ,"warn" ,"error"]
        log_level_st = wx.StaticText(self.panel, -1, u"日志级别:")
        self.log_level = wx.ComboBox(self.panel, -1, s_log_level, wx.DefaultPosition,
         wx.DefaultSize, log_level_list, 0)

        ip_list = ["192.168.200.11", "192.168.200.12"]
        ip_st_remote = wx.StaticText(self.panel, -1, u"配置IP:")
        self.ip = wx.ComboBox(self.panel, -1, s_ip, wx.DefaultPosition,
         wx.DefaultSize, ip_list, 0)

        route_list = ["192.168.200.3"]
        route_st = wx.StaticText(self.panel, -1, u"配置Route:")
        self.route = wx.ComboBox(self.panel, -1, s_route, wx.DefaultPosition,
         wx.DefaultSize, route_list, 0)

        route_next_st = wx.StaticText(self.panel, -1, u"配置下一跳Route:")
        self.route_next = wx.ComboBox(self.panel, -1, s_route_next, wx.DefaultPosition,
         wx.DefaultSize, ip_list, 0)

        work_mod_list = [u"分组业务演示",u"音频实时交互演示"]
        work_mod_st = wx.StaticText(self.panel, -1, u"演示模式选择:")
        self.work_mod = wx.ComboBox(self.panel, -1, s_work_mod, wx.DefaultPosition,
         wx.DefaultSize, work_mod_list, 0)

        self.start_ue_btn = wx.Button(self.panel, -1, u"启动运行")
        # self.start_eNB_btn.SetBackgroundColour('black')
        # self.start_eNB_btn.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnStartUE, self.start_ue_btn)

        self.stop_ue_btn = wx.Button(self.panel, -1, u"停止运行")
        self.Bind(wx.EVT_BUTTON, self.OnStopUE, self.stop_ue_btn)
        self.stop_ue_btn.Disable()

        ###########开始布局############
        sizer1 = wx.FlexGridSizer(cols=2, hgap=1, vgap=1)
        sizer1.AddGrowableCol(1)
        sizer1.AddGrowableCol(3)
        sizer1.Add(id_cell, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.id_cell_t, 0, wx.EXPAND)
        sizer1.Add(rnti, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.rnti_t, 0, wx.EXPAND)
        sizer1.Add(bandwidth, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.bandwidth_t, 0, wx.EXPAND)            
        sizer1.Add(pss_pos_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.pss_pos, 0, wx.EXPAND)
        sizer1.Add(fte_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.fte, 0, wx.EXPAND)
        sizer1.Add(cfo_st, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.cfo, 0, wx.EXPAND)
        # sizer1.Add(u_frequency_st, 0, wx.ALIGN_CENTER_VERTICAL)
        # sizer1.Add(self.u_frequency, 0, wx.EXPAND)
        # sizer1.Add(d_frequency_st, 0, wx.ALIGN_CENTER_VERTICAL)
        # sizer1.Add(self.d_frequency, 0, wx.EXPAND)

        sizer11 = wx.FlexGridSizer(cols=2, hgap=1, vgap=1)
        sizer11.AddGrowableCol(1)
        sizer11.Add(pss_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.pss_status, 0, wx.EXPAND)
        sizer11.Add(sss_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.sss_status, 0, wx.EXPAND)
        sizer11.Add(pbch_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.pbch_status, 0, wx.EXPAND)
        sizer11.Add(process_state_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer11.Add(self.process_state, 0, wx.EXPAND)

        #高级按钮
        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'状态显示'), wx.VERTICAL)
        sizer2.Add(sizer1, 0, wx.EXPAND | wx.ALL | wx.TOP, 10)
        sizer2.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,10)
        sizer2.Add(sizer11, 0, wx.EXPAND | wx.ALL, 10)


        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL|wx.TOP, 0)

        sizer_param = wx.FlexGridSizer(cols=2, hgap=1, vgap=1)
        sizer_param.AddGrowableCol(1)
        sizer_param.Add(u_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.u_frequency_param, 0, wx.EXPAND)
        sizer_param.Add(d_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.d_frequency_param, 0, wx.EXPAND)
        sizer_param.Add(prb_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.prb_c, 0, wx.EXPAND)
        sizer_param.Add(id_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.id_sc, 0, wx.EXPAND)        
        sizer_param.Add(log_type_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.log_type, 0, wx.EXPAND)        
        sizer_param.Add(log_level_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.log_level, 0, wx.EXPAND)    
        sizer_param.Add(ip_st_remote, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.ip, 0, wx.EXPAND)  
        sizer_param.Add(route_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.route, 0, wx.EXPAND)
        sizer_param.Add(route_next_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.route_next, 0, wx.EXPAND)        

        box_st_param = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'本地运行参数配置'), wx.VERTICAL)
        box_st_param.Add(sizer_param, 0, wx.ALIGN_CENTER)

        sizer_work_mod = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        sizer_work_mod.Add(work_mod_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_work_mod.Add(self.work_mod, 0, wx.EXPAND)        

        ctrl_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        ctrl_sizer2.Add((20,20), 0)
        ctrl_sizer2.Add(self.start_ue_btn,0,wx.EXPAND | wx.ALL)
        ctrl_sizer2.Add((20,20), 0)
        ctrl_sizer2.Add(self.stop_ue_btn,0,wx.EXPAND | wx.ALL)

        box_st2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'本地运行UE测试'), wx.VERTICAL)
        box_st2.Add(sizer_work_mod, 0, wx.ALIGN_CENTER)
        box_st2.Add((10,10), 0)
        box_st2.Add(ctrl_sizer2, 0, wx.ALIGN_CENTER)
        box_st2.Add((10,10), 0)

        sizer3 = wx.FlexGridSizer(cols=2, hgap=1, vgap=1)
        sizer3.AddGrowableCol(1)
        sizer3.Add(ip_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.IPText, 1, wx.EXPAND)
        sizer3.Add(port_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.PortText, 1, wx.EXPAND)

        #连接按钮
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add((10,10), 1)
        sizer4.Add(self.connect_button, 0, wx.ALIGN_RIGHT)

        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'远程连接服务器'), wx.VERTICAL)
        sizer5.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)
        sizer5.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        box3 = wx.BoxSizer(wx.VERTICAL)
        box3.Add(box_st_param,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box3.Add((10,10), 0)
        box3.Add(box_st2,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box3.Add((10,10), 0)
        box3.Add(sizer5,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)

        box4 = wx.BoxSizer(wx.VERTICAL)
        box4.Add(box1,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box4.Add(box3,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)

        box_list = wx.BoxSizer(wx.VERTICAL)
        box_list.Add(self.list_rx, 0, wx.EXPAND|wx.TOP)
        box_list.Add(self.list_tx, 0, wx.EXPAND|wx.TOP)

        sizer_list = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'详细状态显示'), wx.VERTICAL)
        sizer_list.Add(box_list, 0, wx.EXPAND | wx.ALL, 10)

        box_all = wx.BoxSizer(wx.HORIZONTAL)
        box_all.Add(box4,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box_all.Add(sizer_list,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)

        #自动调整界面尺寸
        # self.panel.SetSizer(box4)
        self.panel.SetSizer(box_all)

    def status_process(self):
        status = {}
        status_temp = {}
        status_temp['wrong_rx_mac_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_count
        status_temp['wrong_rx_mac_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().wrong_rx_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_count
        status_temp['rx_right_mac_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bytes
        status_temp['rx_right_mac_pdu_bps'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rx_right_mac_pdu_bps
        status_temp['rx_rlc_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_count
        status_temp['rx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_pdu_bytes
        status_temp['rx_rlc_sdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_count
        status_temp['rx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rx_rlc_sdu_bytes
        status_temp['sync_suf_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().sync_suf_num
        status_temp['demapper_suf_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().demapper_suf_num

        status_temp['total_usg_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().total_usg_num
        status_temp['discard_usg_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().discard_usg_num
        
        status_temp['tx_2rlc_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_tx_2rlc_rate()
        status_temp['tx_rlc2mac_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_tx_rlc2mac_rate()
        status_temp['rx_crc_right_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_rx_crc_right_rate()
        status_temp['rx_mac2rlc_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_rx_mac2rlc_rate()
        status_temp['rx_rlc2_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_rx_rlc2_rate()

        status_temp['tx_rlc_sdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_count
        status_temp['tx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_sdu_bytes
        status_temp['tx_rlc_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_count
        status_temp['tx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().tx_rlc_pdu_bytes        
        status['cell_id'] = self.tb.lte_sat_dl_baseband_sync_0.get_cell_id()
        status['prbl'] = self.tb.lte_sat_dl_baseband_sync_0.get_prbl()
        status['pss_status'] = self.tb.lte_sat_dl_baseband_sync_0.get_pss_status()
        status['sss_status'] = self.tb.lte_sat_dl_baseband_sync_0.get_sss_status()
        status['pbch_status'] = self.tb.lte_sat_dl_baseband_sync_0.get_pbch_status()
        status['process_state'] = self.tb.lte_sat_dl_baseband_sync_0.get_process_state()
        status['cfo'] = self.tb.lte_sat_dl_baseband_sync_0.get_cfo()
        status['fte'] = self.tb.lte_sat_dl_baseband_sync_0.get_fte()
        status['pss_pos'] = self.tb.lte_sat_dl_baseband_sync_0.get_pss_pos()

        status['fn'] = self.tb.lte_sat_dl_subframe_demapper_0.get_fn()
        status['sfn'] = self.tb.lte_sat_dl_subframe_demapper_0.get_sfn()
        status['fer'] = self.tb.lte_sat_dl_subframe_demapper_0.get_fer()
        status['rnti'] = self.tb.lte_sat_dl_subframe_demapper_0.get_rnti()

        status['pdu_sum'] = self.tb.lte_sat_layer2_ue_0.get_mac_pdu_sum()
        status['layer2_ue_fer'] = self.tb.lte_sat_layer2_ue_0.get_fer()

        status['ue_stat_info_0'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info_string(0)
        status['ue_stat_info_1'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info_string(1)

        # status['ip'] = '192.168.200.12'
        # status['route'] = '192.168.200.3'
        status['ip'] = self.ip.GetValue()
        status['route'] = self.route.GetValue()
        status['u_freq'] = self.tb.get_ul_center_freq()/1e6
        status['d_freq'] = self.tb.get_dl_center_freq()/1e6
        status['wrong_rx_mac_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_count'])
        status['wrong_rx_mac_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['wrong_rx_mac_pdu_bytes'])
        status['rx_right_mac_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_count'])
        status['rx_right_mac_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bytes'])
        status['rx_right_mac_pdu_bps'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_right_mac_pdu_bps'])
        status['rx_rlc_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_count'])
        status['rx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_pdu_bytes'])
        status['rx_rlc_sdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_count'])
        status['rx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc_sdu_bytes'])
        status['sync_suf_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['sync_suf_num'])
        status['demapper_suf_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['demapper_suf_num'])

        status['total_usg_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['total_usg_num'])
        status['discard_usg_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['discard_usg_num'])
        status['tx_sr_num'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().tx_sr_num
        status['tx_cfo_precompensation'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().tx_cfo_precompensation
        status['rate_record_time'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().rate_record_time

        status['tx_rlc_sdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_count'])
        status['tx_rlc_sdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_sdu_bytes'])
        status['tx_rlc_pdu_count'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_count'])
        status['tx_rlc_pdu_bytes'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc_pdu_bytes'])        
        
        status['tx_2rlc_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_2rlc_rate'])        
        status['tx_rlc2mac_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['tx_rlc2mac_rate'])        
        status['rx_crc_right_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_crc_right_rate'])
        status['rx_mac2rlc_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_mac2rlc_rate'])
        status['rx_rlc2_rate'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().data_convert(status_temp['rx_rlc2_rate'])
        return status        

    def write_param(self):
        self.u_frequency_param.Disable()
        self.d_frequency_param.Disable()
        self.prb_c.Disable()
        self.id_sc.Disable()
        self.log_level.Disable()
        self.log_type.Disable()
        self.stop_ue_btn.Enable()
        self.ip.Disable()
        self.route.Disable()
        self.route_next.Disable()

        #将设置好的参数写入配置文件
        self.terminal_config.read("terminal.conf")

        if "Terminal" not in self.terminal_config.sections():
            self.terminal_config.add_section("Terminal")

        self.terminal_config.set("Terminal", "s_prb_c", self.prb_c.GetValue())
        self.terminal_config.set("Terminal", "s_id_sc", self.id_sc.GetValue())
        self.terminal_config.set("Terminal", "s_u_frequency", self.u_frequency_param.GetValue())
        self.terminal_config.set("Terminal", "s_d_frequency", self.d_frequency_param.GetValue())
        self.terminal_config.set("Terminal", "s_log_level", self.log_level.GetValue())
        self.terminal_config.set("Terminal", "s_log_type", self.log_type.GetValue())
        self.terminal_config.set("Terminal", "s_ip", self.ip.GetValue())
        self.terminal_config.set("Terminal", "s_route", self.route.GetValue())
        self.terminal_config.set("Terminal", "s_route_next", self.route_next.GetValue())
        self.terminal_config.set("Terminal", "s_work_mod", self.work_mod.GetValue())
        #写入配置文件
        param_file = open("terminal.conf","w")
        self.terminal_config.write(param_file)
        param_file.close()

    def setup_param(self):
        print 'in setup_param...'
        ul_center_freq = int(self.u_frequency_param.GetValue())
        dl_center_freq = int(self.d_frequency_param.GetValue())
        cell_id = int(self.id_sc.GetValue())
        log_level = str(self.log_level.GetValue())

        if self.log_type.GetValue() == u'内存日志':
            flag = True
        else:
            flag = False

        if self.prb_c.GetValue() == '1.4':
            prbl = 6
            fftl = 128
            samp_rate = 2e6
        else:
            prbl = 15
            fftl = 256
            samp_rate = 4e6

        print prbl,fftl,samp_rate,cell_id, ul_center_freq,dl_center_freq,
        print flag,log_level

        self.tb.set_prbl(prbl)
        self.tb.set_fftl(fftl)
        self.tb.set_samp_rate(samp_rate)
        self.tb.set_ul_center_freq(ul_center_freq*1e6)
        self.tb.set_dl_center_freq(dl_center_freq*1e6)
        self.tb.variable_ue_config_0.set_logger(flag, log_level)

    def setup_route(self):
        tun2 = self.ip.GetValue()
        route = self.route.GetValue()
        route_next = self.route_next.GetValue()

        if self.tb.lte_sat_dl_subframe_demapper_0.get_rnti() == 61:
            os.system('sudo ifconfig tun2 '+tun2)
            os.system('sudo route add '+route+' dev tun2')
            os.system('sudo route add '+route_next+' dev tun2')
        else:
            os.system('sudo ifconfig tun1 '+tun2)
            os.system('sudo route add '+route+' dev tun1')
            os.system('sudo route add '+route_next+' dev tun1')

    def OnStartUE(self,event):
        self.start_ue_btn.Disable()
        self.stop_ue_btn.Enable()
        self.write_param()

        self.t_1 = threading.Thread(target = self.update_panel)
        self.t_1.setDaemon(True)
        self.t_1.start()        

        self.q = Queue()
        self.p_1 = multiprocessing.Process(name='Run_UE',
                                target=self.Run_UE)
        self.p_1.daemon = True
        self.p_1.start()

    def Run_UE(self):
        os.system('rm -rvf *.log *.dat *.test')
        time.sleep(2)

        if self.work_mod.GetValue() == u'分组业务演示':
            self.tb = run_ue_packet()
            self.setup_route()
        else:
            self.tb = run_ue_audio()
            # self.setup_route()            

        self.setup_param()

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

    def OnStopUE(self,event):
        self.p_1.terminate()

        self.u_frequency_param.Enable()
        self.d_frequency_param.Enable()
        self.prb_c.Enable()
        self.id_sc.Enable()
        self.log_level.Enable()
        self.log_type.Enable()
        self.ip.Enable()
        self.route.Enable()
        self.route_next.Enable()

        self.stop_ue_btn.Disable()
        self.start_ue_btn.Enable()

    def OnConnect(self, event):
        self.IPText.Disable()
        self.PortText.Disable()
        self.connect_button.Disable()
        self.terminal_config.read("terminal.conf")
        if "address" not in self.terminal_config.sections():
            self.terminal_config.add_section("address")

        #address
        self.terminal_config.set("address", "s_ip_remote", self.IPText.GetValue())
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
        time.sleep(2)
        global param 
        if param['work_mod'] == '2': 
            self.tb = run_ue_packet()
            self.setup_route()
            # os.system('sudo ifconfig tun1 192.168.200.12')
            # os.system('sudo route add 192.168.200.3 tun1')
        elif param['work_mod'] == '0':
            self.tb = run_ue_packet()
            self.setup_route()
        elif param['work_mod'] == '1':
            self.tb = run_ue_audio()
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
            self.q.put(self.status_process())

            time.sleep(1) 

    def stop_top_block(self):
        self.p1.terminate()

        self.pss_status.state_red()
        self.sss_status.state_red()
        self.pbch_status.state_red()
        self.process_state.state_red()
        self.cfo.SetLabel('0')
        self.fte.SetLabel('0')
        self.pss_pos.SetLabel('0')
        # self.virtual_ip_t.SetLabel('')
        # self.select_route_t.SetLabel('')
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
        except:
            self.Destroy()

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
