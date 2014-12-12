#!/usr/bin/env python
#coding=utf-8
#################################
#   Copyright 2014.7.23
#       fly_video
#################################
import lte_sat

import wx
import wx.grid
import sys, glob
import os
import threading
import multiprocessing
from multiprocessing import Queue
import traceback,time
from wx.lib.pubsub import Publisher

import numpy as np

#设置系统默认编码方式，不用下面两句，中文会乱码
reload(sys)  
sys.setdefaultencoding("utf-8")

class Detail_Disp(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent,style = wx.TAB_TRAVERSAL)
        self.Centre()
        self.SetBackgroundColour("white")
        
        #创建面板
        self.createframe()

        # 创建一个pubsub接收器,用于接收从子线程传递过来的消息
        Publisher().subscribe(self.updateDisplay, "update")
    
    def updateDisplay(self, msg):
        """
        从线程接收数据并且在界面更新显示
        """
        dict_status = msg.data
        # print str(dict_status)

        rows_rx = [('RX CRC错误总包数',dict_status['rx_wrong_mac_pdu_count']+' packet'),
        ('RX CRC错误字节数',dict_status['rx_wrong_mac_pdu_bytes']+' bytes'),
        ('RX CRC正确总包数',dict_status['rx_right_mac_pdu_count']+' packet'),
        ('RX CRC正确字节数',dict_status['rx_right_mac_pdu_bytes']+' bytes'),
        ('RX CRC正确字节速率',dict_status['rx_crc_right']+' B/s'),
        ('RX CRC　　误包率',str(dict_status['rx_crc_wrong_rate'])+' %'),
        ('',''),
        ('MAC==>RLC总包数',dict_status['rx_rlc_pdu_count']+' packet'),
        ('MAC==>RLC字节数',dict_status['rx_rlc_pdu_bytes']+' bytes'),
        ('MAC==>RLC字节速率',dict_status['rx_mac2rlc']+' B/s'),
        ('',''),
        ('RLC==>高层总包数',dict_status['rx_rlc_sdu_count']+' packet'),
        ('RLC==>高层字节数',dict_status['rx_rlc_sdu_bytes']+' bytes'),
        ('RLC==>高层字节速率',dict_status['rx_rlc2']+' B/s'),
        ('',''),
        ('eNB检测到的SR数',dict_status['rx_sr_num']),
        ('eNB检测到的BSR数',dict_status['rx_bsr_num']),
        ('sync递交子帧数目',dict_status['sync_subf_num']+' 个'),
        ('RNTI61有效TA ',dict_status['detected_ta_num_rnti61']+' 个'),
        ('RNTI65有效TA ',dict_status['detected_ta_num_rnti65']+' 个'),
        ('RNTI61实时TA ',dict_status['rx_real_time_ta_rnti61']),
        ('RNTI65实时TA ',dict_status['rx_real_time_ta_rnti65']),
        ('上行DEMUX子帧数目  ',dict_status['dempper_suf_num']+' 个'),
        ('统计数据间隔为  ',str(dict_status['rate_record_time'])+' ms'),
        ]

        rows_tx = [
        ('TX 高层==>RLC总包数',dict_status['tx_rlc_sdu_count']+' packet'),
        ('TX 高层==>RLC字节数',dict_status['tx_rlc_sdu_bytes']+' bytes'),
        ('TX 高层==>RLC字节速率',dict_status['tx_2rlc']+' B/s'),
        ('',''),
        ('TX RLC==>MAC总包数',dict_status['tx_rlc_pdu_count']+' packet'),
        ('TX RLC==>MAC字节数',dict_status['tx_rlc_pdu_bytes']+' bytes'),
        ('TX RLC==>MAC字节速率',dict_status['tx_rlc2mac']+' B/s'),
        ('TX USG总数目 ',dict_status['tx_usg_count']),        
        ]

        for index in range(len(rows_rx)):
            self.list_rx.SetStringItem(index, 1, str(rows_rx[index][1]))

        for index in range(len(rows_tx)):
            self.list_tx.SetStringItem(index, 1, str(rows_tx[index][1]))            

    def create_list_ctrl(self):
            self.list_rx = wx.ListCtrl(self, -1, style=wx.LC_REPORT, size=(400,600))
            self.list_tx = wx.ListCtrl(self, -1, style=wx.LC_REPORT, size=(400,600))

            columns = ['名称','值']

            self.rows_rx = [('RX CRC错误总包数','0'),
            ('RX CRC错误字节数','0'),
            ('RX CRC正确总包数','0'),
            ('RX CRC正确字节数','0'),
            ('RX CRC正确字节速率','0'),
            ('RX CRC　　误包率','0'),
            ('',''),
            ('MAC==>RLC总包数','0'),
            ('MAC==>RLC字节数','0'),
            ('MAC==>RLC字节速率','0'),
            ('',''),
            ('RLC==>高层总包数','0'),
            ('RLC==>高层字节数','0'),
            ('RLC==>高层字节速率','0'),
            ('',''),
            ('eNB检测到的SR数','0'),
            ('eNB检测到的BSR数','0'),
            ('sync递交子帧数目','0'),
            ('RNTI61有效TA ','0'),
            ('RNTI65有效TA ','0'),
            ('RNTI61实时TA ','0'),
            ('RNTI65实时TA ','0'),
            ('上行DEMUX子帧数目  ','0'),
            ('统计数据间隔为  ','0'),
            ]  

            self.rows_tx = [
            ('TX 高层==>RLC总包数','0'),
            ('TX 高层==>RLC字节数','0'),
            ('TX 高层==>RLC字节速率','0'),
            ('',''),
            ('TX RLC==>MAC总包数','0'),
            ('TX RLC==>MAC字节数','0'),
            ('TX RLC==>MAC字节速率','0'),
            ('TX USG总数目 ','0'),
            ]              

            # Add some columns
            for col, text in enumerate(columns):
                self.list_rx.InsertColumn(col, text)

            for col, text in enumerate(columns):
                self.list_tx.InsertColumn(col, text)            

            # add the rows
            for item in self.rows_rx:
                index = self.list_rx.InsertStringItem(sys.maxint, item[0])
                for col, text in enumerate(item[1:]):
                    self.list_rx.SetStringItem(index, col+1, text)

            for item in self.rows_tx:
                index = self.list_tx.InsertStringItem(sys.maxint, item[0])
                for col, text in enumerate(item[1:]):
                    self.list_tx.SetStringItem(index, col+1, text)

            # set the width of the columns in various ways
            self.list_rx.SetColumnWidth(0, 250)
            # self.list_rx.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.list_rx.SetColumnWidth(1, 150)

            self.list_tx.SetColumnWidth(0, 250)
            self.list_tx.SetColumnWidth(1, 150)        

    def createframe(self):

        #绑定窗口的关闭事件
        # self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.create_list_ctrl()

        sizer_list = wx.BoxSizer(wx.HORIZONTAL)
        sizer_list.Add(self.list_rx, 0, wx.EXPAND|wx.TOP)
        sizer_list.Add(self.list_tx, 0, wx.EXPAND|wx.TOP)

        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'状态显示'), wx.VERTICAL)
        sizer2.Add(sizer_list, 0, wx.EXPAND | wx.ALL, 10)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL, 25)
        box1.Add(wx.StaticLine(self), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)

        # 自动调整界面尺寸
        self.SetSizer(box1)
