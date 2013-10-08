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

from trayicon import TrayIcon
from window import ToolTip
from utils import propagate_expose, get_text_size
from utils import pixbuf_check, text_check
from draw import draw_pixbuf, draw_tray_text
from theme import vtk_theme
from timer import Timer
from constant import print_msg
import gtk
import atk
import cairo
import gobject
import sys 


class StatusIcon(TrayIcon):
    def __init__(self):
        TrayIcon.__init__(self)
        self.height = 16
        self.debug = False
        if len(sys.argv) >= 2:
            if sys.argv[1] == "debug":
                self.debug = True
        #self.set_size_request(-1, self.height)
        self.init_statusiocn_widgets()
        self.init_statusiocn_values()
        self.init_statusicon_events()

    def init_statusiocn_widgets(self):
        self.__main_hbox = gtk.HBox()
        self.add(self.__main_hbox)
    
    def init_statusiocn_values(self):
        self.draw_function_id = self.draw_function

    def init_statusicon_events(self):
        self.connect("expose-event", self.statusicon_draw_expose_event)

    def draw_function(self, cr, x, y, w, h):
        pass
         
    def statusicon_draw_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect
        #
        cr.rectangle(*rect)
        if self.debug:
            cr.set_source_rgba(0, 0, 1, 1.0)
        else:
            cr.set_source_rgba(1, 1, 1, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        #
        cr = widget.window.cairo_create()
        #
        self.draw_function_id(cr, x, y, w, h)
        #
        propagate_expose(widget, event) 
        return True

    ###########################################################
    def get_tray_position(self):
        return self.window.get_position()

    def get_tray_pointer(self):
        return self.window.get_pointer()

    def status_icon_new(self, 
                        text="", 
                        pixbuf=None, 
                        type=gtk.POS_LEFT
                        ):
        widget = Element() 
        self.widget_init(widget, text, pixbuf)
        if type == gtk.POS_LEFT:
            self.__main_hbox.pack_end(widget, False, False)
        else:
            self.__main_hbox.pack_start(widget, False, False)
        self.__main_hbox.show()
        #
        #print "button pixbuf:", widget.get_pixbuf() 
        #print "button text:", widget.get_text()
        return widget

    def widget_init(self, widget, text, pixbuf):
        widget.connect("hide", self.widget_hide_modify_statusicon_size)
        widget.connect("size-allocate", self.widget_realize_event)
        widget.set_size_request(-1, self.height)
        if text_check(text):
            widget.set_text(text)
        if pixbuf_check(pixbuf):
            widget.set_pixbuf(pixbuf)

    def widget_realize_event(self, widget, allocation):
        self.statusicon_modify_size()

    def widget_hide_modify_statusicon_size(self, widget):
        self.statusicon_modify_size()

    def statusicon_modify_size(self):
        width = 0
        for child in self.__main_hbox.get_children():
            if child.get_visible():
                width += child.allocation.width
        self.set_geometry_hints(None, width, self.height, width, self.height, -1, -1, -1, -1, -1, -1)


TRAY_TEXT_IMAGE_TYPE, TRAY_IMAGE_TEXT_TYPE = 0, 1


'''
@ get_pixbuf : return pixbuf
@ set_pixbuf : 设置pixbuf
@ set_icon_theme : 设置主题图表，只需要传入名字
@ set_from_file : 设置图片途径
@ set_text  : 设置文本
@ get_geometry : return x, y, w, h
@ expose_event(widget, event) : 链接重绘制函数
'''

class Element(gtk.Button):
    __gsignals__ = {
        "popup-menu-event" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
        }
    def __init__(self):
        gtk.Button.__init__(self)
        self.__init_element_values()
        self.__init_element_events()

    def __init_element_values(self):
        self.tool_tip = ToolTip()
        #self.__icon_theme = gtk.IconTheme()
        #
        self.__mode_type = TRAY_IMAGE_TEXT_TYPE
        self.__blinking_check = False
        self.__rotate_check = False
        self.rotate_angle = 0
        # init timer.
        self.timer = Timer(200)
        self.timer.Enabled = False
        self.timer.connect("Tick", self.timer_tick)
        # init event connect function.
        self.popup_menu = None
        self.expose_event = self.__expose_event_function 
        # add icon paths.
        #path = get_run_app_path("image")
        #self.append_search_path(path)
        # init left line pixbuf.
        self.left_line_pixbuf = self.load_icon("tray_left_line", size=22)
        self.left_line_w = self.left_line_pixbuf.get_width()
        self.left_line_h = self.left_line_pixbuf.get_height()
        # init right line pixbuf.
        self.right_lien_pixbuf = self.load_icon("tray_right_line", size=22)
        self.right_line_w = self.left_line_pixbuf.get_width()
        self.right_lien_h = self.right_lien_pixbuf.get_height()

    def timer_tick(self, tick):
        self.rotate_angle += 45
        self.queue_draw()

    def __init_element_events(self):
        self.connect("clicked", self.__widget_clicked_event)
        self.connect("button-press-event", self.__widget_button_press_event)
        self.connect("expose-event", self.__widget_expose_event)
        self.connect("enter-notify-event", self.__widget_enter_notify_event)
        self.connect("leave-notify-event", self.__widget_leave_notify_event)

    def append_search_path(self, file):
        self.__icon_theme.append_search_path(file)

    def get_pixbuf(self):
        image = self.get_image()
        if image:
            return image.get_pixbuf()
        else:
            return image

    def set_pixbuf(self, pixbuf):
        image = gtk.Image()
        image.set_from_pixbuf(pixbuf)
        self.set_image(image) 

    def set_icon_theme(self, name):
        try:
            pixbuf = self.load_icon(name)
            if pixbuf:
                self.set_pixbuf(pixbuf)
        except Exception, e:
            print_msg("set_icon_theme[error]:%s"%(e))

    def load_icon(self, name, size=16):
        return vtk_theme.get_pixbuf(name, size)

    def set_pixbuf_file(self, file_path):
        pixbuf = gtk.gdk.pixbuf_new_from_file(file_path)
        self.set_pixbuf(pixbuf)

    def set_from_file(self, file_path):
        self.set_pixbuf_file(file_path)

    def get_text(self):
        return self.get_label()

    def set_text(self, text):
        self.set_label(text)

    def set_mode_type(self, mode_type): # No
        self.__mode_type = mode_type

    def get_mode_type(self):
        return self.__mode_type

    def get_geometry(self):
        screen = self.get_screen() 
        area   = atk.Rectangle()
        origin = self.window.get_origin() 
        area.x      = origin[0] + self.allocation.x
        area.y      = origin[1] 
        area.width  = self.allocation.width
        area.height = self.allocation.height
        return (screen, area)

    def set_blinking(self, blinking_check): # 闪烁
        self.__blinking_check = blinking_check

    def set_rotate(self, rotate_check, interval=None): # 旋转
        if interval:
            self.timer.Interval = interval 
        self.__rotate_check = rotate_check
        self.timer.Enabled = rotate_check

    def set_tooltip_text(self, text):
        self.tool_tip.set_text(text)

    def __widget_clicked_event(self, widget):
        # emit event.
        self.emit("popup-menu-event", self.get_geometry())
        try:
            if self.popup_menu:
                self.popup_menu(widget, self.get_geometry())
        except Exception, e:
            print_msg("widget_clicked_event[error]:%s"%(e))

    def __widget_button_press_event(self, widget, event):
        if event.button == 3:
            self.emit("popup-menu-event", self.get_geometry())
                
    def __widget_expose_event(self, widget, event):
        return self.__expose_event_function(widget, event)

    def __expose_event_function(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect
        #
        self.__draw_left_line(widget, cr, x, y, w, h)
        # draw text and pixbuf.
        text = widget.get_text() 
        text_size = 9
        text_w = 0
        pixbuf = widget.get_pixbuf()
        pixbuf_w = 0
        if pixbuf != None:
            pixbuf_w = pixbuf.get_width() 
            #pixbuf_h = pixbuf.get_height()
            pixbuf_x_padding = x + 5
            if text == "":
                pixbuf_x_padding = x + w/2 - pixbuf_w/2 
            # 旋转 rotate.
            if self.__rotate_check:
                self.__draw_rotate(cr, rect, pixbuf)
                #pixbuf = pixbuf.rotate_simple(self.rotate_angle)
            else:
            # draw pixbuf.
                draw_pixbuf(cr, 
                            pixbuf, 
                            pixbuf_x_padding, 
                            y + h/2 - pixbuf.get_height()/2)
        if text != "":
            text_w, text_h = get_text_size(text, text_size=text_size)
            text_x_padding = x + pixbuf_w + self.left_line_w + 5, 
            if pixbuf == None:
                text_x_padding = x + w/2 - text_w/2
            draw_tray_text(cr, 
                      text, 
                      text_x_padding,
                      y + h/2 - text_h/2,
                      text_size=text_size)
        #
        self.__draw_right_line(widget, cr, x, y, w, h)
        self.__draw_press_rectangle(widget, cr, x, y, w, h)
        #
        w_padding = pixbuf_w + text_w + 8 + self.left_line_w + self.right_line_w
        widget.set_size_request(w_padding - 4, 16)
        #
        return True

    def __draw_rotate(self, cr, rect, pixbuf):
        from dtk.ui.utils import cairo_state
        from math import radians
        with cairo_state(cr):
            cr.translate(rect.x + rect.width/2 , rect.y + rect.height/2)
            cr.rotate(radians(self.rotate_angle))
            cr.translate(-rect.width/2, -rect.height/2)
            x_padding =  rect.width/2 - pixbuf.get_width()/2
            y_padding = rect.height/2 - pixbuf.get_height()/2
            draw_pixbuf(cr, pixbuf, x_padding, y_padding)

    def __draw_left_line(self, widget, cr, x, y, w, h):
        # draw left line.
        if widget.get_state() in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
            draw_pixbuf(cr, 
                        self.left_line_pixbuf, 
                        x, 
                        y + h/2 - self.left_line_h/2)

    def __draw_right_line(self, widget, cr, x, y, w, h):
        # draw right line.
        if widget.get_state() in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
            draw_pixbuf(cr, 
                        self.right_lien_pixbuf, 
                        x + w - self.right_line_w, 
                        y + h/2 - self.right_lien_h/2)

    def __draw_press_rectangle(self, widget, cr, x, y, w, h):
        # draw rectangle.
        if widget.get_state() == gtk.STATE_ACTIVE:
            cr.set_source_rgba(1, 1, 1, 0.1)
            cr.rectangle(x + self.left_line_w, 
                         y, 
                         w - self.left_line_w * 2, 
                         h)
            cr.fill()

    def __widget_enter_notify_event(self, widget, event):
        if self.tool_tip.draw_btn.get_label() != "":
            metry =  self.get_geometry()
            #screen = metry[0]
            rect   = metry[1]
            #screen_w = screen.get_width() 
            #screen_h = screen.get_height()
            x_padding = rect[0] + rect[2]/2 - self.tool_tip.get_size_request()[0]/2 
            x_padding -= self.__set_max_show_menu(x_padding)
            #y_padding_to_creen = self.tool_tip.get_size_request()[1]
            x = x_padding
            y = rect[1] - self.tool_tip.get_size_request()[1]
            self.tool_tip.show_all()
            self.tool_tip.move(x, y)

    def __set_max_show_menu(self, x):        
        screen_w = self.get_screen().get_width()        
        screen_rect_width = x + self.tool_tip.get_size_request()[0]
        if (screen_rect_width) > screen_w:
            return screen_rect_width - screen_w
        else:
            return 0

    def __widget_leave_notify_event(self, widget, event):
        self.tool_tip.hide_all()

gobject.type_register(Element)
gobject.type_register(StatusIcon)

