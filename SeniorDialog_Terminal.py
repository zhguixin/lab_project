#!/usr/bin/env python
#coding=utf-8
import wx
import ConfigParser

from Help_Dialog import Help_Dialog

class SeniorDialog_Terminal(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, title=u'终端高级配置')
        self.parent = parent
        # self.SetTitle(u'终端高级配置')
        self.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        #创建面板
        self.SeniorPanel()

    def SeniorPanel(self):

        #参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_virtual_ip_a = self.param_config.get("Terminal", "s_virtual_ip_a")
        except: s_virtual_ip_a = '192.168.200.11'

        try: s_select_route_a = self.param_config.get("Terminal", "s_select_route_a")
        except: s_select_route_a = '192.168.200.3'

        try: s_virtual_ip_b = self.param_config.get("Terminal", "s_virtual_ip_b")
        except: s_virtual_ip_b = '192.168.200.11'

        try: s_select_route_b = self.param_config.get("Terminal", "s_select_route_b")
        except: s_select_route_b = '192.168.200.3'

        try: s_rnti_a = self.param_config.getint("Terminal", "s_rnti_a")
        except: s_rnti_a = 100

        try: s_rnti_b = self.param_config.getint("Terminal", "s_rnti_b")
        except: s_rnti_b = 200

        try: s_t_advance_a = self.param_config.get("Terminal", "s_t_advance_a")
        except: s_t_advance_a = '0'

        try: s_t_advance_b = self.param_config.get("Terminal", "s_t_advance_b")
        except: s_t_advance_b = '0'

        try: s_n_pucch_a = self.param_config.get("Terminal", "s_n_pucch_a")
        except: s_n_pucch_a = '0'

        try: s_n_pucch_b = self.param_config.get("Terminal", "s_n_pucch_b")
        except: s_n_pucch_b = '18'

        try: s_data_rules = self.param_config.get("Terminal", "s_data_rules")
        except: s_data_rules = '规则递增'

        try: s_iter_num = self.param_config.getint("Terminal", "s_iter_num")
        except: s_iter_num = 4

        try: s_delta_ss = self.param_config.getint("Terminal", "s_delta_ss")
        except: s_delta_ss = 10

        try: s_shift = self.param_config.getint("Terminal", "s_shift")
        except: s_shift = 1

        try: s_DMRS1 = self.param_config.get("Terminal", "s_DMRS1")
        except: s_DMRS1 = '4'

        try: s_decision_type = self.param_config.get("Terminal", "s_decision_type")
        except: s_decision_type = 'soft'

        try: s_algorithm_c = self.param_config.get("Terminal", "s_algorithm_c")
        except: s_algorithm_c = 'Max_Log'

        try: s_gain_r_sc = self.param_config.getint("Terminal", "s_gain_r_sc")
        except: s_gain_r_sc = 10

        try: s_gain_s_sc = self.param_config.getint("Terminal", "s_gain_s_sc")
        except: s_gain_s_sc = 10

        try: s_samp_rate_sc = self.param_config.get("Terminal", "s_samp_rate_sc")
        except: s_samp_rate_sc = '2M'

        try: s_c_srs_a = self.param_config.getint("Terminal", "s_c_srs_a")
        except: s_c_srs_a = 4

        try: s_b_srs_a = self.param_config.getint("Terminal", "s_b_srs_a")
        except: s_b_srs_a = 1

        try: s_n_srs_a = self.param_config.getint("Terminal", "s_n_srs_a")
        except: s_n_srs_a = 4

        try: s_n_rrc_a = self.param_config.getint("Terminal", "s_n_rrc_a")
        except: s_n_rrc_a = 0

        try: s_k_tc_a = self.param_config.get("Terminal", "s_k_tc_a")
        except: s_k_tc_a = '0'

        try: s_srs_period_a = self.param_config.get("Terminal", "s_srs_period_a")
        except: s_srs_period_a = '2'

        try: s_srs_offset_a = self.param_config.get("Terminal", "s_srs_offset_a")
        except: s_srs_offset_a = '0'

        try: s_sr_periodicity_a = self.param_config.get("Terminal", "s_sr_periodicity_a")
        except: s_sr_periodicity_a = '10'

        try: s_sr_offset_a = self.param_config.get("Terminal", "s_sr_offset_a")
        except: s_sr_offset_a = '2'

        try: s_k_tc_b = self.param_config.get("Terminal", "s_k_tc_b")
        except: s_k_tc_b = '1'

        try: s_srs_period_b = self.param_config.get("Terminal", "s_srs_period_b")
        except: s_srs_period_b = '2'

        try: s_srs_offset_b = self.param_config.get("Terminal", "s_srs_offset_b")
        except: s_srs_offset_b = '1'

        try: s_sr_periodicity_b= self.param_config.get("Terminal", "s_sr_periodicity_b")
        except: s_sr_periodicity_b = '10'

        try: s_sr_offset_b = self.param_config.get("Terminal", "s_sr_offset_b")
        except: s_sr_offset_b = '4'

        try: s_c_srs_b = self.param_config.getint("Terminal", "s_c_srs_b")
        except: s_c_srs_b = 4

        try: s_b_srs_b = self.param_config.getint("Terminal", "s_b_srs_b")
        except: s_b_srs_b = 1

        try: s_n_srs_b = self.param_config.getint("Terminal", "s_n_srs_b")
        except: s_n_srs_b = 4

        try: s_n_rrc_b = self.param_config.getint("Terminal", "s_n_rrc_b")
        except: s_n_rrc_b = 0

        try: s_t_reordering = self.param_config.getint("Terminal", "s_t_reordering")
        except: s_t_reordering = 40

        try: s_t_statusprohibit = self.param_config.getint("Terminal", "s_t_statusprohibit")
        except: s_t_statusprohibit = 40

        try: s_t_pollretransmit = self.param_config.getint("Terminal", "s_t_pollretransmit")
        except: s_t_pollretransmit = 40

        try: s_maxretxthreshold = self.param_config.get("Terminal", "s_maxretxthreshold")
        except: s_maxretxthreshold = '4'

        try: s_sn_fieldlength = self.param_config.get("Terminal", "s_sn_fieldlength")
        except: s_sn_fieldlength = '10'

        try: s_pollpdu = self.param_config.get("Terminal", "s_pollpdu")
        except: s_pollpdu = '16'

        try: s_pollbyte = self.param_config.get("Terminal", "s_pollbyte")
        except: s_pollbyte = '125'

        #终端A的RNTI，两个终端单独配置
        RNTI_st_A = wx.StaticText(self, -1, u"RNTI:")
        self.RNTI_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.RNTI_A.SetRange(61,65523)
        self.RNTI_A.SetValue(s_rnti_a)

        #终端B的RNTI，两个终端单独配置
        RNTI_st_B = wx.StaticText(self, -1, u"RNTI:")
        self.RNTI_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.RNTI_B.SetRange(61,65523)
        self.RNTI_B.SetValue(s_rnti_b)

        #终端A的时间提前量，终端与信关站之间的单向传播时延；两个终端单独配置 
        t_advance_st_A = wx.StaticText(self, -1, u"时间提前量:")
        self.t_advance_A = wx.TextCtrl(self, -1, s_t_advance_a)

        #终端B的时间提前量，终端与信关站之间的单向传播时延；两个终端单独配置 
        t_advance_st_B = wx.StaticText(self, -1, u"时间提前量:")
        self.t_advance_B = wx.TextCtrl(self, -1, s_t_advance_b)

        #终端A的虚拟ip地址
        virtual_ip_st_A = wx.StaticText(self, -1, u"虚拟ip地址:")
        self.virtual_ip_A = wx.TextCtrl(self, -1, s_virtual_ip_a)

        #终端A的选择路由
        select_route_st_A = wx.StaticText(self, -1, u"选择路由:")
        self.select_route_A = wx.TextCtrl(self, -1, s_select_route_a)

        #终端B的虚拟ip地址
        virtual_ip_st_B = wx.StaticText(self, -1, u"虚拟ip地址:")
        self.virtual_ip_B = wx.TextCtrl(self, -1, s_virtual_ip_b)

        #终端B的选择路由
        select_route_st_B = wx.StaticText(self, -1, u"选择路由:")
        self.select_route_B = wx.TextCtrl(self, -1, s_select_route_b)

        #用户A资源索引，两个终端单独配置
        n_pucch_A_st = wx.StaticText(self, -1, u"资源索引:")
        self.n_pucch_A = wx.TextCtrl(self, -1, s_n_pucch_a)

        #用户B资源索引，两个终端单独配置
        n_pucch_B_st = wx.StaticText(self, -1, u"资源索引:")
        self.n_pucch_B = wx.TextCtrl(self, -1, s_n_pucch_b)

        #C_SRS由高层的srs-BandwidthConfig参数得到，终端A用此参数确定序列的长度
        C_SRS_A_st = wx.StaticText(self, -1, "C_SRS:")
        self.C_SRS_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.C_SRS_A.SetRange(0,7)
        self.C_SRS_A.SetValue(s_c_srs_a)

        #C_SRS由高层的srs-BandwidthConfig参数得到，终端B用此参数确定序列的长度
        C_SRS_B_st = wx.StaticText(self, -1, "C_SRS:")
        self.C_SRS_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.C_SRS_B.SetRange(0,7)
        self.C_SRS_B.SetValue(s_c_srs_b)

        #由高层的srs-Bandwidth参数得到，终端A用此参数确定序列的长度
        B_SRS_A_st = wx.StaticText(self, -1, "B_SRS:")
        self.B_SRS_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.B_SRS_A.SetRange(0,3)
        self.B_SRS_A.SetValue(s_b_srs_a)

        #由高层的srs-Bandwidth参数得到，终端B用此参数确定序列的长度
        B_SRS_B_st = wx.StaticText(self, -1, "B_SRS:")
        self.B_SRS_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.B_SRS_B.SetRange(0,3)
        self.B_SRS_B.SetValue(s_b_srs_b)

        #由高层cyclicshift参数得到 ，终端A用此参数确定序列的循环移位
        n_SRS_A_st = wx.StaticText(self, -1, "n_SRS:")
        self.n_SRS_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_SRS_A.SetRange(0,7)
        self.n_SRS_A.SetValue(s_n_srs_a)

        #由高层cyclicshift参数得到 ，终端B用此参数确定序列的循环移位
        n_SRS_B_st = wx.StaticText(self, -1, "n_SRS:")
        self.n_SRS_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_SRS_B.SetRange(0,7)
        self.n_SRS_B.SetValue(s_n_srs_b)

        #终端A的K_TC,两个终端分别配置
        K_TC_A_list = ['0', '1']
        K_TC_A_st = wx.StaticText(self, -1, u"K_TC:")
        self.K_TC_A = wx.ComboBox(self, -1, s_k_tc_a, wx.DefaultPosition, wx.DefaultSize, K_TC_A_list, 0)

        #终端B的K_TC,两个终端分别配置
        K_TC_B_list = ['0', '1']
        K_TC_B_st = wx.StaticText(self, -1, u"K_TC:")
        self.K_TC_B = wx.ComboBox(self, -1, s_k_tc_b, wx.DefaultPosition, wx.DefaultSize, K_TC_B_list, 0)

        #终端A的SRS周期，终端分别配置
        SRS_period_A_list = ['1','2','5','10']
        SRS_period_A_st = wx.StaticText(self, -1, u"SRS_period:")
        self.SRS_period_A = wx.ComboBox(self, -1, s_srs_period_a, wx.DefaultPosition, wx.DefaultSize, SRS_period_A_list, 0)
        
        #终端B的SRS周期，终端分别配置
        SRS_period_B_list = ['1','2','5','10']
        SRS_period_B_st = wx.StaticText(self, -1, u"SRS_period:")
        self.SRS_period_B = wx.ComboBox(self, -1, s_srs_period_b, wx.DefaultPosition, wx.DefaultSize, SRS_period_B_list, 0)
        
        #终端A的SRS补偿，终端分别配置
        SRS_offset_A_list = ['0','1','2','3','4','5','6','8']
        SRS_offset_A_st = wx.StaticText(self, -1, u"SRS_offset:")
        self.SRS_offset_A = wx.ComboBox(self, -1, s_srs_offset_a, wx.DefaultPosition, wx.DefaultSize, SRS_offset_A_list, 0)
        
        #终端B的SRS补偿，终端分别配置
        SRS_offset_B_list = ['0','1','2','3','4','5','6','8']
        SRS_offset_B_st = wx.StaticText(self, -1, u"SRS_offset:")
        self.SRS_offset_B = wx.ComboBox(self, -1, s_srs_offset_b, wx.DefaultPosition, wx.DefaultSize, SRS_offset_B_list, 0)
        
        #终端A的SR周期，终端分别配置
        SR_periodicity_A_list = ['5','10','20','40','80','2','1']
        SR_periodicity_A_st = wx.StaticText(self, -1, u"SR_periodicity:")
        self.SR_periodicity_A = wx.ComboBox(self, -1, s_sr_periodicity_a, wx.DefaultPosition, wx.DefaultSize, SR_periodicity_A_list, 0)
        
        #终端B的SR周期，终端分别配置
        SR_periodicity_B_list = ['5','10','20','40','80','2','1']
        SR_periodicity_B_st = wx.StaticText(self, -1, u"SR_periodicity:")
        self.SR_periodicity_B = wx.ComboBox(self, -1, s_sr_periodicity_b, wx.DefaultPosition, wx.DefaultSize, SR_periodicity_B_list, 0)
        
        #终端A的SR补偿，终端分别配置
        SR_offset_A_st = wx.StaticText(self, -1, u"SR_offset:")
        self.SR_offset_A = wx.TextCtrl(self, -1, s_sr_offset_a)

        #终端B的SR补偿，终端分别配置
        SR_offset_B_st = wx.StaticText(self, -1, u"SR_offset:")
        self.SR_offset_B = wx.TextCtrl(self, -1, s_sr_offset_b)

        #由高层freqDomainPositon参数给出，终端A用此参数确定映射时的频带起始位置
        n_RRC_A_st = wx.StaticText(self, -1, "n_RRC:")
        self.n_RRC_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_RRC_A.SetRange(0,23)
        self.n_RRC_A.SetValue(s_n_rrc_a)

        #由高层freqDomainPositon参数给出，终端B用此参数确定映射时的频带起始位置
        n_RRC_B_st = wx.StaticText(self, -1, "n_RRC:")
        self.n_RRC_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_RRC_B.SetRange(0,23)
        self.n_RRC_B.SetValue(s_n_rrc_b)

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
        self.Delta_ss.SetValue(s_delta_ss)

        #循环移位间隔
        shift_st = wx.StaticText(self, -1, u"循环移位间隔:")
        self.shift = wx.SpinCtrl(self, -1, "", (-1,-1))
        self.shift.SetRange(1,3)
        self.shift.SetValue(s_shift)

        #解调参考符号
        DMRS1_list = ['0', '2', '3', '4', '6', '8', '9', '10']
        DMRS1_st = wx.StaticText(self, -1, u"DMRS1:")
        self.DMRS1 = wx.ComboBox(self, -1, s_DMRS1, wx.DefaultPosition, wx.DefaultSize, DMRS1_list, 0)

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

        #采样率
        samp_rate_list = ['2M','4M']
        samp_rate_st = wx.StaticText(self, -1 ,u"采样率:")
        self.samp_rate_c = wx.ComboBox(self, -1, s_samp_rate_sc, wx.DefaultPosition, wx.DefaultSize, samp_rate_list, 0)

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
        SN_FieldLength_list = ['5', '10']
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
        self.help_button1 = wx.Button(self, -1, u"帮助1")
        self.help_button1.SetBackgroundColour('black')
        self.help_button1.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Help,self.help_button1)

        self.help_button2 = wx.Button(self, -1, u"帮助2")
        self.help_button2.SetBackgroundColour('black')
        self.help_button2.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Help_dialog2,self.help_button2)

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
        sizer2.Add(DMRS1_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.DMRS1, 0, wx.EXPAND)
        sizer2.Add(decision_type_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.decision_type, 0, wx.EXPAND)
        sizer2.Add(algorithm_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.algorithm_c, 0, wx.EXPAND)
        sizer2.Add(Gain_r_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_r_sc, 0, wx.EXPAND)
        sizer2.Add(Gain_s_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_s_sc, 0, wx.EXPAND)
        sizer2.Add(samp_rate_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.samp_rate_c, 0, wx.EXPAND)

        #RLC布局
        sizer4 = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
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

        #终端A布局
        sizerA = wx.FlexGridSizer(cols=4,hgap=5,vgap=5)
        sizerA.AddGrowableCol(1)
        sizerA.Add(RNTI_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.RNTI_A, 0, wx.EXPAND)
        sizerA.Add(C_SRS_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.C_SRS_A, 0, wx.EXPAND)
        sizerA.Add(B_SRS_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.B_SRS_A, 0, wx.EXPAND)
        sizerA.Add(n_SRS_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.n_SRS_A, 0, wx.EXPAND)
        sizerA.Add(n_RRC_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.n_RRC_A, 0, wx.EXPAND)
        sizerA.Add(K_TC_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.K_TC_A, 0, wx.EXPAND)
        sizerA.Add(SRS_period_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SRS_period_A, 0, wx.EXPAND)
        sizerA.Add(SRS_offset_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SRS_offset_A, 0, wx.EXPAND)
        sizerA.Add(SR_periodicity_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SR_periodicity_A, 0, wx.EXPAND)
        sizerA.Add(SR_offset_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SR_offset_A, 0, wx.EXPAND)
        sizerA.Add(n_pucch_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.n_pucch_A, 0, wx.EXPAND)
        sizerA.Add(t_advance_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.t_advance_A, 0, wx.EXPAND)
        sizerA.Add(virtual_ip_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.virtual_ip_A, 0, wx.EXPAND)
        sizerA.Add(select_route_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.select_route_A, 0, wx.EXPAND)

        #终端B布局
        sizerB = wx.FlexGridSizer(cols=4,hgap=5,vgap=5)
        sizerB.AddGrowableCol(1)
        sizerB.Add(RNTI_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.RNTI_B, 0, wx.EXPAND)
        sizerB.Add(C_SRS_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.C_SRS_B, 0, wx.EXPAND)
        sizerB.Add(B_SRS_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.B_SRS_B, 0, wx.EXPAND)
        sizerB.Add(n_SRS_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.n_SRS_B, 0, wx.EXPAND)
        sizerB.Add(n_RRC_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.n_RRC_B, 0, wx.EXPAND)
        sizerB.Add(K_TC_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.K_TC_B, 0, wx.EXPAND)
        sizerB.Add(SRS_period_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SRS_period_B, 0, wx.EXPAND)
        sizerB.Add(SRS_offset_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SRS_offset_B, 0, wx.EXPAND)
        sizerB.Add(SR_periodicity_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SR_periodicity_B, 0, wx.EXPAND)
        sizerB.Add(SR_offset_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SR_offset_B, 0, wx.EXPAND)
        sizerB.Add(n_pucch_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.n_pucch_B, 0, wx.EXPAND)
        sizerB.Add(t_advance_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.t_advance_B, 0, wx.EXPAND)
        sizerB.Add(virtual_ip_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.virtual_ip_B, 0, wx.EXPAND)
        sizerB.Add(select_route_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.select_route_B, 0, wx.EXPAND)

        #确定按钮布局
        sizer31 = wx.BoxSizer(wx.HORIZONTAL)
        sizer31.Add((20,20), 1)
        sizer31.Add(self.ok_button, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        sizer31.Add(self.help_button1, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        sizer31.Add(self.help_button2, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add((120,180), 1)
        sizer3.Add(sizer31, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)

        #添加参数子块，带边框的模块布局
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'MAC/PHY层参数'), wx.VERTICAL)
        sizer5.Add(sizer2, 0, wx.EXPAND | wx.ALL, 10)

        sizer6 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'RLC层参数'), wx.VERTICAL)
        sizer6.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        # sizer7 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'终端A'), wx.VERTICAL)
        sizer7 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'RNTI61'), wx.VERTICAL)
        sizer7.Add(sizerA, 0, wx.EXPAND | wx.ALL, 10)

        # sizer8 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'终端B'), wx.VERTICAL)
        sizer8 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'RNTI65'), wx.VERTICAL)
        sizer8.Add(sizerB, 0, wx.EXPAND | wx.ALL, 10)

        sizer9 = wx.BoxSizer(wx.VERTICAL)
        sizer9.Add(sizer7, 0, wx.EXPAND | wx.ALL, 10)
        sizer9.Add(sizer8, 0, wx.EXPAND | wx.ALL, 10)
        sizer9.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(sizer5, 0, wx.EXPAND | wx.ALL, 10)
        sizer1.Add(sizer6, 0, wx.EXPAND | wx.ALL, 10)

        sizer10 = wx.BoxSizer(wx.HORIZONTAL)
        sizer10.Add(sizer1, 0, wx.EXPAND | wx.ALL, 5)
        sizer10.Add(sizer9, 0, wx.EXPAND | wx.ALL, 5)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer10, 0, wx.EXPAND | wx.ALL, 5)

        #自动调整界面尺寸
        self.SetSizer(box)
        box.Fit(self)
        box.SetSizeHints(self)

    def Help(self,event):
        self.dialog = Help_Dialog(self)
        # self.dialog.ShowModal()
        self.dialog.Show()

    def Help_dialog2(self,event):
        dlg = wx.MessageDialog(None, "根据标准TS36.211   Table 5.5.3.2-1\t\n\
        当链路带宽为1.4M，C_SRS、B_SRS、n_RRC的值应分别设置为：4、1、0\n\t当链路带宽为3M，C_SRS、B_SRS、n_RRC的值应分别设置为：0、1、0",
                          '帮助',
                          wx.OK | wx.ICON_INFORMATION)
        retCode = dlg.ShowModal()
