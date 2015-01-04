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
import traceback,time,datetime
import ConfigParser
from wx.lib.pubsub import Publisher 
import IPy

# from MatplotPanel import MatplotPanel as StatusPanel
# from StatusPanel import StatusPanel as StatusPanel
from StatusPanel_ue import StatusPanel as StatusPanel

from Audio_ue import Audio_ue as run_ue_audio
from SeniorDialog_Terminal import SeniorDialog_Terminal

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
        # self.panel_1 = MatplotPanel(self.sp)
        # self.panel_1 = StatusPanel(self.sp)
        self.panel_1 = StatusPanel(self.sp)
        self.sp.SplitVertically(self.panel,self.panel_1,700)

        self.panel.SetBackgroundColour("white")

        self.terminal_config = ConfigParser.ConfigParser()
        self.terminal_config.read("terminal.conf")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")
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
        
        rows_rx = [
        ('sync递交子帧数目 ',dict_status['sync_suf_num']+' 个'),
        ('下行DEMUX子帧数目 ',dict_status['demapper_suf_num']+' 个'),
        ('',''),
        ('RX CRC错误总包数',dict_status['wrong_rx_mac_pdu_count']+' packet'),
        ('RX CRC错误字节数',dict_status['wrong_rx_mac_pdu_bytes']+' bytes'),
        ('RX CRC正确总包数',dict_status['rx_right_mac_pdu_count']+' packet'),
        ('RX CRC正确字节数',dict_status['rx_right_mac_pdu_bytes']+' bytes'),
        ('RX CRC正确速率 ',dict_status['rx_crc_right_rate']+' B/s'),
        ('',''),
        ('MAC==>RLC总包数',dict_status['rx_rlc_pdu_count']+' packet'),
        ('MAC==>RLC字节数',dict_status['rx_rlc_pdu_bytes']+' bytes'),
        ('MAC==>RLC字节速率',dict_status['rx_mac2rlc_rate']+' B/s'),
        ('',''),
        ('RLC==>高层总包数',dict_status['rx_rlc_sdu_count']+' packet'),
        ('RLC==>高层字节数',dict_status['rx_rlc_sdu_bytes']+' bytes'),
        ('RLC==>高层字节速率',dict_status['rx_rlc2_rate']+' B/s'),
        # ('',''),
        # ('RX 丢弃调度数目',dict_status['total_usg_num']),
        # ('RX 总调度的数目',dict_status['discard_usg_num']),
        ('',''),
        ('统计数据间隔为 ',str(dict_status['rate_record_time'])+' ms'),
        ]

        rows_tx = [
        ('TX 发送的SR数目',dict_status['tx_sr_num']),
        ('TX 预补偿归一化频偏',dict_status['tx_cfo_precompensation']),
        ('',''),
        ('TX 高层==>RLC总包数',dict_status['tx_rlc_sdu_count']+' packet'),
        ('TX 高层==>RLC字节数',dict_status['tx_rlc_sdu_bytes']+' bytes'),
        ('TX 高层==>RLC字节速率',dict_status['tx_2rlc_rate']+' B/s'),
        ('',''),
        ('TX RLC==>MAC总包数',dict_status['tx_rlc_pdu_count']+' packet'),
        ('TX RLC==>MAC字节数',dict_status['tx_rlc_pdu_bytes']+' bytes'),
        ('TX RLC==>MAC字节速率',dict_status['tx_rlc2mac_rate']+' B/s'),
        ('',''),
        ('UE端丢弃调度数目 ',dict_status['discard_usg_num']),
        ('UE端总调度的数目 ',dict_status['total_usg_num']),
        ]
        for index in range(len(rows_rx)):
            self.list_rx.SetStringItem(index, 1, str(rows_rx[index][1]))

        for index in range(len(rows_tx)):
            self.list_tx.SetStringItem(index, 1, str(rows_tx[index][1])) 

        # if dict_status['flag'] == True:
        #     self.q_2.put('\nquit...')
        #     time.sleep(1)            
        #     self.p_1.terminate()
        #     print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
        #     print 'reboot...'
        #     time.sleep(2)
        #     # self.p_1.start()
        #     self.p_1 = multiprocessing.Process(name='Run_UE',
        #                             target=self.Run_UE)
        #     self.p_1.daemon = True
        #     self.p_1.start()

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
        # try: s_id_sc = self.terminal_config.get("Terminal", "s_id_sc")
        # except: s_id_sc = '10'
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
        try: s_selected_rnti = self.terminal_config.get("Terminal", "s_selected_rnti")
        except: s_selected_rnti = '61'        
        #设置连接服务器的IP地址和端口号
        self.terminal_config.read("terminal.conf")
        try: s_ip_remote = self.terminal_config.get("address", "s_ip_remote")
        except: s_ip_remote = '192.168.139.180'

        try: s_port = self.terminal_config.get("address", "s_port")
        except: s_port = '7000'

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
        # id_statictext = wx.StaticText(self.panel, -1, u"小区ID:")
        # self.id_sc = wx.SpinCtrl(self.panel, -1, s_id_sc, (-1, -1))
        # self.id_sc.SetRange(0,503)

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

        # route_list = ["192.168.200.3"]
        # route_st = wx.StaticText(self.panel, -1, u"配置Route:")
        # self.route = wx.ComboBox(self.panel, -1, s_route, wx.DefaultPosition,
        #  wx.DefaultSize, route_list, 0)

        # route_next_st = wx.StaticText(self.panel, -1, u"配置Route:")
        # self.route_next = wx.ComboBox(self.panel, -1, s_route_next, wx.DefaultPosition,
        #  wx.DefaultSize, ip_list, 0)

        rnti_list = ['61','65']
        rnti_select_st = wx.StaticText(self.panel, -1, u"RNTI选择:")
        self.rnti_select = wx.ComboBox(self.panel, -1, s_selected_rnti, wx.DefaultPosition,
         wx.DefaultSize, rnti_list, 0)

        self.detail_setup_btn = wx.Button(self.panel, -1, u"详细配置")
        self.detail_setup_btn.SetBackgroundColour('black')
        self.detail_setup_btn.SetForegroundColour('white')        
        self.Bind(wx.EVT_BUTTON, self.OnDetailSetup, self.detail_setup_btn) 

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

        # 友情提示控件
        hint_st = wx.StaticText(self.panel, -1, u"温馨提示：\n分组业务演示包含数据与视频的测试，" + 
            "\n音频通过话筒采样实现接、听;本地参数配置起决定性作用")
        hint_st.SetForegroundColour('black')
        hint_st.SetBackgroundColour('white')
        font = wx.Font(10, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)
        hint_st.SetFont(font)

        ip_st = wx.StaticText(self.panel, -1, u"IP地址 :")
        self.IPText = wx.TextCtrl(self.panel, -1, s_ip_remote)
        self.IPText.SetBackgroundColour('#c2e6f8')
        self.IPText.SetForegroundColour('black')
        port_st = wx.StaticText(self.panel, -1, u"端口号 :")  
        self.PortText = wx.TextCtrl(self.panel, -1, s_port)
        self.PortText.SetBackgroundColour('#c2e6f8')
        self.PortText.SetForegroundColour('black')        

        #连接按钮
        self.connect_button = wx.Button(self.panel, -1, u"连接")
        self.connect_button.SetBackgroundColour('black')
        self.connect_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)  
        # self.connect_button.SetDefault() 

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

        sizer_param = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        sizer_param.AddGrowableCol(1)
        sizer_param.Add(u_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.u_frequency_param, 0, wx.EXPAND)
        sizer_param.Add(d_frequency_st_param, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.d_frequency_param, 0, wx.EXPAND)
        sizer_param.Add(prb_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.prb_c, 0, wx.EXPAND)
        # sizer_param.Add(id_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        # sizer_param.Add(self.id_sc, 0, wx.EXPAND)
        sizer_param.Add(log_type_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.log_type, 0, wx.EXPAND)        
        sizer_param.Add(log_level_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.log_level, 0, wx.EXPAND)
        sizer_param.Add(ip_st_remote, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.ip, 0, wx.EXPAND)  
        # sizer_param.Add(route_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        # sizer_param.Add(self.route, 0, wx.EXPAND)
        # sizer_param.Add(route_next_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        # sizer_param.Add(self.route_next, 0, wx.EXPAND)
        sizer_param.Add(rnti_select_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer_param.Add(self.rnti_select, 0, wx.EXPAND)

        box_st_param = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'本地运行参数配置'), wx.VERTICAL)
        box_st_param.Add(sizer_param, 0, wx.ALIGN_CENTER)
        box_st_param.Add(self.detail_setup_btn, 0, wx.ALIGN_RIGHT)

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
        box_st2.Add(hint_st, 0)

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
        sizer5.Add(sizer3, 0, wx.EXPAND | wx.ALL, 1)
        sizer5.Add(sizer4, 0, wx.EXPAND | wx.ALL, 1)

        box3 = wx.BoxSizer(wx.VERTICAL)
        box3.Add(box_st_param,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box3.Add((5,5), 0)
        box3.Add(box_st2,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 0)
        box3.Add((5,5), 0)
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
        # status['ip'] = self.ip.GetValue()
        # status['route'] = self.route.GetValue()
        # status['u_freq'] = self.tb.get_ul_center_freq()/1e6
        # status['d_freq'] = self.tb.get_dl_center_freq()/1e6
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
        
        # status['flag'] = self.tb.lte_sat_dl_baseband_sync_0.is_reboot_needed()

        return status

    def get_status(self):
        status = {}
        status['disp_dl_demapper'] = self.tb.lte_sat_dl_subframe_demapper_0.get_stat().get_disp()
        status['data_dl_demapper'] = self.tb.lte_sat_dl_subframe_demapper_0.get_stat().get_data()
        status['unit_dl_demapper'] = self.tb.lte_sat_dl_subframe_demapper_0.get_stat().get_unit()
        
        status['disp_ul_mapper'] = self.tb.lte_sat_ul_subframe_mapper_0.get_stat().get_disp()
        status['data_ul_mapper'] = self.tb.lte_sat_ul_subframe_mapper_0.get_stat().get_data()
        status['unit_ul_mapper'] = self.tb.lte_sat_ul_subframe_mapper_0.get_stat().get_unit()

        status['disp_dl_sync'] = self.tb.lte_sat_dl_baseband_sync_0.get_stat().get_disp()
        status['data_dl_sync'] = self.tb.lte_sat_dl_baseband_sync_0.get_stat().get_data()
        status['unit_dl_sync'] = self.tb.lte_sat_dl_baseband_sync_0.get_stat().get_unit()

        status['disp_layer2_ue'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_disp()
        status['data_layer2_ue'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_data()
        status['unit_layer2_ue'] = self.tb.lte_sat_layer2_ue_0.get_ue_stat_info().get_unit()

        return status

    def write_param(self):
        self.u_frequency_param.Disable()
        self.d_frequency_param.Disable()
        self.prb_c.Disable()
        # self.id_sc.Disable()
        self.log_level.Disable()
        self.log_type.Disable()
        self.stop_ue_btn.Enable()
        self.ip.Disable()
        self.work_mod.Disable()
        # self.route.Disable()
        # self.route_next.Disable()
        self.rnti_select.Disable()

        #将设置好的参数写入配置文件
        self.terminal_config.read("terminal.conf")

        if "Terminal" not in self.terminal_config.sections():
            self.terminal_config.add_section("Terminal")

        self.terminal_config.set("Terminal", "s_prb_c", self.prb_c.GetValue())
        # self.terminal_config.set("Terminal", "s_id_sc", self.id_sc.GetValue())
        self.terminal_config.set("Terminal", "s_u_frequency", self.u_frequency_param.GetValue())
        self.terminal_config.set("Terminal", "s_d_frequency", self.d_frequency_param.GetValue())
        self.terminal_config.set("Terminal", "s_log_level", self.log_level.GetValue())
        self.terminal_config.set("Terminal", "s_log_type", self.log_type.GetValue())
        self.terminal_config.set("Terminal", "s_ip", self.ip.GetValue())
        # self.terminal_config.set("Terminal", "s_route", self.route.GetValue())
        # self.terminal_config.set("Terminal", "s_route_next", self.route_next.GetValue())
        self.terminal_config.set("Terminal", "s_work_mod", self.work_mod.GetValue())
        self.terminal_config.set("Terminal", "s_selected_rnti", self.rnti_select.GetValue())

        #写入配置文件
        param_file = open("terminal.conf","w")
        self.terminal_config.write(param_file)
        param_file.close()

    def setup_param(self):
        global param
        param_temp = {}
        param_temp[u'u_frequency_T'] = self.u_frequency_param.GetValue()
        param_temp[u'd_frequency_T'] = self.d_frequency_param.GetValue()
        param_temp[u'Bandwidth'] = self.prb_c.GetValue()
        param_temp[u'log_level'] = str(self.log_level.GetValue())

        if self.log_type.GetValue() == u'内存日志':
            param_temp[u'log_type'] = True
        else:
            param_temp[u'log_type'] = False

        # param = {u'n_pucch': u'0', u'work_mod': u'1', u'DMRS1_T': u'4',
        # u'Delta_ss_T': u'10', u'algorithm_T': u'Max_Log',
        # u'samp_rate_T': u'4M',u'C_SRS': u'4', u'm_part': u'2', u'n_RRC': u'10',
        # u'decision_type_T': u'soft', u'shift_T': u'1',u'IP': u'192.168.200.111',
        # u'K_TC': u'0', u'n_SRS': u'4', u'SR_periodicity': u'10',
        # u'RNTI': u'65', u'B_SRS': u'1', u't_advance': u'0', u'data_rules_T': u'1',
        # u'M_part': u'2', u'route': u'192.168.200.333', u'gain_r_T': u'10',
        # u'SRS_period': u'2',u'id_cell': 10, u'gain_s_T': u'10', u'iter_num_T': u'4',
        # u'SR_offset': u'2',u'Threshold': u'0.5', u'SRS_offset': u'0'}
        
        param.update(param_temp)

        return param

    def setup_route(self):
        tun2 = self.ip.GetValue()
        # route = self.route.GetValue()
        # route_next = self.route_next.GetValue()

        ip = IPy.IP(tun2).make_net('255.255.255.0')
        ip = ip.strNormal()

        if self.tb.lte_sat_dl_subframe_demapper_0.get_rnti() == 61:
            os.system('sudo ifconfig tun2 '+tun2)
            # os.system('sudo route add '+route+' dev tun2')
            # os.system('sudo route add '+route_next+' dev tun2')
            os.system('sudo route add -net '+ip+' dev tun2')
        else:
            os.system('sudo ifconfig tun1 '+tun2)
            # os.system('sudo route add '+route+' dev tun1')
            # os.system('sudo route add '+route_next+' dev tun1')
            os.system('sudo route add -net '+ip+' dev tun1')

    def get_device_info(self):
        pass

    def OnStartUE(self,event):
        print '########################'
        print 'start...'        
        self.start_ue_btn.Disable()
        self.stop_ue_btn.Enable()
        self.get_device_info()
        self.write_param()
        
        self.t_1 = threading.Thread(target = self.update_panel)
        self.t_1.setDaemon(True)
        self.t_1.start()

        self.q = Queue()
        self.q_2 = Queue()
        self.q_list = Queue()
        self.p_1 = multiprocessing.Process(name='Run_UE',
                                target=self.Run_UE)
        self.p_1.daemon = True
        self.p_1.start()

    def Run_UE(self):
        os.system('rm -rvf *.log *.dat *.test')
        time.sleep(2)
        param = self.setup_param()
        starttime = datetime.datetime.now()

        if self.rnti_select.GetValue() == '61':
            from ue61_ping_15prb_modify import ue61_ping_15prb as run_ue_packet
            print 'ue61_ping_15prb...'
        else:
            from ue65_ping_15prb_modify import ue65_ping_15prb as run_ue_packet
            print 'ue65_ping_15prb...'

        if self.work_mod.GetValue() == u'分组业务演示':
            self.tb = run_ue_packet(**param)
            time.sleep(5)
            self.setup_route()
        else:
            self.tb = run_ue_audio(**param)
            # self.setup_route()

        self.t_1 = threading.Thread(target = self.put_data)
        self.t_1.setDaemon(True)
        self.t_1.start()

        self.tb.start()

        print self.q_2.get()#阻塞在此处
        # print self.q_2.get_nowait()
        self.tb.stop()
        self.tb.wait()
        endtime = datetime.datetime.now()

        print '*************************************'
        print '起始时间： ' + str(starttime)
        print '结束时间： ' + str(endtime)
        print '消耗时间： ' + str(endtime - starttime)

    def update_panel(self):
        while True:
            try:
                if self.p_1.is_alive():
                    wx.CallAfter(Publisher().sendMessage, "update", self.q.get())
                    wx.CallAfter(Publisher().sendMessage, "update_list", self.q_list.get())
            except:
                # pass
                print 'self.p1..dead'
            time.sleep(1)

    def put_data(self):
        while True:
            self.q.put(self.status_process())
            self.q_list.put(self.get_status())
            time.sleep(1)

    def OnStopUE(self,event):
        self.q_2.put('\nquit...')
        time.sleep(1)

        self.OnStop_Disp()

        self.p_1.terminate()

    def OnStop_Disp(self):
        self.u_frequency_param.Enable()
        self.d_frequency_param.Enable()
        self.prb_c.Enable()
        # self.id_sc.Enable()
        self.log_level.Enable()
        self.log_type.Enable()
        self.ip.Enable()
        # self.route.Enable()
        # self.route_next.Enable()
        self.rnti_select.Enable()
        self.work_mod.Enable()

        self.stop_ue_btn.Disable()
        self.start_ue_btn.Enable()

        ############################
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

        ##############################
        self.panel_1.clear_disp()

    def OnDetailSetup(self,event):
        self.seniordialog = SeniorDialog_Terminal(None)
        self.seniordialog.ok_button.Bind(wx.EVT_BUTTON, self.OnOk)
        self.seniordialog.Bind(wx.EVT_CLOSE, self.OnCloseWindow_SDT)
        self.seniordialog.Show()
        self.detail_setup_btn.Disable()

    def OnCloseWindow_SDT(self,event):
        self.detail_setup_btn.Enable()
        self.seniordialog.Destroy()

    def OnOk(self,event):
        # 将设置好的参数写入配置文件
        self.param_config.read("param.conf")
        if "Terminal" not in self.param_config.sections():
            self.param_config.add_section("Terminal")

        self.param_config.set("Terminal", "s_rnti_a", self.seniordialog.RNTI_A.GetValue())
        self.param_config.set("Terminal", "s_rnti_b", self.seniordialog.RNTI_B.GetValue())
        self.param_config.set("Terminal", "s_t_advance_a", self.seniordialog.t_advance_A.GetValue())
        self.param_config.set("Terminal", "s_t_advance_b", self.seniordialog.t_advance_B.GetValue())
        self.param_config.set("Terminal", "s_virtual_ip_a", self.seniordialog.virtual_ip_A.GetValue())
        self.param_config.set("Terminal", "s_virtual_ip_b", self.seniordialog.virtual_ip_B.GetValue())
        self.param_config.set("Terminal", "s_select_route_a", self.seniordialog.select_route_A.GetValue())
        self.param_config.set("Terminal", "s_select_route_b", self.seniordialog.select_route_B.GetValue())
        self.param_config.set("Terminal", "s_n_pucch_a", self.seniordialog.n_pucch_A.GetValue())
        self.param_config.set("Terminal", "s_n_pucch_b", self.seniordialog.n_pucch_B.GetValue())
        self.param_config.set("Terminal", "s_data_rules", self.seniordialog.data_rules.GetValue())
        self.param_config.set("Terminal", "s_iter_num", self.seniordialog.iter_num.GetValue())
        self.param_config.set("Terminal", "s_delta_ss", self.seniordialog.Delta_ss.GetValue())
        self.param_config.set("Terminal", "s_shift", self.seniordialog.shift.GetValue())
        self.param_config.set("Terminal", "s_DMRS1", self.seniordialog.DMRS1.GetValue())
        self.param_config.set("Terminal", "s_decision_type", self.seniordialog.decision_type.GetValue())
        self.param_config.set("Terminal", "s_algorithm_c", self.seniordialog.algorithm_c.GetValue())
        self.param_config.set("Terminal", "s_gain_r_sc", self.seniordialog.Gain_r_sc.GetValue())
        self.param_config.set("Terminal", "s_gain_s_sc", self.seniordialog.Gain_s_sc.GetValue())
        self.param_config.set("Terminal", "s_samp_rate_sc", self.seniordialog.samp_rate_c.GetValue())
        self.param_config.set("Terminal", "s_c_srs_a", self.seniordialog.C_SRS_A.GetValue())
        self.param_config.set("Terminal", "s_b_srs_a", self.seniordialog.B_SRS_A.GetValue())
        self.param_config.set("Terminal", "s_n_srs_a", self.seniordialog.n_SRS_A.GetValue())
        self.param_config.set("Terminal", "s_n_rrc_a", self.seniordialog.n_RRC_A.GetValue())
        self.param_config.set("Terminal", "s_k_tc_a", self.seniordialog.K_TC_A.GetValue())
        self.param_config.set("Terminal", "s_srs_period_a", self.seniordialog.SRS_period_A.GetValue())
        self.param_config.set("Terminal", "s_srs_offset_a", self.seniordialog.SRS_offset_A.GetValue())
        self.param_config.set("Terminal", "s_sr_periodicity_a", self.seniordialog.SR_periodicity_A.GetValue())
        self.param_config.set("Terminal", "s_sr_offset_a", self.seniordialog.SR_offset_A.GetValue())
        self.param_config.set("Terminal", "s_c_srs_b", self.seniordialog.C_SRS_B.GetValue())
        self.param_config.set("Terminal", "s_b_srs_b", self.seniordialog.B_SRS_B.GetValue())
        self.param_config.set("Terminal", "s_n_srs_b", self.seniordialog.n_SRS_B.GetValue())
        self.param_config.set("Terminal", "s_n_rrc_b", self.seniordialog.n_RRC_B.GetValue())
        self.param_config.set("Terminal", "s_k_tc_b", self.seniordialog.K_TC_B.GetValue())
        self.param_config.set("Terminal", "s_srs_period_b", self.seniordialog.SRS_period_B.GetValue())
        self.param_config.set("Terminal", "s_srs_offset_b", self.seniordialog.SRS_offset_B.GetValue())
        self.param_config.set("Terminal", "s_sr_periodicity_b", self.seniordialog.SR_periodicity_B.GetValue())
        self.param_config.set("Terminal", "s_sr_offset_b", self.seniordialog.SR_offset_B.GetValue())
        self.param_config.set("Terminal", "s_t_reordering", self.seniordialog.t_Reordering.GetValue())
        self.param_config.set("Terminal", "s_t_statusprohibit", self.seniordialog.t_StatusProhibit.GetValue())
        self.param_config.set("Terminal", "s_t_pollretransmit", self.seniordialog.t_PollRetransmit.GetValue())
        self.param_config.set("Terminal", "s_maxretxthreshold", self.seniordialog.maxRetxThreshold.GetValue())
        self.param_config.set("Terminal", "s_sn_fieldlength", self.seniordialog.SN_FieldLength.GetValue())
        self.param_config.set("Terminal", "s_pollpdu", self.seniordialog.pollPDU.GetValue())
        self.param_config.set("Terminal", "s_pollbyte", self.seniordialog.pollByte.GetValue())
        # 写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        self.detail_setup_btn.Enable()
        self.seniordialog.Destroy()

    def OnConnect(self, event):
        self.write_param()

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
                        self.q_list = Queue()
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
                    wx.CallAfter(Publisher().sendMessage, "update_list", self.q_list.get())
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
        
        if self.rnti_select.GetValue() == '61':
            from ue61_ping_15prb import ue61_ping_15prb as run_ue_packet
            print 'ue61_ping_15prb...'
        else:
            from ue65_ping_15prb import ue65_ping_15prb as run_ue_packet
            print 'ue65_ping_15prb...'

        global param 
        param.update(self.setup_param())

        if param['work_mod'] == '0': 
            self.tb = run_ue_packet(**param)
            time.sleep(5)
            self.setup_route()
        else:
            self.tb = run_ue_audio(**param)

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
            self.q_list.put(self.get_status())

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
            self.q_2.put('\nquit...')
            time.sleep(1)
            self.p_1.terminate()
        except:
            pass

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
