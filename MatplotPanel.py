#!/usr/bin/env python
#coding=utf-8
import wx

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

test_data = ()
class MatplotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,style = wx.TAB_TRAVERSAL)
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
        