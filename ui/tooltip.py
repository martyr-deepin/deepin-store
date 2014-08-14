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

import cairo
import gtk
import pango
import pangocairo
import math
from dtk_cairo_blur import gaussian_blur
from dtk.ui.constant import DEFAULT_FONT, DEFAULT_FONT_SIZE

def cairo_popover_rectangle(widget,
                   surface_context,
                   trayicon_x, trayicon_y,
                   trayicon_w, trayicon_h,
                   radius):
    cr = surface_context
    x = trayicon_x
    y = trayicon_y
    w = trayicon_w - (trayicon_x * 2)
    h = trayicon_h - (trayicon_x * 2)
    # draw.
    cr.arc (x + radius,
            y + radius,
            radius,
            math.pi,
            math.pi * 1.5)

    cr.arc (x + w - radius,
            y + radius,
            radius,
            math.pi * 1.5,
            math.pi * 2.0)
    cr.arc(x + w - radius,
           y + h - radius,
           radius,
           0,
           math.pi * 0.5)

    cr.arc(x + radius,
           y + h - radius,
           radius,
           math.pi * 0.5,
           math.pi)

    cr.close_path()

def new_surface(width, height):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    surface_context = cairo.Context(surface)
    return  surface, surface_context

def propagate_expose(widget, event):
    if hasattr(widget, "get_child") and widget.get_child() != None:
        widget.propagate_expose(widget.get_child(), event)

def get_text_size(text, text_size=DEFAULT_FONT_SIZE, text_font=DEFAULT_FONT):
    try:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        cr = cairo.Context(surface)
        context = pangocairo.CairoContext(cr)
        layout = context.create_layout()
        temp_font = pango.FontDescription("%s %s" % (text_font, text_size))
        layout.set_font_description(temp_font)
        layout.set_text(text)
        return layout.get_pixel_size()
    except:
        return (0, 0)

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

def alpha_color_hex_to_cairo((color, alpha)):
    (r, g, b) = color_hex_to_cairo(color)
    return (r, g, b, alpha)

def color_hex_to_cairo(color):
    # 将 #FF0000 转换成 set_source_rgb 适应的值. 范围是 0.0 ~ 1.0
    gdk_color = gtk.gdk.color_parse(color)
    return (gdk_color.red / 65535.0, gdk_color.green / 65535.0, gdk_color.blue / 65535.0)


SAHOW_VALUE = 2
ARROW_WIDTH = 10

DRAW_WIN_TYPE_BG = "bg"
DRAW_WIN_TYPE_FG = "fg"

