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

import os
from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.utils import get_content_size
from deepin_utils.file import get_parent_dir
from data import DATA_ID
from nls import _
from constant import LANGUAGE

ICON_SIZE = 48
STAR_SIZE = 13

ITEM_PKG_OFFSET_X = 22
ITEM_CHECKBUTTON_WIDTH = 32
ITEM_CHECKBUTTON_PADDING_X = 8
ITEM_CHECKBUTTON_PADDING_Y = 29
ITEM_INFO_AREA_WIDTH = -1
ITEM_STAR_AREA_WIDTH = STAR_SIZE * 5
ITEM_BUTTON_PADDING_RIGHT = 40
ITEM_NO_NOTIFY_AREA_WIDTH = 130
ITEM_NOTIFY_AGAIN_AREA_WIDTH = 100

ITEM_NO_NOTIFY_STRING = _("No reminder")
(ITEM_NO_NOTIFY_WIDTH, ITEM_NO_NOTIFY_HEIGHT) = get_content_size(ITEM_NO_NOTIFY_STRING)
ITEM_NOTIFY_AGAIN_STRING = _("Remind again")
(ITEM_NOTIFY_AGAIN_WIDTH, ITEM_NOTIFY_AGAIN_HEIGHT) = get_content_size(ITEM_NOTIFY_AGAIN_STRING)

if LANGUAGE == 'en_US':
    NAME_SIZE = 9
    ITEM_STATUS_TEXT_PADDING_RIGHT = 175
    ITEM_BUTTON_AREA_WIDTH = 190
    ITEM_BUTTON_PADDING_RIGHT = 70
    DEFAULT_FONT_SIZE = 9
    ITEM_CONFIRM_BUTTON_PADDING_RIGHT = 130
    ITEM_CANCEL_BUTTON_PADDING_RIGHT = 80
else:
    NAME_SIZE = 10
    ITEM_STATUS_TEXT_PADDING_RIGHT = 130
    ITEM_BUTTON_AREA_WIDTH = 160
    ITEM_BUTTON_PADDING_RIGHT = 40
    DEFAULT_FONT_SIZE = 10
    ITEM_CONFIRM_BUTTON_PADDING_RIGHT = 100
    ITEM_CANCEL_BUTTON_PADDING_RIGHT = 50


ITEM_HEIGHT = 74
ITEM_PADDING_X = 10
ITEM_PADDING_Y = 13
ITEM_PADDING_MIDDLE = 10
SHORT_DESC_PADDING_Y = 4

PROGRESSBAR_HEIGHT = 12

ICON_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update", DATA_ID, "app_icon")

def get_icon_pixbuf_path(pkg_name):
    if os.path.exists(os.path.join(ICON_DIR, "%s.png" % pkg_name)):
        return os.path.join(ICON_DIR, "%s.png" % (pkg_name))
    else:
        return os.path.join(ICON_DIR, "default.png")

def render_pkg_icon(cr, rect, icon_pixbuf, offset_x=0):
    # Draw icon.
    draw_pixbuf(cr, 
                icon_pixbuf, 
                rect.x + ITEM_PADDING_X + offset_x + (ICON_SIZE - icon_pixbuf.get_width()) / 2,
                rect.y + ITEM_PADDING_Y,
                )    
    
def render_pkg_name(cr, rect, alias_name, text_width, offset_x=0):
    draw_text(cr, 
              alias_name, 
              rect.x + ITEM_PADDING_X + ICON_SIZE + ITEM_PADDING_MIDDLE + offset_x,
              rect.y + ITEM_PADDING_Y,
              text_width,
              NAME_SIZE,
              text_size=NAME_SIZE)
    
def render_pkg_info(cr, rect, alias_name, pkg_name, icon_pixbuf, first_info, second_info, offset_x=0):
    text_width = rect.width - ICON_SIZE - ITEM_PADDING_X * 2 - ITEM_PADDING_MIDDLE
    
    # Draw icon.
    render_pkg_icon(cr, rect, icon_pixbuf, offset_x)
        
    # Draw name.
    render_pkg_name(cr, rect, alias_name, text_width, offset_x)
    
    # Draw first pkg information.
    draw_text(cr,
              first_info,
              rect.x + ITEM_PADDING_X + ICON_SIZE + ITEM_PADDING_MIDDLE + offset_x,
              rect.y + ITEM_PADDING_Y + DEFAULT_FONT_SIZE * 2,
              text_width,
              DEFAULT_FONT_SIZE,
              text_size=DEFAULT_FONT_SIZE,
              text_color="#333333")
    
    # Draw second pkg information.
    if second_info:
        draw_text(cr,
                  second_info,
                  rect.x + ITEM_PADDING_X + ICON_SIZE + ITEM_PADDING_MIDDLE + offset_x,
                  rect.y + ITEM_PADDING_Y + DEFAULT_FONT_SIZE * 4,
                  text_width,
                  DEFAULT_FONT_SIZE,
                  text_size=DEFAULT_FONT_SIZE,
                  text_color="#333333")

def render_star(cr, rect, star_buffer):
    star_buffer.render(cr, rect)

def get_star_level(star_level):
    return int(round(star_level))
