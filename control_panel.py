#!/usr/bin/env python
#coding=utf-8
#################################
#   Copyright 2014.6.10
#       fly_vedio 
#   @author: zhguixin@163.com
#################################
import wx
import wx.grid
import sys
import threading  
import socket,select
import json
import time
import Queue
import ConfigParser
from wx.lib.pubsub import Publisher 

#设置系统默认编码方式，不用下面两句，中文会乱码
reload(sys)  
sys.setdefaultencoding("utf-8")

from SeniorDialog_Gateway import SeniorDialog_Gateway
from SeniorDialog_Terminal import SeniorDialog_Terminal

#定义一些全局变量
param = {}
param_T = {}
param_TA = {}
param_TB = {}
param_G = {}

class Terminal(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        #创建面板
        self.CreatePanel()

    def CreatePanel(self):

        #参数从文件中读取并初始化，如果初始文件不存在这个参数的值则用默认值
        try: s_u_frequency = self.param_config.get("Terminal", "s_u_frequency")
        except: s_u_frequency = '800'

        try: s_d_frequency = self.param_config.get("Terminal", "s_d_frequency")
        except: s_d_frequency = '900'

        try: s_m_part = self.param_config.get("Terminal", "s_m_part")
        except: s_m_part = '2'

        try: s_bigm_part = self.param_config.get("Terminal", "s_bigm_part")
        except: s_bigm_part = '2'

        try: s_threshold = self.param_config.get("Terminal", "s_threshold")
        except: s_threshold = '0.85'

        #上行中心频率
        u_frequency_list = ['20','800','900','1000','1200']
        u_frequency_st = wx.StaticText(self, -1, u"上行中心频率(MHz):")
        self.u_frequency = wx.ComboBox(self, -1, s_u_frequency, wx.DefaultPosition,
         wx.DefaultSize, u_frequency_list, 0)

        #下行中心频率
        d_frequency_list = ['40','900','1000','1200']
        d_frequency_st = wx.StaticText(self, -1, u"下行中心频率(MHz):")
        self.d_frequency = wx.ComboBox(self, -1, s_d_frequency, wx.DefaultPosition,
         wx.DefaultSize, d_frequency_list, 0)

        # m_part优化算法插零数
        m_part_list = ['1','2','4']
        m_part_st = wx.StaticText(self, -1, u"m_part优化算法插零数:")
        self.m_part = wx.ComboBox(self, -1, s_m_part, wx.DefaultPosition, wx.DefaultSize, m_part_list, 0)

        # M_part算法分段数
        M_part_list = ['1','2','4','8']
        M_part_st = wx.StaticText(self, -1, u"M_part算法分段数:")
        self.M_part = wx.ComboBox(self, -1, s_bigm_part, wx.DefaultPosition, wx.DefaultSize, M_part_list, 0)

        #阈值
        Threshold_st = wx.StaticText(self, -1, u"阈值:")
        self.Threshold = wx.TextCtrl(self, -1, s_threshold)

        #高级按钮
        self.senior_button = wx.Button(self, -1, u"高级")
        self.senior_button.SetBackgroundColour('black')
        self.senior_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Senior,self.senior_button)

        #######开始布局############
        #参数窗口
        sizer2 = wx.FlexGridSizer(cols=2, hgap=10, vgap=20)
        sizer2.AddGrowableCol(1)
        sizer2.Add(u_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.u_frequency, 0, wx.EXPAND)
        sizer2.Add(d_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.d_frequency, 0, wx.EXPAND)
        sizer2.Add(m_part_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.m_part, 0, wx.EXPAND)
        sizer2.Add(M_part_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.M_part, 0, wx.EXPAND)
        sizer2.Add(Threshold_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Threshold, 0, wx.EXPAND)

        #高级按钮
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add((20,20), 1)
        sizer3.Add(self.senior_button, 0, wx.ALIGN_RIGHT)

        #添加参数子块，带边框的模块布局，包含参数和高级按钮
        sizer1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'重要参数'), wx.VERTICAL)
        sizer1.Add(sizer2, 0, wx.EXPAND | wx.ALL, 15)
        # sizer1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        #box1垂直布局,box1即左半界面
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)
        box1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 5)

        #自动调整界面尺寸
        self.SetSizer(box1)
        box1.Fit(self)
        box1.SetSizeHints(self)

    def Senior(self,event):
        self.seniordialog = SeniorDialog_Terminal(None)
        self.seniordialog.ok_button.Bind(wx.EVT_BUTTON, self.OnOk)
        self.seniordialog.Bind(wx.EVT_CLOSE, self.OnCloseWindow_SDT)
        self.seniordialog.Show()
        # self.seniordialog.ShowModal()
        self.senior_button.Disable()

    def OnCloseWindow_SDT(self,event):
        self.senior_button.Enable()
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
        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        self.senior_button.Enable()
        self.seniordialog.Destroy()