class Window(gtk.Window):
    def __init__(self, type=gtk.WINDOW_TOPLEVEL):
        gtk.Window.__init__(self, type)
        self.__init_values()
        self.__init_settings()
        self.__init_widgets()
        self.__init_events()

    def __init_values(self):
        self.draw_rectangle_bool = True
        self.surface = None
        self.old_w = 0
        self.old_h = 0
        self.old_offset = 0
        self.trayicon_x = SAHOW_VALUE * 2
        self.trayicon_y = SAHOW_VALUE * 2
        self.trayicon_border = 3
        self.radius = 5
        self.ali_left = 8
        self.ali_right = 8
        self.ali_top  = 8
        self.ali_bottom = 7
        self.sahow_check = True
        # pixbuf.
        self.draw_win_type = DRAW_WIN_TYPE_FG
        self.bg_pixbuf = None
        self.bg_alpha = 1.0
        self.bg_x, self.bg_y = 0,0
        self.fg_alpha = 0.8
        # colors.
        self.base_color = "#FFFFFF"
        self.sahow_color = ("#000000", 0.3)
        self.border_out_color = ("#000000", 1.0)

    def __init_settings(self):
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.set_decorated(False)
        self.set_app_paintable(True)
        #

    def __init_widgets(self):
        self.__draw = gtk.EventBox()
        self.main_ali  = gtk.Alignment(1, 1, 1, 1)
        # set main_ali padding size.
        self.main_ali.set_padding(self.ali_top,
                                  self.ali_bottom,
                                  self.ali_left,
                                  self.ali_right)
        self.__draw.add(self.main_ali)
        self.add(self.__draw)

    def __init_events(self):
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.connect("size-allocate", self.__on_size_allocate)
        self.__draw.connect("expose-event", self.__draw_expose_event)
        self.connect("destroy", lambda w : gtk.main_quit())

    def __draw_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        #
        cr.rectangle(*rect)
        cr.set_source_rgba(1, 1, 1, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        cr = widget.window.cairo_create()
        x, y, w, h = rect
        # draw bg type background.
        if self.draw_win_type == DRAW_WIN_TYPE_BG:
            self.draw_background(cr, rect)
        #
        if self.sahow_check:
            self.__expose_event_draw(cr)
        # draw fg type background.
        if self.draw_win_type == DRAW_WIN_TYPE_FG:
            self.draw_background(cr, rect)
        #
        propagate_expose(widget, event)
        return True

    def draw_background(self, cr, rect):
        x, y, w, h = rect
        cr.save()
        cairo_popover_rectangle(self, cr,
                      self.trayicon_x + self.trayicon_border + 1,
                      self.trayicon_y + self.trayicon_border + 1,
                      w, h + 1,
                      self.radius)
        cr.clip()
        if self.bg_pixbuf:
            cr.set_source_pixbuf(self.bg_pixbuf, self.bg_x, self.bg_y)
            cr.paint_with_alpha(self.bg_alpha)
        else:
            cr.set_source_rgb(*color_hex_to_cairo(self.base_color))
            cr.rectangle(x, y, w, h)
            cr.fill()
        cr.restore()

    def __on_size_allocate(self, widget, alloc):
        x, y, w, h = self.allocation
        # !! no expose and blur.
        if ((self.old_w == w and self.old_h == h)):
            return False
        #
        self.surface, self.surface_cr = new_surface(w, h)
        self.__compute_shadow(w, h)
        self.old_w = w
        self.old_h = h

    def __compute_shadow(self, w, h):
        # sahow.
        cairo_popover_rectangle(self, self.surface_cr,
                      self.trayicon_x, self.trayicon_y,
                      w, h,
                      self.radius)
        self.surface_cr.set_source_rgba( # set sahow color.
                *alpha_color_hex_to_cairo((self.sahow_color)))
        self.surface_cr.fill_preserve()
        gaussian_blur(self.surface, SAHOW_VALUE)
        # border.
        if self.draw_rectangle_bool:
            # out border.
            self.surface_cr.clip()
            cairo_popover_rectangle(self, self.surface_cr,
                          self.trayicon_x + self.trayicon_border,
                          self.trayicon_y + self.trayicon_border,
                          w, h + 1,
                          self.radius)
            self.surface_cr.set_source_rgba( # set out border color.
                    *alpha_color_hex_to_cairo(self.border_out_color))
            self.surface_cr.set_line_width(self.border_width)
            self.surface_cr.fill()
            self.draw_in_border(w, h)

    def draw_in_border(self, w, h):
        # in border.
        self.surface_cr.reset_clip()
        cairo_popover_rectangle(self, self.surface_cr,
                      self.trayicon_x + self.trayicon_border + 1,
                      self.trayicon_y + self.trayicon_border + 1,
                      w, h + 1,
                      self.radius)
        self.surface_cr.set_source_rgba(1, 1, 1, 1.0) # set in border color.
        self.surface_cr.set_line_width(self.border_width)
        self.surface_cr.fill()

    def __expose_event_draw(self, cr):
        if self.surface:
            cr.set_source_surface(self.surface, 0, 0)
            cr.paint_with_alpha(self.fg_alpha)

    def set_bg_pixbuf(self, pixbuf, x=0, y=0, alpha=1.0):
        self.bg_pixbuf = pixbuf
        self.bg_x = x
        self.bg_y = y
        self.bg_alpha = alpha
        self.queue_draw()

    def set_draw_win_type(self, type=DRAW_WIN_TYPE_FG):
        self.draw_win_type = type
        self.queue_draw()

    def add_widget(self, widget):
        self.main_ali.add(widget)

class ToolTip(Window):
    def __init__(self):
        Window.__init__(self, gtk.WINDOW_POPUP)
        self.base_color = "#000000"
        self.sahow_check = False # 设置外发光.
        self.text_size = 11
        self.radius = 3 # 设置圆角.
        self.set_opacity(0.7) # 设置透明值.
        self.draw_btn = gtk.Button("")
        self.draw_btn.connect("expose-event", self.__draw_btn_expose_event)
        self.add_widget(self.draw_btn)

    def set_text(self, text):
        self.draw_btn.set_label(text)
        rect = self.draw_btn.allocation
        self.draw_btn.queue_draw_area(rect.x, rect.y, rect.width, rect.height)
        size = get_text_size(text, text_size=self.text_size)
        width_padding = 10
        height_padding = 15
        self.resize(1, 1)
        text_size = get_text_size("我们", text_size=self.text_size)
        self.set_size_request(size[0] + width_padding + 17,
                              text_size[1] + height_padding + 10)

    def __draw_btn_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        # draw background.
        b_x_padding, b_y_padding, b_w_padding, b_h_padding = 2, 2, 4, 4
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(rect.x + b_x_padding,
                     rect.y + b_y_padding,
                     rect.width - b_w_padding,
                     rect.height - b_h_padding)
        cr.fill()
        # draw text.
        text_color = "#FFFFFF"
        text = widget.get_label()
        size = get_text_size(text, text_size=self.text_size)
        x_padding = 5
        draw_text(cr, text,
                  rect.x + x_padding,
                  rect.y + rect.height/2 - size[1]/2, text_color=text_color, text_size=self.text_size)
        '''
        self.resize(1, 1)
        self.set_size_request(win_width,
                              win_height)
        '''
        return True


if __name__ == "__main__":
    #test = TrayIconWin()
    test = ToolTip()
    #test  = Window()
    #test.set_pos_type(gtk.POS_TOP)
    #test.set_pos_type(gtk.POS_BOTTOM)
    #test.set_bg_pixbuf(gtk.gdk.pixbuf_new_from_file("test.png"))
    #test.set_text("Linux Deepin 12.12 alpha")
    test.resize(380, 250)
    (screen, px, py, modifier_type) = test.get_display().get_pointer()
    test.move(px-10, py-10)
    test.set_text("Linux Deepin 12.12 alpha...........")
    test.show_all()
    gtk.main()
