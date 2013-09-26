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
from dtk.ui.application import Application

class Application(Application):
    '''
    This is the base class of every program based on deepin-ui.
    Every program should realize it.
    '''
    
    def __init__(self, 
                 app_support_colormap=True, 
                 resizable=True,
                 window_type=gtk.WINDOW_TOPLEVEL, 
                 close_callback=None,
                 ):
        '''
        Initialize the Application class.
        
        @param app_support_colormap: Set False if your program don't allow manipulate colormap, 
        such as mplayer, otherwise you should keep this option as True.
        @param resizable: Set this option with False if you want window's size fixed, default is True.
        '''
        # Init.
        self.app_support_colormap = app_support_colormap
        self.resizable = resizable
        self.window_type = window_type

        if close_callback:
            self.close_callback = close_callback
        else:
            self.close_callback = self.close_window

        self.skin_preview_pixbuf = None

        # Start application.
        self.init()

