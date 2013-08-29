#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011~2013 Deepin, Inc.
#               2011~2013 Kaisheng Ye
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
import gobject
from dtk.ui.utils import alpha_color_hex_to_cairo

class PanedBox(gtk.Bin):
    def __init__(self, bottom_window_height=39, bottom_show_first=False):
        gtk.Bin.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)

        self.content_box = None
        self.control_box = None
        self.show_bottom = False

        self.control_box_height = bottom_window_height

        self.bottom_win_show_check = False

        self.paint_bottom_window = self.__paint_bottom_window
        self.enter_bottom_win_callback = None
        self.bottom_show_first = bottom_show_first

    def do_realize(self):
        gtk.Bin.do_realize(self)
        self.set_realized(True)
        self.allocation.x = 0
        self.allocation.y = 0
        self.window = gtk.gdk.Window(
            self.get_parent_window(),
            window_type=gtk.gdk.WINDOW_CHILD,
            x=self.allocation.x,
            y=self.allocation.y,
            width=self.allocation.width,
            height=self.allocation.height,
            colormap=self.get_colormap(),
            wclass=gtk.gdk.INPUT_OUTPUT,
            visual=self.get_visual(),
            event_mask=(self.get_events() 
                      | gtk.gdk.EXPOSURE_MASK
                      | gtk.gdk.BUTTON_MOTION_MASK
                      | gtk.gdk.ENTER_NOTIFY_MASK
                      | gtk.gdk.LEAVE_NOTIFY_MASK
                      | gtk.gdk.POINTER_MOTION_HINT_MASK
                      | gtk.gdk.BUTTON_PRESS_MASK
                      ))
        self.window.set_user_data(self)
        #self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.__init_bottom_window()
        if self.content_box:
            self.content_box.set_parent_window(self.window)
        self.queue_resize()

    def __init_bottom_window(self):
        self.bottom_window = gtk.gdk.Window(
                self.window,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                x=0,
                y=0 + self.allocation.height - self.control_box_height,
                width=self.allocation.width, 
                height=self.control_box_height,
                event_mask=(self.get_events() 
                          | gtk.gdk.EXPOSURE_MASK
                          | gtk.gdk.BUTTON_PRESS_MASK
                          | gtk.gdk.BUTTON_RELEASE_MASK
                          | gtk.gdk.ENTER_NOTIFY_MASK
                          | gtk.gdk.LEAVE_NOTIFY_MASK
                          | gtk.gdk.POINTER_MOTION_MASK
                          | gtk.gdk.POINTER_MOTION_HINT_MASK
                          ))
        self.bottom_window.set_user_data(self)
        #self.style.set_background(self.bottom_window, gtk.STATE_NORMAL)
        if self.control_box:
            self.control_box.set_parent_window(self.bottom_window)

    def do_unrealize(self):
        gtk.Bin.do_unrealize(self)

    def do_map(self):
        gtk.Bin.do_map(self)
        self.set_flags(gtk.MAPPED)
        self.window.show()
        if self.bottom_show_first:
            self.bottom_window.show()
        else:
            self.bottom_window.hide()

    def do_unmap(self):
        gtk.Bin.do_unmap(self)

    def do_expose_event(self, e):
        gtk.Bin.do_expose_event(self, e)
        if e.window == self.bottom_window:
            self.paint_bottom_window(e)
            gtk.Bin.do_expose_event(self, e)
            return False
        return False

    def do_motion_notify_event(self, e):
        if e.window == self.bottom_window:
            if self.enter_bottom_win_callback:
                self.enter_bottom_win_callback()
        return False

    def __paint_bottom_window(self, e):
        bottom_rect = self.bottom_window.get_size()
        cr = self.window.cairo_create()
        cr.set_source_rgba(*alpha_color_hex_to_cairo(("#ff0000", 0.1)))
        cr.rectangle(0, 0, bottom_rect[0], bottom_rect[1])
        cr.fill()

    def __in_bottom_edge(self, e):
        min_x = 0
        max_x = 0 + self.bottom_window.get_size()[0]
        min_y = 0 + self.allocation.height - self.control_box_height
        max_y = 0 + self.allocation.height 
        return (min_y <= int(e.y) <= max_y and min_x <= int(e.x) <= max_x)

    def __in_bottom_win(self, e):
        width, height = self.bottom_window.get_size()
        min_x = 0
        max_x = 0 + width
        min_y = 0 + height - self.control_box_height
        max_y = 0 + height 
        return (min_y <= int(e.y) <= max_y and min_x <= int(e.x) <= max_x)

    def add_bottom_widget(self, widget):
        self.control_box = widget
        self.control_box.set_parent(self)

    def add_content_widget(self, widget):
        self.content_box = widget
        self.content_box.set_parent(self)

    def do_add(self, widget):
        gtk.Bin.do_add(self, widget)

    def do_remove(self, widget):
        widget.unparent()

    def do_forall(self, include_internals, callback, data):
        if self.control_box:
            callback(self.control_box, data)
        if self.content_box:
            callback(self.content_box, data)

    def do_size_request(self, req):
        if self.control_box:
            self.control_box.size_request()
        if self.content_box:
            self.content_box.size_request()

    def do_size_allocate(self, allocation):
        self.allocation = allocation
        self.allocation.x = 0
        self.allocation.y = 0
        # 
        self.set_all_size()

    def set_all_size(self):
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*self.allocation)
        if self.content_box:
            child1_allocation = gtk.gdk.Rectangle()
            child1_allocation.x = 0 
            child1_allocation.y = 0 
            child1_allocation.width = self.allocation.width
            child1_allocation.height = self.allocation.height
            self.content_box.size_allocate(child1_allocation)
            # top and bottom window move resize.
            if self.flags() & gtk.REALIZED:
                self.bottom_window.move_resize(0, 
                                               0 + self.allocation.height - self.control_box_height, 
                                               child1_allocation.width, 
                                               self.control_box_height)
                if self.control_box:
                    bottom_child_allocation = gtk.gdk.Rectangle()
                    bottom_child_allocation.x = 0
                    bottom_child_allocation.y = 0
                    bottom_child_allocation.width = child1_allocation.width
                    bottom_child_allocation.height = self.control_box_height
                    self.control_box.size_allocate(bottom_child_allocation)

gobject.type_register(PanedBox)
