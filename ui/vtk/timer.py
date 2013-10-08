#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Hailong Qiu
#
# Author:     Hailong Qiu <356752238@qq.com>
# Maintainer: Hailong Qiu <356752238@qq.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import gobject

class Timer(gobject.GObject):
    __gsignals__ = {
        "Tick" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                  ())
        }        
    def __init__(self, interval_=0):
        gobject.GObject.__init__(self)
        self.__interval = interval_
        self.__enabled  = False # True : 开启 ; False : 关闭.
        self.__timer_id = None
        
    ''' Enabled [get/set] methed
        enabled_ : bool value.
        return : bool value.
    '''    
    @property    
    def Enabled(self):
        return self.__enabled        
    
    @Enabled.setter
    def Enabled(self, enabled_):    
        self.__enabled = enabled_
        self.__run_timer()
        
    @Enabled.getter    
    def Enabled(self):    
        return self.__enabled
    
    ''' Interval [get/set] mothed
        interval_ : int value.
        return : int value.
    '''    
    @property
    def Interval(self):            
        return self.__interval
        
    @Interval.setter
    def Interval(self, interval_):
        self.__interval = interval_        
        self.__remove_timer()
        self.__run_timer()
        
    @Interval.getter    
    def Interval(self):    
        return self.__interval
            
    def __remove_timer(self):
        if self.__timer_id:
            gtk.timeout_remove(self.__timer_id)
            self.__timer_id = None
        
    def __run_timer(self):
        if not self.__timer_id:
            self.__timer_id = gtk.timeout_add(
                                  self.__interval, 
                                  self.__run_timer_send_function)
                    
    def __run_timer_send_function(self):
        if self.__enabled: # send connect.
            self.emit("Tick")
        return True    
        
if __name__ == "__main__":
    import time
    
    def btn1_clicked(widget):
        # print timer.Interval
        # timer.Interval  = 1000
        timer.Enabled = True
    
    def btn2_clicked(widget):
        # timer.Interval = 30
        timer.Enabled = False
        
    def timer_tick(tick):    
        print "i love c and linux."
        # timer.Enabled = False
        # timer.Interval = 5000
        # print "i love c and linux."
        # timer.Enabled = True        
        
    # init timer.
    timer = Timer(100)        
    timer.connect("Tick", timer_tick)
    timer.Enabled = True
    # timer.Interval = 30

    # init widget.
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    btn_hbox = gtk.HBox()
    btn1 = gtk.Button("改变时间")
    btn2 = gtk.Button("改变时间")    
    # button connect.
    btn1.connect("clicked", btn1_clicked)
    btn2.connect("clicked", btn2_clicked)
    #     
    btn_hbox.pack_start(btn1)
    btn_hbox.pack_start(btn2)
    win.add(btn_hbox)
    
    win.show_all()
    gtk.main()
