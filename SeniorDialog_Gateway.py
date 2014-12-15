#!/usr/bin/env python
#coding=utf-8
import wx
import ConfigParser

from Help_Dialog import Help_Dialog

class SeniorDialog_Gateway(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, title=u'信关站高级配置')
        self.parent = parent
        self.SetBackgroundColour("white")

        # 绑定窗口的关闭事件
        # self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        # 创建面板
        self.SeniorPanel()

    def SeniorPanel(self):
        # 参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_data_rules = self.param_config.get("Gateway_station", "s_data_rules")
        except: s_data_rules = '规则递增'

        try: s_iter_num = self.param_config.getint("Gateway_station", "s_iter_num")
        except: s_iter_num = 4

        try: s_Delta_ss = self.param_config.getint("Gateway_station", "s_delta_ss")
        except: s_Delta_ss = 10

        try: s_shift = self.param_config.getint("Gateway_station", "s_shift")
        except: s_shift = 1

        try: s_DMRS2 = self.param_config.getint("Gateway_station", "s_DMRS2")
        except: s_DMRS2 = 4

        try: s_decision_type = self.param_config.get("Gateway_station", "s_decision_type")
        except: s_decision_type = 'soft'

        try: s_algorithm_c = self.param_config.get("Gateway_station", "s_algorithm_c")
        except: s_algorithm_c = 'Max_Log'

        try: s_gain_r_sc = self.param_config.getint("Gateway_station", "s_gain_r_sc")
        except: s_gain_r_sc = 10

        try: s_gain_s_sc = self.param_config.getint("Gateway_station", "s_gain_s_sc")
        except: s_gain_s_sc = 10

        try: s_exp_code_rate_u_sc = self.param_config.get("Gateway_station", "s_exp_code_rate_u_sc")
        except: s_exp_code_rate_u_sc = '0.45'

        try: s_exp_code_rate_d_sc = self.param_config.get("Gateway_station", "s_exp_code_rate_d_sc")
        except: s_exp_code_rate_d_sc = '0.45'

        try: s_samp_rate_sc = self.param_config.get("Gateway_station", "s_samp_rate_sc")
        except: s_samp_rate_sc = '2M'

        try: s_virtual_ip_sc = self.param_config.get("Gateway_station", "s_virtual_ip_sc")
        except: s_virtual_ip_sc = '192.168.200.11'

        try: s_select_route_sc = self.param_config.get("Gateway_station", "s_select_route_sc")
        except: s_select_route_sc = '192.168.200.3'

        try: s_t_reordering = self.param_config.getint("Gateway_station", "s_t_reordering")
        except: s_t_reordering = 40

        try: s_t_statusprohibit = self.param_config.getint("Gateway_station", "s_t_statusprohibit")
        except: s_t_statusprohibit = 40

        try: s_t_pollretransmit = self.param_config.getint("Gateway_station", "s_t_pollretransmit")
        except: s_t_pollretransmit = 40

        try: s_maxretxthreshold = self.param_config.get("Gateway_station", "s_maxretxthreshold")
        except: s_maxretxthreshold = '4'

        try: s_sn_fieldlength = self.param_config.get("Gateway_station", "s_sn_fieldlength")
        except: s_sn_fieldlength = '10'

        try: s_pollpdu = self.param_config.get("Gateway_station", "s_pollpdu")
        except: s_pollpdu = '16'

        try: s_pollbyte = self.param_config.get("Gateway_station", "s_pollbyte")
        except: s_pollbyte = '125'

        #测试数据生成规则
        data_rules_list = [u'规则递增', u'指定种子的随机序列']
        data_rules_st = wx.StaticText(self, -1, u"测试数据生成规则:")
        self.data_rules = wx.ComboBox(self, -1, s_data_rules, wx.DefaultPosition, wx.DefaultSize, data_rules_list, 0)

        #译码算法迭代次数
        iter_num_st = wx.StaticText(self, -1, u"译码算法迭代次数:")
        self.iter_num = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.iter_num.SetRange(1,8)
        self.iter_num.SetValue(s_iter_num)

        #用于配置fss
        Delta_ss_st = wx.StaticText(self, -1, u"Δss:")
        self.Delta_ss = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.Delta_ss.SetRange(0,29)
        self.Delta_ss.SetValue(s_Delta_ss)

        #循环移位间隔
        shift_st = wx.StaticText(self, -1, u"循环移位间隔:")
        self.shift = wx.SpinCtrl(self, -1, "", (-1,-1))
        self.shift.SetRange(1,3)
        self.shift.SetValue(s_shift)

        #解调参考符号DMRS2
        DMRS2_st = wx.StaticText(self, -1, "DMRS2:")
        self.DMRS2 = wx.SpinCtrl(self, -1, "", (-1,-1))
        self.DMRS2.SetRange(0,7)
        self.DMRS2.SetValue(s_DMRS2)

        #判决方式
        decision_type_list = ['soft', 'hard']
        decision_type_st = wx.StaticText(self, -1, u"判决方式:")
        self.decision_type = wx.ComboBox(self, -1, s_decision_type, wx.DefaultPosition, wx.DefaultSize, decision_type_list, 0)

        #Turbo译码算法 
        algorithm_list = ['Max_Log',u'维特比']
        algorithm_st = wx.StaticText(self, -1 ,u"Turbo译码算法:")
        self.algorithm_c = wx.ComboBox(self, -1, s_algorithm_c, wx.DefaultPosition, wx.DefaultSize, algorithm_list, 0)

        #收发增益控制
        Gain_r_st = wx.StaticText(self, -1 ,u"接收增益(dB):")
        self.Gain_r_sc = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.Gain_r_sc.SetRange(0,30)
        self.Gain_r_sc.SetValue(s_gain_r_sc)

        Gain_s_st = wx.StaticText(self, -1, u"发送增益(dB):")
        self.Gain_s_sc = wx.SpinCtrl(self,-1, "",(-1, -1))
        self.Gain_s_sc.SetRange(0,20)
        self.Gain_s_sc.SetValue(s_gain_s_sc)

        #上行编码码率
        exp_code_rate_u_st = wx.StaticText(self, -1, u"上行编码码率:")
        self.exp_code_rate_u = wx.TextCtrl(self, -1, s_exp_code_rate_u_sc)

        #下行编码码率
        exp_code_rate_d_st = wx.StaticText(self, -1, u"下行编码码率:")
        self.exp_code_rate_d = wx.TextCtrl(self, -1, s_exp_code_rate_d_sc)

        #采样率
        samp_rate_list = ['2M','4M']
        samp_rate_st = wx.StaticText(self, -1 ,u"采样率:")
        self.samp_rate_c = wx.ComboBox(self, -1, s_samp_rate_sc, wx.DefaultPosition, wx.DefaultSize, samp_rate_list, 0)

        #虚拟ip地址
        virtual_ip_st = wx.StaticText(self, -1, u"虚拟ip地址:")
        self.virtual_ip = wx.TextCtrl(self, -1, s_virtual_ip_sc)

        #选择路由
        select_route_st = wx.StaticText(self, -1, u"选择路由:")
        self.select_route = wx.TextCtrl(self, -1, s_select_route_sc)

        #由RLC UM的收端或AM使用，定时超时表明目前接收到但尚未递交高层的一段数据必须丢弃
        t_Reordering_st = wx.StaticText(self, -1, "t_Reordering(ms):")
        self.t_Reordering = wx.Slider(self, -1, s_t_reordering, 0, 200, size=(300, -1),
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        #设置滑块的刻度
        self.t_Reordering.SetTickFreq(5, 1)  
        #设置箭头调整的幅度
        self.t_Reordering.SetLineSize(10)
        #调整pageup/pagedown调整的幅度
        self.t_Reordering.SetPageSize(5)

        #由RLC AM使用，发送完一个状态报告之后，禁止再次发送的时间范围
        t_StatusProhibit_st = wx.StaticText(self, -1, "t_StatusProhibit(ms):")
        self.t_StatusProhibit = wx.Slider(self, -1, s_t_statusprohibit, 0, 500, 
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.t_StatusProhibit.SetTickFreq(10, 1) 
        self.t_StatusProhibit.SetLineSize(10)
        self.t_StatusProhibit.SetPageSize(5)

        #由RLC AM使用，发起状态查询，即主动请求对端发送状态报告的周期
        t_PollRetransmit_st = wx.StaticText(self, -1, "t_PollRetransmit(ms):")
        self.t_PollRetransmit = wx.Slider(self, -1, s_t_pollretransmit, 5, 500, 
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.t_PollRetransmit.SetTickFreq(10, 1) 
        self.t_PollRetransmit.SetLineSize(10)
        self.t_PollRetransmit.SetPageSize(5)

        #最大重传次数
        maxRetxThreshold_list = ['1', '2', '3', '4', '6', '8', '16', '32']
        maxRetxThreshold_st = wx.StaticText(self, -1, u"最大重传次数:")
        self.maxRetxThreshold = wx.ComboBox(self, -1, s_maxretxthreshold, wx.DefaultPosition, wx.DefaultSize, maxRetxThreshold_list, 0)

        #RLC UM使用，PDU中序号占用的比特数
        SN_FieldLength_list = ['5','10']
        SN_FieldLength_st = wx.StaticText(self, -1, "SN_FieldLength:")
        self.SN_FieldLength = wx.ComboBox(self, -1, s_sn_fieldlength, wx.DefaultPosition, wx.DefaultSize, SN_FieldLength_list, 0)

        #RLC AM使用，当发送的PDU个数大于该计数器，强制启动状态查询
        pollPDU_list = ['4', '8', '16', '32', '64', '128', '256']
        pollPDU_st = wx.StaticText(self, -1, "pollPDU:")
        self.pollPDU = wx.ComboBox(self, -1, s_pollpdu, wx.DefaultPosition, wx.DefaultSize, pollPDU_list, 0)

        #RLC AM使用，当发送的SDU字节数大于该计数器，强制启动状态查询
        pollByte_list = ['25','50','75','100','125','250','375','500','750','1000','1250','1500','2000','3000']
        pollByte_st = wx.StaticText(self, -1, "pollByte(KB):")
        self.pollByte = wx.ComboBox(self, -1, s_pollbyte, wx.DefaultPosition, wx.DefaultSize, pollByte_list, 0)

        #确定设置按钮
        self.ok_button = wx.Button(self, -1, u"确定")
        self.ok_button.SetBackgroundColour('black')
        self.ok_button.SetForegroundColour('white')
        # self.ok_button.SetDefault()

        #帮助按钮
        self.help_button = wx.Button(self, -1, u"帮助")
        self.help_button.SetBackgroundColour('black')
        self.help_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Help,self.help_button)

        #MAC/PHY布局
        sizer2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        sizer2.AddGrowableCol(1)
        sizer2.Add(data_rules_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.data_rules, 0, wx.EXPAND)
        sizer2.Add(iter_num_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.iter_num, 0, wx.EXPAND)
        sizer2.Add(Delta_ss_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Delta_ss, 0, wx.EXPAND)
        sizer2.Add(shift_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.shift, 0, wx.EXPAND)
        sizer2.Add(DMRS2_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.DMRS2, 0, wx.EXPAND)
        sizer2.Add(decision_type_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.decision_type, 0, wx.EXPAND)
        sizer2.Add(algorithm_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.algorithm_c, 0, wx.EXPAND)
        sizer2.Add(Gain_r_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_r_sc, 0, wx.EXPAND)
        sizer2.Add(Gain_s_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_s_sc, 0, wx.EXPAND)
        sizer2.Add(exp_code_rate_u_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.exp_code_rate_u, 0, wx.EXPAND)
        sizer2.Add(exp_code_rate_d_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.exp_code_rate_d, 0, wx.EXPAND)
        sizer2.Add(samp_rate_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.samp_rate_c, 0, wx.EXPAND)
        sizer2.Add(virtual_ip_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.virtual_ip, 0, wx.EXPAND)
        sizer2.Add(select_route_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.select_route, 0, wx.EXPAND)

        #RLC布局
        sizer4 = wx.FlexGridSizer(cols=2,hgap=5,vgap=12)
        sizer4.AddGrowableCol(1)
        sizer4.Add(t_Reordering_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_Reordering, 0, wx.EXPAND)
        sizer4.Add(t_StatusProhibit_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_StatusProhibit, 0, wx.EXPAND)
        sizer4.Add(t_PollRetransmit_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_PollRetransmit, 0, wx.EXPAND)
        sizer4.Add(maxRetxThreshold_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.maxRetxThreshold, 0, wx.EXPAND)
        sizer4.Add(SN_FieldLength_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.SN_FieldLength, 0, wx.EXPAND)
        sizer4.Add(pollPDU_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.pollPDU, 0, wx.EXPAND)
        sizer4.Add(pollByte_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.pollByte, 0, wx.EXPAND)

        #确定按钮布局
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add((20,20), 1)
        sizer3.Add(self.ok_button, 0, wx.ALIGN_RIGHT)
        sizer3.Add(self.help_button, 0, wx.ALIGN_RIGHT)

        #添加参数子块，带边框的模块布局
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'MAC/PHY层参数'), wx.VERTICAL)
        sizer5.Add(sizer2, 0, wx.EXPAND | wx.ALL, 10)

        sizer6 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'RLC层参数'), wx.VERTICAL)
        sizer6.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(sizer5, 0, wx.EXPAND | wx.ALL, 10)
        sizer1.Add(sizer6, 0, wx.EXPAND | wx.ALL, 10)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)
        box.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        #自动调整界面尺寸
        self.SetSizer(box)
        box.Fit(self)
        box.SetSizeHints(self)

    def Help(self,event):
        self.dialog = Help_Dialog(self)
        # self.dialog.ShowModal()
        self.dialog.Show()

    # def OnCloseWindow(self):
    #     self.Destroy()
    #     self.dialog.Destroy()

