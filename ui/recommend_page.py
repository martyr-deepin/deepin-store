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

from math import pi
import gobject
import gtk
import os
from deepin_utils.file import get_parent_dir
from dtk.ui.draw import draw_pixbuf
from dtk.ui.iconview import IconItem
from events import global_event

PKG_PICTURE_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update_data", "recommend_picture", "zh_CN")

class RecommendIconItem(IconItem):
    '''
    class docs
    '''
    
    def __init__(self, pkg_name):
        '''
        init docs
        '''
        IconItem.__init__(self)
        self.pkg_name = pkg_name
        self.pkg_picture_pixbuf = None
        self.hover_flag = False
        
    def get_width(self):
        '''
        Get item width.
        
        This is IconView interface, you should implement it.
        '''
        return 177
    
    def get_height(self):
        '''
        Get item height.
        
        This is IconView interface, you should implement it.
        '''
        return 108
    
    def render(self, cr, rect):
        if self.pkg_picture_pixbuf == None:
            self.pkg_picture_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(PKG_PICTURE_DIR, "%s.jpg" % self.pkg_name))
            
        padding_x = (rect.width - self.pkg_picture_pixbuf.get_width()) / 2
        padding_y = (rect.height - self.pkg_picture_pixbuf.get_height()) / 2
        draw_pixbuf(cr, 
                    self.pkg_picture_pixbuf, 
                    rect.x + padding_x,
                    rect.y + padding_y)    
        
    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.
        
        This is IconView interface, you should implement it.
        '''
        global_event.emit("switch-to-detail-page", self.pkg_name)
    
    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> del self.pixbuf
        >>> self.pixbuf = None

        This is IconView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        if self.pkg_picture_pixbuf:
            del self.pkg_picture_pixbuf
            self.pkg_picture_pixbuf = None
            
        return True
        
gobject.type_register(RecommendIconItem)
        