class Gateway_station(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        # 创建面板
        self.CreatePanel()

    def CreatePanel(self):

        # 参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_prb_c = self.param_config.get("Gateway_station", "s_prb_c")
        except: s_prb_c = '1.4'

        try: s_id_sc = self.param_config.getint("Gateway_station", "s_id_sc")
        except: s_id_sc = 10

        try: s_modtype_u = self.param_config.get("Gateway_station", "s_modtype_u")
        except: s_modtype_u = 'QPSK'

        try: s_modtype_d = self.param_config.get("Gateway_station", "s_modtype_d")
        except: s_modtype_d = 'QPSK'

        try: s_u_frequency = self.param_config.get("Gateway_station", "s_u_frequency")
        except: s_u_frequency = '800'

        try: s_d_frequency = self.param_config.get("Gateway_station", "s_d_frequency")
        except: s_d_frequency = '900'

        # 链路带宽
        PRBList = ['1.4','3']
        prb_statictext = wx.StaticText(self, -1, u"链路带宽(MHz):")
        self.prb_c = wx.ComboBox(self, -1, s_prb_c, wx.DefaultPosition, wx.DefaultSize, PRBList, 0)

        # 小区ID
        id_statictext = wx.StaticText(self, -1, u"小区ID:")
        self.id_sc = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.id_sc.SetRange(0,503)
        self.id_sc.SetValue(s_id_sc)

        # 调制方式
        ModtypeList = ['QPSK','16QAM']
        modtype_st_u = wx.StaticText(self, -1, u"上行调制方式:")
        self.modtype_u = wx.ComboBox(self, -1, s_modtype_u, wx.DefaultPosition, wx.DefaultSize, ModtypeList, 0)

        modtype_st_d = wx.StaticText(self, -1, u"下行调制方式:")
        self.modtype_d = wx.ComboBox(self, -1, s_modtype_d, wx.DefaultPosition, wx.DefaultSize, ModtypeList, 0)

        # 上行中心频率
        u_frequency_list = ['20','800','900','1000','1200']
        u_frequency_st = wx.StaticText(self, -1, u"上行中心频率(MHz):")
        self.u_frequency = wx.ComboBox(self, -1, s_u_frequency, wx.DefaultPosition,
         wx.DefaultSize, u_frequency_list, 0)

        # 下行中心频率
        d_frequency_list = ['40','900','1000','1200']
        d_frequency_st = wx.StaticText(self, -1, u"下行中心频率(MHz):")
        self.d_frequency = wx.ComboBox(self, -1, s_d_frequency, wx.DefaultPosition,
         wx.DefaultSize, d_frequency_list, 0)

        # 高级按钮
        self.senior_button = wx.Button(self, -1, u"高级")
        self.senior_button.SetBackgroundColour('black')
        self.senior_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Senior,self.senior_button)

        #######开始布局############
        # 参数窗口
        sizer2 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer2.AddGrowableCol(1)
        sizer2.Add(prb_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.prb_c, 0, wx.EXPAND)
        sizer2.Add(modtype_st_u, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.modtype_u, 0, wx.EXPAND)
        sizer2.Add(modtype_st_d, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.modtype_d, 0, wx.EXPAND)
        sizer2.Add(id_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.id_sc, 0, wx.EXPAND)
        sizer2.Add(u_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.u_frequency, 0, wx.EXPAND)
        sizer2.Add(d_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.d_frequency, 0, wx.EXPAND)

        # 高级按钮
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add((20,20), 1)
        sizer3.Add(self.senior_button, 0, wx.ALIGN_RIGHT)

        # 添加参数子块，带边框的模块布局，包含参数和高级按钮
        sizer1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'重要参数'), wx.VERTICAL)
        sizer1.Add(sizer2, 0, wx.EXPAND | wx.ALL, 15)
        # sizer1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        # box1垂直布局,box1即左半界面
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)
        box1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 5)

        # 自动调整界面尺寸
        self.SetSizer(box1)
        box1.Fit(self)
        box1.SetSizeHints(self)

    def Senior(self,event):
        self.seniordialog = SeniorDialog_Gateway(None)
        self.seniordialog.ok_button.Bind(wx.EVT_BUTTON, self.OnOk)
        self.seniordialog.Bind(wx.EVT_CLOSE, self.OnCloseWindow_SDG)
        # self.seniordialog.ShowModal()
        self.seniordialog.Show()
        self.senior_button.Disable()

    def OnCloseWindow_SDG(self,event):
        self.senior_button.Enable()
        self.seniordialog.Destroy()

    def OnOk(self,event):
        # 将设置好的参数写入配置文件
        self.param_config.read("param.conf")

        if "Gateway_station" not in self.param_config.sections():
            self.param_config.add_section("Gateway_station")

        self.param_config.set("Gateway_station", "s_data_rules", self.seniordialog.data_rules.GetValue())
        self.param_config.set("Gateway_station", "s_iter_num", self.seniordialog.iter_num.GetValue())
        self.param_config.set("Gateway_station", "s_delta_ss", self.seniordialog.Delta_ss.GetValue())
        self.param_config.set("Gateway_station", "s_shift", self.seniordialog.shift.GetValue())
        self.param_config.set("Gateway_station", "s_DMRS2", self.seniordialog.DMRS2.GetValue())
        self.param_config.set("Gateway_station", "s_decision_type", self.seniordialog.decision_type.GetValue())
        self.param_config.set("Gateway_station", "s_algorithm_c", self.seniordialog.algorithm_c.GetValue())
        self.param_config.set("Gateway_station", "s_gain_r_sc", self.seniordialog.Gain_r_sc.GetValue())
        self.param_config.set("Gateway_station", "s_gain_s_sc", self.seniordialog.Gain_s_sc.GetValue())
        self.param_config.set("Gateway_station", "s_exp_code_rate_u_sc", self.seniordialog.exp_code_rate_u.GetValue())
        self.param_config.set("Gateway_station", "s_exp_code_rate_d_sc", self.seniordialog.exp_code_rate_d.GetValue())
        self.param_config.set("Gateway_station", "s_samp_rate_sc", self.seniordialog.samp_rate_c.GetValue())
        # self.param_config.set("Gateway_station", "s_virtual_ip_sc", self.seniordialog.virtual_ip.GetValue())
        # self.param_config.set("Gateway_station", "s_select_route_sc", self.seniordialog.select_route.GetValue())
        self.param_config.set("Gateway_station", "s_t_reordering", self.seniordialog.t_Reordering.GetValue())
        self.param_config.set("Gateway_station", "s_t_statusprohibit", self.seniordialog.t_StatusProhibit.GetValue())
        self.param_config.set("Gateway_station", "s_t_pollretransmit", self.seniordialog.t_PollRetransmit.GetValue())
        self.param_config.set("Gateway_station", "s_maxretxthreshold", self.seniordialog.maxRetxThreshold.GetValue())
        self.param_config.set("Gateway_station", "s_sn_fieldlength", self.seniordialog.SN_FieldLength.GetValue())
        self.param_config.set("Gateway_station", "s_pollpdu", self.seniordialog.pollPDU.GetValue())
        self.param_config.set("Gateway_station", "s_pollbyte", self.seniordialog.pollByte.GetValue())
        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        self.senior_button.Enable()
        self.seniordialog.Destroy()

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
        wx.Frame.__init__(self, None, title=u"控制界面")
        self.Centre()
        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        
        #创建面板
        self.createframe()

        # 创建一个pubsub接收器,用于接收从子线程传递过来的消息
        Publisher().subscribe(self.updateDisplay, "update")
        Publisher().subscribe(self.updateDisplay_t, "update_t")

    def createframe(self):
        #绑定窗口的关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        #创建状态栏
        # self.panel.Bind(wx.EVT_MOTION, self.OnDataMotion)
        self.statusbar = self.CreateStatusBar()
        #将状态栏分割为2个区域,比例为1:1
        self.statusbar.SetFieldsCount(2)  
        self.statusbar.SetStatusWidths([-1, -1])

        #启动按钮
        self.start_button = wx.Button(self.panel, -1, u"启动")
        self.start_button.SetBackgroundColour((0, 0, 0, 255))
        self.start_button.SetForegroundColour(wx.WHITE)
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.start_button) 
        self.start_button.Disable()

        #停止按钮
        self.stop_button = wx.Button(self.panel, -1, u"停止")
        self.stop_button.SetBackgroundColour((0, 0, 0, 255))
        self.stop_button.SetForegroundColour(wx.WHITE)
        self.Bind(wx.EVT_BUTTON, self.OnStop, self.stop_button) 
        self.stop_button.Disable()

        #监听按钮
        self.monitor_button = wx.Button(self.panel, -1, u"监听")
        self.monitor_button.SetBackgroundColour('black')
        self.monitor_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnMonitor, self.monitor_button)  
        # self.monitor_button.SetDefault() 

        #配置按钮
        self.config_button = wx.Button(self.panel, -1, u"配置")
        self.config_button.SetBackgroundColour('black')
        self.config_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.OnConfig,self.config_button)

        #设置IP地址和端口号
        self.param_config.read("param.conf")
        try: s_ip = self.param_config.get("address", "s_ip")
        except: s_ip = '192.168.139.180'

        try: s_port = self.param_config.get("address", "s_port")
        except: s_port = '7000'

        try: s_num = self.param_config.getint("work_mod", "s_num")
        except: s_num = 0

        ip_st = wx.StaticText(self.panel, -1, u"IP地址 :")
        self.IPText = wx.TextCtrl(self.panel, -1, s_ip)  
        # self.IPText.SetBackgroundColour('#c2e6f8')
        # self.IPText.SetForegroundColour('black')
        port_st = wx.StaticText(self.panel, -1, u"端口号 :")
        self.PortText = wx.TextCtrl(self.panel, -1, s_port)
        # self.PortText.SetBackgroundColour('#c2e6f8')
        # self.PortText.SetForegroundColour('black')

        # 在面板上创建一个notebook
        nb = wx.Notebook(self.panel)
        self.page1 = Gateway_station(nb)
        self.page2 = Terminal(nb)
        nb.AddPage(self.page1, u"信关站")
        nb.AddPage(self.page2, u"终端")

        #状态显示文本框
        gateway_st = wx.StaticText(self.panel, -1, "信关站:")  
        self.panel_gateway = PanelOne(self.panel)

        terminal_st_A = wx.StaticText(self.panel, -1, "终端A:")  
        self.panel_terminal_A = PanelOne(self.panel)

        terminal_st_B = wx.StaticText(self.panel, -1, "终端B:")  
        self.panel_terminal_B = PanelOne(self.panel)

        self.DisplayText = wx.TextCtrl(self.panel, -1, '',   
                size=(250, 520), style=wx.TE_MULTILINE | wx.TE_READONLY) 
        self.DisplayText.SetBackgroundColour('gray')

        #模式选择
        work_mod_list = ['分组业务演示', '音频业务演示']
        self.work_mod = wx.RadioBox(self.panel, -1, "业务模式", wx.DefaultPosition, wx.DefaultSize,
                        work_mod_list, 2, wx.RA_SPECIFY_COLS)
        self.work_mod.SetBackgroundColour((250,250,250,255))
        self.work_mod.SetSelection(s_num)

        #启动、停止、监听、配置按钮水平布局
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.monitor_button)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.config_button)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.start_button)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.stop_button)
        sizer1.Add((20,20), 1)

        sizer2 = wx.FlexGridSizer(cols=4, hgap=10, vgap=10)
        sizer2.AddGrowableCol(1)
        sizer2.Add(ip_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.IPText, 0, wx.EXPAND)
        sizer2.Add(port_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.PortText, 0, wx.EXPAND)

        sizer3 = wx.FlexGridSizer(cols=6, hgap=10, vgap=10)
        sizer3.AddGrowableCol(1)
        sizer3.AddGrowableCol(3)
        sizer3.Add(gateway_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.panel_gateway, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(terminal_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.panel_terminal_A, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(terminal_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.panel_terminal_B, 1, wx.ALIGN_CENTER_VERTICAL)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(nb, 0, wx.EXPAND | wx.ALL, 10)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL, 10)
        box1.Add(self.work_mod,0,wx.EXPAND | wx.ALL, 10)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,10)
        box1.Add(sizer1,0,wx.EXPAND | wx.ALL, 10)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)

        box2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'状态显示'), wx.VERTICAL)
        box2.Add(self.DisplayText, 0, wx.EXPAND | wx.ALL, 10)
        box2.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(box1, 0, wx.EXPAND | wx.ALL, 20)
        box.Add(box2, 1, wx.EXPAND | wx.ALL, 20)

        #自动调整界面尺寸
        self.panel.SetSizer(box)
        box.Fit(self)
        box.SetSizeHints(self)

    # def OnDataMotion(self, event):  
          
    #     #设置状态栏1内容  
        # self.statusbar.SetStatusText(u"鼠标位置：" + str(event.GetPositionTuple()), 0)
        # self.statusbar.SetStatusText(u"误码率：" + str(), 0)
    #     self.statusbar.SetStatusText(u"误码率：", 0)  
          
    #     #设置状态栏2内容
    #     self.statusbar.SetStatusText(u"误帧率：", 1)  
     
    #     #设置状态栏3内容  
    #     self.statusbar.SetStatusText(u"信息速率：", 2)  
               
    #     event.Skip()

    def updateDisplay(self, msg): 
        """
        从线程接收数据并且在界面更新显示
        """
        self.DisplayText.AppendText(msg.data)

    def updateDisplay_t(self, msg): 
        """
        从线程接收数据并且在界面更新显示
        """
        self.status = msg.data
        
        # if len(self.clients)==2:
        #     self.panel_terminal_A.state_green()
        #     self.panel_terminal_B.state_green()
        # elif len(self.clients)==1:
        #     self.panel_terminal_A.state_green()
        #     self.panel_terminal_B.state_red()
        # elif len(self.clients)==0:
        #     self.panel_terminal_A.state_red()
        #     self.panel_terminal_B.state_red()

        if self.status.has_key('A_ip'):
            self.panel_terminal_A.state_green()
        else:
            self.panel_terminal_A.state_red()

        if self.status.has_key('B_ip'):
            self.panel_terminal_B.state_green()
        else:
            self.panel_terminal_B.state_red()

        if self.status.has_key('gateway'):
            self.panel_gateway.state_green()
        else:
            self.panel_gateway.state_red()

        if self.work_mod.GetSelection()==0:
            try:
                self.statusbar.SetStatusText(u"误码率："+str(self.status['get_ber']), 0)
                self.statusbar.SetStatusText(u"误帧率："+str(self.status['get_fer']), 1)
            except:
                pass
        else:
            self.statusbar.SetStatusText(u"误码率：", 0)
            self.statusbar.SetStatusText(u"误帧率：", 1)

    def OnStart(self,event):
        ###############page1#################
        self.page1.prb_c.Disable()
        self.page1.modtype_u.Disable()
        self.page1.modtype_d.Disable()
        self.page1.id_sc.Disable()
        self.page1.u_frequency.Disable()
        self.page1.d_frequency.Disable()
        ###############page2#################
        self.page2.u_frequency.Disable()
        self.page2.d_frequency.Disable()
        self.page2.m_part.Disable()
        self.page2.M_part.Disable()
        self.page2.Threshold.Disable()
        #############work_mod################
        self.work_mod.Disable()
        try:
            self.start_button.Disable()
            self.stop_button.Enable()
            for s in self.inputs:
                if s is self.server:
                    pass
                else:
                    s.send('start_block')
                    self.DisplayText.AppendText(u'启动...\n')
        except:
            print "请先建立连接"
            self.DisplayText.AppendText(u'请先建立连接...\n')

    def OnStop(self,event):
        ###############page1#################
        self.page1.prb_c.Enable()
        self.page1.modtype_u.Enable()
        self.page1.modtype_d.Enable()
        self.page1.id_sc.Enable()
        self.page1.u_frequency.Enable()
        self.page1.d_frequency.Enable()
        ###############page2#################
        self.page2.u_frequency.Enable()
        self.page2.d_frequency.Enable()
        self.page2.m_part.Enable()
        self.page2.M_part.Enable()
        self.page2.Threshold.Enable()
        #############work_mod################
        self.work_mod.Enable()
        try:
            self.stop_button.Disable()
            self.start_button.Enable()
            for s in self.inputs:
                if s is self.server:
                    pass
                else:
                    s.send('stop_block')
                    self.DisplayText.AppendText(u'停止...\n')
        except:
            print "请先建立连接"
            self.DisplayText.AppendText(u'请先建立连接...\n')

    def OnConfig(self,event):
        self.start_button.Enable()
        self.stop_button.Enable()
        self.param_config.read("param.conf")
        if "work_mod" not in self.param_config.sections():
            self.param_config.add_section("work_mod")

        #work_mod
        self.param_config.set("work_mod", "s_num", self.work_mod.GetSelection())

        if "Gateway_station" not in self.param_config.sections():
            self.param_config.add_section("Gateway_station")

        #Gateway_station
        self.param_config.set("Gateway_station", "s_prb_c", self.page1.prb_c.GetValue())
        self.param_config.set("Gateway_station", "s_id_sc", self.page1.id_sc.GetValue())
        self.param_config.set("Gateway_station", "s_modtype_u", self.page1.modtype_u.GetValue())
        self.param_config.set("Gateway_station", "s_modtype_d", self.page1.modtype_d.GetValue())
        self.param_config.set("Gateway_station", "s_u_frequency", self.page1.u_frequency.GetValue())
        self.param_config.set("Gateway_station", "s_d_frequency", self.page1.d_frequency.GetValue())

        if "Terminal" not in self.param_config.sections():
            self.param_config.add_section("Terminal")

        #Terminal
        self.param_config.set("Terminal", "s_u_frequency", self.page2.u_frequency.GetValue())
        self.param_config.set("Terminal", "s_d_frequency", self.page2.d_frequency.GetValue())
        self.param_config.set("Terminal", "s_m_part", self.page2.m_part.GetValue())
        self.param_config.set("Terminal", "s_bigm_part", self.page2.M_part.GetValue())
        self.param_config.set("Terminal", "s_threshold", self.page2.Threshold.GetValue())
        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        #高级界面参数，如果存在param.conf文件，读取，否则等于param{}里的初始值
        try:
            self.param_config.read("param.conf")
        except:
            param_TA = {'RNTI':'100', 't_advance':'0', 'n_pucch':'0','data_rules_T':'0','iter_num_T':'4', 
                'Delta_ss_T':'10', 'shift_T':'1', 'DMRS1_T':'4', 'decision_type_T':'soft', 'algorithm_T':'Max_Log',
                'gain_r_T':'10', 'gain_s_T':'10', 'samp_rate_T':'2M',  'C_SRS':'4', 'B_SRS':'1', 'n_SRS':'4', 
                'n_RRC':'0', 'K_TC':'0','SRS_period':'2','SRS_offset':'0','SR_periodicity':'10','SR_offset':'2',
                't_Reordering_T':'40', 't_StatusProhibit_T':'40','t_PollRetransmit_T':'40','maxRetxThreshold_T':'4',
                'SN_FieldLength_T':'10','pollPDU_T':'16','pollByte_T':'125','route':'192.168.200.3',
                'IP':'192.168.200.11','route':'192.168.200.3'}         

            param_TB = { 'RNTI':'200',  't_advance':'0','n_pucch':'18','data_rules_T':'0','iter_num_T':'4', 
                'Delta_ss_T':'10', 'shift_T':'1', 'DMRS1_T':'4', 'decision_type_T':'soft', 'algorithm_T':'Max_Log',
                'gain_r_T':'10', 'gain_s_T':'10', 'samp_rate_T':'2M','C_SRS':'5', 'B_SRS':'2', 'n_SRS':'5', 'n_RRC':'0',
                'SRS_period':'2','SRS_offset':'1','SR_periodicity':'10','SR_offset_B':'4','t_Reordering_T':'40', 
                't_StatusProhibit_T':'40','t_PollRetransmit_T':'40','maxRetxThreshold_T':'4', 'SN_FieldLength_T':'10',
                'pollPDU_T':'16','pollByte_T':'125','route':'192.168.200.3','K_TC':'1','IP':'192.168.200.11',
                'route':'192.168.200.3'}

            param_G = {'data_rules_G':'0','iter_num_G':'4', 'Delta_ss_G':'10', 'shift_G':'1', 'DMRS2_G':'4',
                'decision_type_G':'soft', 'algorithm_G':'Max_Log', 'gain_r_G':'10','gain_s_G':'10', 'samp_rate_G':'2M', 
                'exp_code_rate_u_G':'0.45', 'exp_code_rate_d_G':'0.45','t_Reordering_G':'40', 't_StatusProhibit_G':'40',
                't_PollRetransmit_G':'40', 'maxRetxThreshold_G':'4', 'SN_FieldLength_G':'10', 'pollPDU_G':'16', 
                'pollByte_G':'125','ip':'192.168.200.11','route':'192.168.200.3'}
        else:
            #Terminal
            global param, param_T, param_TA, param_TB, param_G
            param_TA['RNTI'] = self.param_config.get("Terminal", "s_rnti_a")
            param_TB['RNTI'] = self.param_config.get("Terminal", "s_rnti_b")
            param_TA['t_advance'] = self.param_config.get("Terminal", "s_t_advance_a")
            param_TB['t_advance'] = self.param_config.get("Terminal", "s_t_advance_b")
            param_TA['n_pucch'] = self.param_config.get("Terminal", "s_n_pucch_a")
            param_TB['n_pucch'] = self.param_config.get("Terminal", "s_n_pucch_b")
            if self.param_config.get("Terminal", "s_data_rules") == '指定种子的随机序列':
                param_T['data_rules_T'] = '1'
            else:
                param_T['data_rules_T'] = '0'
            param_T['iter_num_T'] = self.param_config.get("Terminal", "s_iter_num")
            param_T['Delta_ss_T'] = self.param_config.get("Terminal", "s_delta_ss")
            param_T['shift_T'] = self.param_config.get("Terminal", "s_shift")
            param_T['DMRS1_T'] = self.param_config.get("Terminal", "s_DMRS1")
            param_T['decision_type_T'] = self.param_config.get("Terminal", "s_decision_type")
            param_T['algorithm_T'] = self.param_config.get("Terminal", "s_algorithm_c")
            param_T['gain_r_T'] = self.param_config.get("Terminal", "s_gain_r_sc")
            param_T['gain_s_T'] = self.param_config.get("Terminal", "s_gain_s_sc")
            param_T['samp_rate_T'] = self.param_config.get("Terminal", "s_samp_rate_sc")

            param_TA['IP'] = self.param_config.get("Terminal", "s_virtual_ip_a")
            param_TA['route'] = self.param_config.get("Terminal", "s_select_route_a")
            param_TB['IP'] = self.param_config.get("Terminal", "s_virtual_ip_b")
            param_TB['route'] = self.param_config.get("Terminal", "s_select_route_b")
            param_TA['C_SRS'] = self.param_config.get("Terminal", "s_c_srs_a")
            param_TA['B_SRS'] = self.param_config.get("Terminal", "s_b_srs_a")
            param_TA['n_SRS'] = self.param_config.get("Terminal", "s_n_srs_a")
            param_TA['n_RRC'] = self.param_config.get("Terminal", "s_n_rrc_a")
            param_TB['C_SRS'] = self.param_config.get("Terminal", "s_c_srs_b")
            param_TB['B_SRS'] = self.param_config.get("Terminal", "s_b_srs_b")
            param_TB['n_SRS'] = self.param_config.get("Terminal", "s_n_srs_b")
            param_TB['n_RRC'] = self.param_config.get("Terminal", "s_n_rrc_b")
            param_TA['K_TC'] = self.param_config.get("Terminal", "s_k_tc_a")
            param_TB['K_TC'] = self.param_config.get("Terminal", "s_k_tc_b")
            param_TA['SRS_period'] = self.param_config.get("Terminal", "s_srs_period_a")
            param_TB['SRS_period'] = self.param_config.get("Terminal", "s_srs_period_b")
            param_TA['SRS_offset'] = self.param_config.get("Terminal", "s_srs_offset_a")
            param_TB['SRS_offset'] = self.param_config.get("Terminal", "s_srs_offset_b")
            param_TA['SR_periodicity'] = self.param_config.get("Terminal", "s_sr_periodicity_a")
            param_TB['SR_periodicity'] = self.param_config.get("Terminal", "s_sr_periodicity_b")
            param_TA['SR_offset'] = self.param_config.get("Terminal", "s_sr_offset_a")
            param_TB['SR_offset'] = self.param_config.get("Terminal", "s_sr_offset_b")
            # param['t_Reordering_T'] = self.param_config.get("Terminal", "s_t_reordering")
            # param['t_StatusProhibit_T'] = self.param_config.get("Terminal", "s_t_statusprohibit")
            # param['t_PollRetransmit_T'] = self.param_config.get("Terminal", "s_t_pollretransmit")
            # param['maxRetxThreshold_T'] = self.param_config.get("Terminal", "s_maxretxthreshold")
            # param['SN_FieldLength_T'] = self.param_config.get("Terminal", "s_sn_fieldlength")
            # param['pollPDU_T'] = self.param_config.get("Terminal", "s_pollpdu")
            # param['pollByte_T'] = self.param_config.get("Terminal", "s_pollbyte")
            #Gateway_station
            if self.param_config.get("Gateway_station", "s_data_rules") == '指定种子的随机序列':
                param_G['data_rules_G'] = '1'
            else:
                param_G['data_rules_G'] = '0'
            param_G['iter_num_G'] = self.param_config.get("Gateway_station", "s_iter_num")
            param_G['Delta_ss_G'] = self.param_config.get("Gateway_station", "s_delta_ss")
            param_G['shift_G'] = self.param_config.get("Gateway_station", "s_shift")
            param_G['DMRS2_G'] = self.param_config.get("Gateway_station", "s_DMRS2")
            param_G['decision_type_G'] = self.param_config.get("Gateway_station", "s_decision_type")
            param_G['algorithm_G'] = self.param_config.get("Gateway_station", "s_algorithm_c")
            param_G['gain_r_G'] = self.param_config.get("Gateway_station", "s_gain_r_sc")
            param_G['gain_s_G'] = self.param_config.get("Gateway_station", "s_gain_s_sc")
            param_G['exp_code_rate_u_G'] = self.param_config.get("Gateway_station", "s_exp_code_rate_u_sc")
            param_G['exp_code_rate_d_G'] = self.param_config.get("Gateway_station", "s_exp_code_rate_d_sc")
            param_G['samp_rate_G'] = self.param_config.get("Gateway_station", "s_samp_rate_sc")
            param_G['ip'] = self.param_config.get("Gateway_station", "s_virtual_ip_sc")
            param_G['route'] = self.param_config.get("Gateway_station", "s_select_route_sc")
            # param['t_Reordering_G'] = self.param_config.get("Gateway_station", "s_t_reordering")
            # param['t_StatusProhibit_G'] = self.param_config.get("Gateway_station", "s_t_statusprohibit")
            # param['t_PollRetransmit_G'] = self.param_config.get("Gateway_station", "s_t_pollretransmit")
            # param['maxRetxThreshold_G'] = self.param_config.get("Gateway_station", "s_maxretxthreshold")
            # param['SN_FieldLength_G'] = self.param_config.get("Gateway_station", "s_sn_fieldlength")
            # param['pollPDU_G'] = self.param_config.get("Gateway_station", "s_pollpdu")
            # param['pollByte_G'] = self.param_config.get("Gateway_station", "s_pollbyte")

        #主界面的参数
        if self.work_mod.GetItemLabel(self.work_mod.GetSelection()) == '分组业务演示':
            param['work_mod'] = '0'
        else:
            param['work_mod'] = '1'

        param_G['u_frequency_G'] = self.page1.u_frequency.GetValue()
        param_G['d_frequency_G'] = self.page1.d_frequency.GetValue()

        param_T['u_frequency_T'] = self.page2.u_frequency.GetValue()
        param_T['d_frequency_T'] = self.page2.d_frequency.GetValue()

        param['m_part'] = self.page2.m_part.GetValue()
        param['M_part'] = self.page2.M_part.GetValue()
        param['Threshold'] = self.page2.Threshold.GetValue()
        param['Bandwidth'] = self.page1.prb_c.GetValue()
        param['id_cell'] = self.page1.id_sc.GetValue()
        param['mod_type_u'] = self.page1.modtype_u.GetValue()
        param['mod_type_d'] = self.page1.modtype_d.GetValue()            

        param_TA.update(param_T)
        param_TB.update(param_T)
        param_TA.update(param)
        param_TB.update(param)
        param_G.update(param)

        jparam_ta = json.dumps(param_TA)
        jparam_tb = json.dumps(param_TB)
        jparam_g = json.dumps(param_G)

        try:
            print self.clients
            if self.clients.has_key('A_ip'):
                self.clients['A_ip'].send(jparam_ta)
                print jparam_ta
            if self.clients.has_key('B_ip'):
                print jparam_tb
                self.clients['B_ip'].send(jparam_tb)                
            if self.clients.has_key('gateway'):
                print jparam_g
                self.clients['gateway'].send(jparam_g)
                
        except:
            print "请先建立连接"
            self.DisplayText.AppendText(u'请先建立连接...\n')

    def OnMonitor(self,event):
        self.param_config.read("param.conf")
        if "address" not in self.param_config.sections():
            self.param_config.add_section("address")

        #address
        self.param_config.set("address", "s_ip", self.IPText.GetValue())
        self.param_config.set("address", "s_port", self.PortText.GetValue())

        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        #监视按钮按下之后，按钮不能再次按下
        self.monitor_button.Disable()
        self.IPText.Disable()
        self.PortText.Disable()

        t1 = threading.Thread(target = self.start_server)
        t1.setDaemon(True)
        t1.start()

    def start_server(self): 
        try:
            #创建socket并绑定  
            self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
            self.port = int(self.PortText.GetValue())  
            self.host = str(self.IPText.GetValue())  
            self.server.setblocking(False)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
            self.server.bind((self.host, self.port))  
            self.server.listen(3)  
            wx.CallAfter(Publisher().sendMessage, "update", u'控制界面等待连接...\n')
        except:
            self.monitor_button.Enable()
            self.IPText.Enable()
            self.PortText.Enable()
    
        # 读socket
        self.inputs = [ self.server ] 

        # 写socket
        outputs = []  

        #客户端地址
        self.clients = {}
  
        # 消息队列
        message_queues = {} 
  
        while self.inputs:  
            # 等待出现至少一个连接准备好,要求处理
            print "等待事件"  
            readable, writable, exceptional = select.select(self.inputs, outputs, self.inputs)  
              
            # 读socket处理
            for s in readable:  
                # 如果读socket是server，则建立连接；如果读socket是connection，则接收数据
                if s is self.server:  
                    try:
                        self.connection, self.client_address = s.accept()  
                    except:
                        print '请输入正确的IP地址'
                        sys.exit()
                    else:
                        wx.CallAfter(Publisher().sendMessage, "update", u'与 %s %s建立连接\n' % self.client_address)
                        self.connection.setblocking(False)
                        self.inputs.append(self.connection)  
                        # 给连接一个队列，该队列用于发送数据 
                        message_queues[self.connection] = Queue.Queue() 
                        # print self.inputs
                else: 
                    data = s.recv(1024) 
                    try:
                        message = json.loads(data)
                        if message:  
                            # print message
                            # message.update(self.clients)
                            if message.has_key('terminal') and message['terminal'] == 'true':
                                if self.clients.has_key('A_ip'):
                                    self.clients['B_ip'] = s
                                    # self.connection.send('B')
                                if not self.clients.has_key('A_ip'):
                                    self.clients['A_ip'] = s
                                    # self.connection.send('A')
                            elif message.has_key('gateway') and message['gateway'] == 'true':
                                self.clients['gateway'] = s

                            # 客户端有数据发送   
                            # wx.CallAfter(Publisher().sendMessage, "update_t", message)
                            # message_queues[s].put(data)
                            # Add output channel for response    
                            if s not in outputs:
                                outputs.append(s)

                        # if message.has_key('gateway'):
                        #     if message['gateway'] == 'false':
                        # if message.has_key('terminal'):
                        #     if message['terminal'] == 'false':
                        #         if self.clients.has_key('B_ip'):
                        #             del self.clients['B_ip']
                        #         else:
                        #             del self.clients['A_ip']
                        # print self.clients
                    except:  
                        print "客户端没有数据发送，关闭连接"
                        # self.DisplayText.AppendText(u'关闭与%s %s的连接\n\n' % client_address)
                        # try:
                        #     wx.CallAfter(Publisher().sendMessage, "update", u'关闭与%s的连接\n' % name) 
                        # except:pass 
                        
                        # 停止对该连接的读socket监听  
                        # try:
                        if self.clients.has_key('B_ip') and self.clients['B_ip'] == s:
                            del self.clients['B_ip']
                            wx.CallAfter(Publisher().sendMessage, "update", u'关闭与%s的连接\n' % '终端B') 
                        if self.clients.has_key('A_ip') and self.clients['A_ip'] == s:
                            del self.clients['A_ip']
                            wx.CallAfter(Publisher().sendMessage, "update", u'关闭与%s的连接\n' % '终端A') 
                        if self.clients.has_key('gateway') and self.clients['gateway'] == s:
                            # message['gateway'] = 'false'
                            del self.clients['gateway']
                            wx.CallAfter(Publisher().sendMessage, "update", u'关闭与%s的连接\n' % '信关站') 
                        # except:
                        #     message['gateway'] = 'false'
                        #     wx.CallAfter(Publisher().sendMessage, "update", u'关闭与%s的连接\n' % '信关站') 

                        if s in outputs:  
                            outputs.remove(s)  
                        self.inputs.remove(s)  
                        s.close()  
                        # 移除消息队列  
                        del message_queues[s]  

                    merge_message = dict(message.items()+self.clients.items())
                    wx.CallAfter(Publisher().sendMessage, "update_t", merge_message)
            # 写socket处理 
            for s in writable:  
                try:  
                    next_msg = message_queues[s].get_nowait()  
                except Queue.Empty:  
                    # 如果消息队列没有消息，则停止写socket 
                    outputs.remove(s)  
                else:  
                    #如果消息队列有消息，则向客户端写
                    wx.CallAfter(Publisher().sendMessage, "update", u'向%s发送消息:%s' % (s.getpeername(), next_msg))  
                    s.send(next_msg)  

            #异常错误处理 
            for s in exceptional:
                wx.CallAfter(Publisher().sendMessage, "update", u'与%s的连接出现异常错误'% s.getpeername())  
                # 停止对该连接的读socket监听 
                self.inputs.remove(s)  
                if s in outputs:  
                    outputs.remove(s)  
                s.close()  
                # 移除消息队列  
                del message_queues[s]  
  
    def OnCloseWindow(self, event):
        self.Destroy()

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

