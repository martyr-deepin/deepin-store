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
import gobject
from dtk.ui.star_view import StarBuffer
from server_action import FetchVoteInfo
from dtk.ui.threads import post_gui
from dtk.ui.iconview import IconItem
from dtk.ui.treeview import TreeItem
from dtk.ui.utils import get_event_coords, propagate_expose

STAR_SIZE = 13

class DscStarBuffer(StarBuffer):

    def __init__(self, pkg_name, obj=None):
        StarBuffer.__init__(self)
        self.pkg_name = pkg_name
        self.obj = obj
        FetchVoteInfo(pkg_name, self.update_vote_info).start()

    @post_gui
    def update_vote_info(self, vote_info):
        star = float(vote_info[0].encode('utf-8').strip())
        self.star_level = int(star)
        if isinstance(self.obj, IconItem) or isinstance(self.obj, TreeItem):
            if getattr(self.obj, 'star_level'):
                self.obj.star_level = int(star)
            self.obj.emit_redraw_request()

class StarView(gtk.Button):
    '''
    StarView class.
    
    @undocumented: expose_star_view
    @undocumented: motion_notify_star_view
    '''

    __gsignals__ = {
        "star-press" : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
    }

	
    def __init__(self, star_level=5):
        '''
        Initialize StarView class.
        '''
        gtk.Button.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.star_buffer = StarBuffer()
        self.read_only = False
        self.star_level = star_level
        
        self.set_size_request(STAR_SIZE * 5, STAR_SIZE)
        
        self.connect("leave-notify-event", self.leave_notify_star_view)
        self.connect("motion-notify-event", self.motion_notify_star_view)
        self.connect("expose-event", self.expose_star_view)        
        self.connect("button-press-event", self.star_button_press_handler)

    def set_star_level(self, star_level):
        self.star_level = star_level
        self.star_buffer.star_level = star_level
        self.queue_draw()

    def set_read_only(self, b):
        if b:
            self.read_only = True
            self.star_buffer.star_level = self.star_level
            self.queue_draw()
        else:
            self.read_only = False
            self.queue_draw()

    def star_button_press_handler(self, widget, event):
        (event_x, event_y) = get_event_coords(event)
        self.emit('star-press', int(min(event_x / (STAR_SIZE / 2) + 1, 10)))
        
    def expose_star_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        self.star_buffer.render(cr, rect)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
    def motion_notify_star_view(self, widget, event):
        if not self.read_only:
            (event_x, event_y) = get_event_coords(event)
            self.star_buffer.star_level = int(min(event_x / (STAR_SIZE / 2) + 1, 10))
            self.queue_draw()

    def leave_notify_star_view(self, widget, event):
        self.star_buffer.star_level = self.star_level
        self.queue_draw()
        
gobject.type_register(StarView)        

