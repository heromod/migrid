#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6.3 on Fri Feb  6 16:45:53 2009

import wx


class MyEpiFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyEpiFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        # Menu Bar
        self.frame_1_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        self.Quit = wx.MenuItem(wxglade_tmp_menu, wx.NewId(), "Quit", "Quit program", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.Quit)
        self.frame_1_menubar.Append(wxglade_tmp_menu, "File")
        self.SetMenuBar(self.frame_1_menubar)
        # Menu Bar end
        self.label_1 = wx.StaticText(self, -1, "Data file")
        self.datafile = wx.TextCtrl(self, -1, "RfilesAndscripts/Inter99All290606.sav")
        self.button_1 = wx.Button(self, -1, "Browse")
        self.label_2 = wx.StaticText(self, -1, "First gene index")
        self.g1 = wx.TextCtrl(self, -1, "74", style=wx.TE_CENTRE)
        self.label_3 = wx.StaticText(self, -1, "Last gene index")
        self.g2 = wx.TextCtrl(self, -1, "103", style=wx.TE_CENTRE)
        self.label_3_copy = wx.StaticText(self, -1, "First trait index")
        self.t1 = wx.TextCtrl(self, -1, "7", style=wx.TE_CENTRE)
        self.label_3_copy_1 = wx.StaticText(self, -1, "Last trait index")
        self.t2 = wx.TextCtrl(self, -1, "37", style=wx.TE_CENTRE)
        self.label_8 = wx.StaticText(self, -1, "Selection variable index")
        self.sv = wx.TextCtrl(self, -1, "2", style=wx.TE_CENTRE)
        self.label_9 = wx.StaticText(self, -1, "Classes")
        self.c1 = wx.TextCtrl(self, -1, "1")
        self.label_10 = wx.StaticText(self, -1, "to")
        self.c2 = wx.TextCtrl(self, -1, "2")
        self.runlocal = wx.CheckBox(self, -1, "Run on local host")
        self.label_6 = wx.StaticText(self, -1, "Output directory")
        self.outputdir = wx.TextCtrl(self, -1, "epifiles/")
        self.button_2 = wx.Button(self, -1, "Browse")
        self.label_4 = wx.StaticText(self, -1, "Status:")
        self.statusfeed = wx.TextCtrl(self, -1, "Status feed from MiG jobs", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        self.label_5 = wx.StaticText(self, -1, "Overall:")
        self.progress = wx.TextCtrl(self, -1, "")
        self.label_7 = wx.StaticText(self, -1, "jobs completed")
        self.Stop = wx.Button(self, -1, "Stop")
        self.Start = wx.Button(self, -1, "Start")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyEpiFrame.__set_properties
        self.SetTitle("Epistasis on MiG")
        self.SetSize((519, 784))
        self.c1.SetMinSize((30, 27))
        self.c2.SetMinSize((30, 27))
        self.statusfeed.SetFont(wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.progress.Enable(False)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyEpiFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_3 = wx.GridSizer(1, 3, 0, 0)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_4 = wx.GridSizer(1, 3, 0, 10)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_2 = wx.GridSizer(6, 2, 0, 0)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.GridSizer(1, 3, 0, 0)
        grid_sizer_1.Add(self.label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.datafile, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.button_1, 0, wx.ALIGN_RIGHT, 0)
        sizer_1.Add(grid_sizer_1, 0, wx.TOP|wx.BOTTOM|wx.EXPAND, 10)
        grid_sizer_2.Add(self.label_2, 0, 0, 0)
        grid_sizer_2.Add(self.g1, 0, 0, 0)
        grid_sizer_2.Add(self.label_3, 0, 0, 0)
        grid_sizer_2.Add(self.g2, 0, 0, 0)
        grid_sizer_2.Add(self.label_3_copy, 0, 0, 0)
        grid_sizer_2.Add(self.t1, 0, 0, 0)
        grid_sizer_2.Add(self.label_3_copy_1, 0, 0, 0)
        grid_sizer_2.Add(self.t2, 0, 0, 0)
        grid_sizer_2.Add(self.label_8, 0, 0, 0)
        grid_sizer_2.Add(self.sv, 0, 0, 0)
        grid_sizer_2.Add(self.label_9, 0, 0, 0)
        sizer_5.Add(self.c1, 0, 0, 0)
        sizer_5.Add(self.label_10, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(self.c2, 0, 0, 0)
        grid_sizer_2.Add(sizer_5, 0, 0, 0)
        sizer_1.Add(grid_sizer_2, 0, wx.EXPAND, 0)
        sizer_4.Add(self.runlocal, 0, 0, 0)
        sizer_1.Add(sizer_4, 0, wx.EXPAND, 0)
        grid_sizer_4.Add(self.label_6, 0, 0, 0)
        grid_sizer_4.Add(self.outputdir, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_4.Add(self.button_2, 0, wx.ALIGN_RIGHT, 0)
        sizer_1.Add(grid_sizer_4, 0, wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        sizer_2.Add(self.label_4, 0, 0, 0)
        sizer_2.Add(self.statusfeed, 6, wx.ALL|wx.EXPAND, 10)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
        grid_sizer_3.Add(self.label_5, 0, 0, 0)
        grid_sizer_3.Add(self.progress, 0, 0, 0)
        grid_sizer_3.Add(self.label_7, 0, 0, 0)
        sizer_1.Add(grid_sizer_3, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_3.Add(self.Stop, 0, 0, 0)
        sizer_3.Add(self.Start, 0, 0, 0)
        sizer_1.Add(sizer_3, 0, wx.ALIGN_RIGHT, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

# end of class MyEpiFrame


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MyEpiFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()