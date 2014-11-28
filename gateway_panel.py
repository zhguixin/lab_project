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

from Detail_Disp import Detail_Disp
from Detail_Dialog import Detail_Dialog

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
        wx.Frame.__init__(self, None, title=u"信关站界面", size=(1200,800))
        self.Centre()
        # self.SetBackgroundColour("white")

        self.sp = wx.SplitterWindow(self)
        self.panel = wx.Panel(self.sp, style=wx.SP_3D|wx.TAB_TRAVERSAL)
        self.p1 = Detail_Disp(self.sp)
        # self.sp.SplitVertically(self.panel,self.p1,500)
        self.sp.SplitVertically(self.p1,self.panel,360)

        self.panel.SetBackgroundColour("white")

        
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
            self.list_rx = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT, size=(400,600))
            self.list_tx = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT, size=(400,600))

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
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.create_list_ctrl()

        #详细显示按钮
        self.detail_button = wx.Button(self.panel, -1, u"详细显示")
        self.detail_button.SetBackgroundColour('black')
        self.detail_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Detail,self.detail_button)
        self.detail_button.Disable()

        sizer_list = wx.BoxSizer(wx.HORIZONTAL)
        sizer_list.Add(self.list_rx, 0, wx.EXPAND|wx.TOP)
        sizer_list.Add(self.list_tx, 0, wx.EXPAND|wx.TOP)

        #详细显示按钮
        sizer_detail = wx.BoxSizer(wx.HORIZONTAL)
        sizer_detail.Add((10,10), 1)
        sizer_detail.Add(self.detail_button, 0, wx.ALIGN_RIGHT)

        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'状态显示'), wx.VERTICAL)
        sizer2.Add(sizer_list, 0, wx.EXPAND | wx.ALL, 10)
        sizer2.Add(sizer_detail, 0, wx.EXPAND | wx.ALL, 10)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL, 25)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)

        # 自动调整界面尺寸
        self.panel.SetSizer(box1)

    def Detail(self,event):
        self.detail_dlg = Detail_Dialog(None)
        self.detail_dlg.Bind(wx.EVT_CLOSE, self.OnCloseWindowDetail)
        self.detail_dlg.Show()
        self.detail_button.Disable()

    def OnCloseWindowDetail(self,event):
        self.detail_button.Enable()
        self.detail_dlg.Destroy()

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
