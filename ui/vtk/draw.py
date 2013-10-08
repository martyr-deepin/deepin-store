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

from constant import DEFAULT_FONT, DEFAULT_FONT_SIZE
from color import color_hex_to_cairo 
from utils import get_text_size
import cairo
import pango
import pangocairo




def draw_pixbuf(cr, pixbuf, x, y, alpha=1.0):
    cr.set_source_pixbuf(pixbuf, x, y)
    cr.paint_with_alpha(1.0)

def draw_text(cr, text, x, y, w=0, h=0,
              text_size=DEFAULT_FONT_SIZE,
              text_color="#FFFFFF",
              text_font=DEFAULT_FONT,
              alignment=None,
              pango_list=None,
              markup=None):
    cr.set_source_rgb(*color_hex_to_cairo(text_color)) 

    context = pangocairo.CairoContext(cr)
    layout = context.create_layout()
    # 设置字体.
    layout.set_font_description(pango.FontDescription("%s %s" % (text_font, text_size)))
    # 设置文本.
    layout.set_text(text) 
    # add pango list attributes.
    if pango_list:
        layout.set_attributes(pango_list)
    # 设置文本的alignment.
    text_size = get_text_size(text, text_size, text_font)
    x_padding, y_padding = 0, 0
    if alignment == pango.ALIGN_LEFT:
        x_padding = 0
        y_padding = h/2 - text_size[1]/2
    elif alignment == pango.ALIGN_CENTER:
        x_padding = w/2 - text_size[0]/2
        y_padding = h/2 - text_size[1]/2
    elif alignment == pango.ALIGN_RIGHT:
        x_padding = w - text_size[0]
        y_padding = h/2 - text_size[1]/2
    # 设置markup.
    if markup:
        layout.set_markup(markup)
        if alignment:
            layout.set_alignment(alignment)
    # 设置移动.
    cr.move_to(x + x_padding, y + y_padding)
    #
    context.update_layout(layout)
    context.show_layout(layout)

def draw_tray_text(cr, text, x, y, 
                  out_text_color="#000000",
                  in_text_color="#FFFFFF",
                  line_width=2,
                  text_font=DEFAULT_FONT,
                  text_size=DEFAULT_FONT_SIZE,
                  ):
    line_width = line_width
    cr_alpha = 0.35
    # set out text color.
    r, g, b = color_hex_to_cairo(out_text_color)
    context = pangocairo.CairoContext(cr)
    layout = context.create_layout()
    layout.set_font_description(pango.FontDescription("%s %s" % (text_font, text_size)))
    # set text.
    layout.set_text(text)
    #
    cr.move_to(x, y)
    cr.save()       
    cr.layout_path(layout)
    cr.set_line_width(line_width)
    cr.set_source_rgba(r, g, b, cr_alpha)
    cr.stroke_preserve()
    cr.fill()
    cr.restore()

    cr.save()
    cr.new_path()

    r, g, b = color_hex_to_cairo(in_text_color) 
    cr.set_source_rgb(r, g, b)
    cr.set_operator(cairo.OPERATOR_OVER)

    cr.move_to(x, y)       
    context.show_layout(layout)
        
