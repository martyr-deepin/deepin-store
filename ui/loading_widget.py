#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Kaisheng Ye
# 
# Author:     Kaisheng Ye <kaisheng.ye@gmail.com>
# Maintainer: Kaisheng Ye <kaisheng.ye@gmail.com>
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
import math
from dtk.ui.utils import alpha_color_hex_to_cairo
from skin import app_theme

class Loading(gtk.Button):
    
    rate = 60.0

    def __init__(self, diameter=30, line_width=4):
        gtk.Button.__init__(self)
        self.diameter = diameter
        self.line_width = line_width

        self.set_size_request(diameter, diameter)
        self.radian_per_part = 2*math.pi/self.rate

        self.tick_radian = 0
        
        self.connect("expose-event", self.expose)

        gtk.timeout_add(10, self.tick)

    def expose(self, widget, event=None):
        cr = widget.window.cairo_create()
        rect = widget.get_allocation()

        cr.set_line_width(self.line_width)
        for i in range(int(self.rate)):
            cr.set_source_rgba(*alpha_color_hex_to_cairo((app_theme.get_color("sidebar_select").get_color(), i/self.rate)))
            cr.arc(
                rect.x + rect.width / 2, 
                rect.y + rect.height / 2, 
                (self.diameter-self.line_width)/2.0, 
                self.tick_radian + i * self.radian_per_part, 
                self.tick_radian + (i+1) * self.radian_per_part
            )
            cr.stroke()
        return True

    def tick(self):
        self.tick_radian += self.radian_per_part
        self.queue_draw()
        return True

if __name__ == '__main__':
    win = gtk.Window()
    win.set_position(gtk.WIN_POS_CENTER)
    win.set_size_request(400, 300)
    win.connect("destroy", gtk.main_quit)

    loading_widget = Loading("#00F")
    loading_widget_align = gtk.Alignment()
    loading_widget_align.set(0.5, 0.5, 0, 0)
    loading_widget_align.add(loading_widget)

    win.add(loading_widget_align)
    win.show_all()
    gtk.main()
