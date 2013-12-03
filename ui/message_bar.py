#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
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

from skin import app_theme
from dtk.ui.cycle_strip import CycleStrip
from dtk.ui.label import Label
import gtk

class MessageBar(CycleStrip):
    '''
    class docs
    '''
	
    def __init__(self, padding_left=0):
        '''
        init docs
        '''
        # Init.
        CycleStrip.__init__(self, app_theme.get_pixbuf("strip/background.png"))
        
        self.label = Label()
        self.label_align = gtk.Alignment()
        self.label_align.set(0.0, 0.5, 0, 0)
        self.label_align.set_padding(0, 0, padding_left, 0)
        self.label_align.add(self.label)
        self.pack_start(self.label_align, True, True)
        
    def set_message(self, message):
        self.label.set_text(message)
