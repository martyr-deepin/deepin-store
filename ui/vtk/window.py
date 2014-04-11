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
from constant import print_msg
from draw  import draw_text
from color import alpha_color_hex_to_cairo, color_hex_to_cairo
from utils import new_surface, propagate_expose, get_text_size
from utils import cairo_popover, cairo_popover_rectangle 
#from blur.vtk_cairo_blur import gaussian_blur
from dtk_cairo_blur import gaussian_blur
import utils

import os
from deepin_utils.file import get_parent_dir

import dbus
import dbus.service
import dbus.mainloop.glib
from dbus.mainloop.glib import DBusGMainLoop
from deepin_utils.ipc import is_dbus_name_exists

SAHOW_VALUE = 2 
ARROW_WIDTH = 10

class TrayIconWin(gtk.Window):
    def __init__(self):
        #gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        # init values.
        self.init_values()
        self.init_trayicon_settings()
        self.init_trayicon_events()
        self.hide_all() 

    def init_values(self):
        self.surface = None
        self.old_w = 0
        self.old_h = 0
        self.old_offset = 0
        self.trayicon_x = SAHOW_VALUE * 2  
        self.trayicon_y = SAHOW_VALUE * 2
        self.trayicon_border = 2.5
        self.radius = 5
        self.arrow_width = ARROW_WIDTH
        self.arrow_height = ARROW_WIDTH/2 
        self.tray_pos_type = gtk.POS_BOTTOM
        self.offset = 30 
        self.ali_size = 10
        self.alpha = 0.95
        self.debug = False
        # colors.
        self.sahow_color = ("#000000", 0.15)
        self.border_out_color = ("#000000", 1.0)

    def init_trayicon_settings(self):
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        #self.set_modal(True)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_position(gtk.WIN_POS_NONE)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_MENU)
        self.set_opacity(self.alpha)
        #
        self.draw = gtk.EventBox()
        self.main_ali  = gtk.Alignment(0, 0, 1, 1)
        self.main_ali.connect_after("expose-event", self.main_ali_expose_event)
        # set main_ali padding size.
        self.set_pos_type(self.tray_pos_type)
        self.add(self.draw)
        self.draw.add(self.main_ali)
        self.hide_all()

    def main_ali_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        padding_top    = 0
        padding_bottom = self.arrow_height 
        x = self.ali_size + int(self.trayicon_x + padding_top)
        y = int(self.ali_size + self.trayicon_x + padding_bottom)
        w = int(self.ali_size + self.trayicon_x)
        h = int(self.ali_size + self.trayicon_x)
        #############################################
        if self.debug:
            cr.set_source_rgb(1, 0, 0)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            cr.set_source_rgb(0, 0, 1)
            cr.rectangle(rect.x + x, rect.y + h, rect.width - h - x, rect.height - w - y)
            cr.stroke()


    def add_plugin(self, widget):
        self.main_ali.add(widget)

    def remove_plugin(self, widget):
        if self.main_ali.get_children() != []:
            self.main_ali.remove(widget)
        else:
            print_msg("main_ali no widgets")

    def plugs_add_event(self, socket):
        pass 

    def plugs_remove_event(self, socket):
        pass

    def get_id(self):
        return self.socket.get_id()

    def init_trayicon_events(self):
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.connect("configure-event", self.menu_configure_event)
        self.connect("button-press-event", self.tray_icon_button_press) 
        self.connect("size-allocate", self.on_size_allocate)
        self.draw.connect("expose-event", self.draw_expose_event)
        self.connect("show", self.trayicon_show_event)
        self.connect("destroy", lambda w : gtk.main_quit())
        
    def menu_configure_event(self, widget, event):
        pass

    def tray_icon_button_press(self, widget, event):        
        if self.in_window_check(widget, event):
            self.hide_all()
            self.grab_remove()

    def in_window_check(self, widget, event):
        toplevel = widget.get_toplevel()
        window_x, window_y = toplevel.get_position()
        x_root = event.x_root
        y_root = event.y_root
        if not ((x_root >= window_x and x_root < window_x + widget.allocation.width) 
            and (y_root >= window_y and y_root < window_y + widget.allocation.height)):
            return True
        
    def trayicon_show_event(self, widget):
        gtk.gdk.pointer_grab(
            self.window,
            True,
            gtk.gdk.POINTER_MOTION_MASK
            | gtk.gdk.BUTTON_PRESS_MASK
            | gtk.gdk.BUTTON_RELEASE_MASK
            | gtk.gdk.ENTER_NOTIFY_MASK
            | gtk.gdk.LEAVE_NOTIFY_MASK,
            None,
            None,
            gtk.gdk.CURRENT_TIME)
        gtk.gdk.keyboard_grab(
                self.window, 
                owner_events=False, 
                time=gtk.gdk.CURRENT_TIME)
        self.grab_add()        

    def draw_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        #
        cr.rectangle(*rect)
        cr.set_source_rgba(1, 1, 1, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        cr = widget.window.cairo_create()
        x, y, w, h = rect
        self.expose_event_draw(cr)
        #
        propagate_expose(widget, event)
        return True

    def on_size_allocate(self, widget, alloc):
        x, y, w, h = self.allocation
        # !! no expose and blur.
        if ((self.old_w == w and self.old_h == h) 
            and self.offset == self.old_offset):
            return False
        # 
        self.surface, self.surface_cr = new_surface(w, h)
        self.compute_shadow(w, h)
        self.old_w = w
        self.old_h = h
        self.old_offset = self.offset

    def compute_shadow(self, w, h):
        # sahow.
        cairo_popover(self, self.surface_cr, 
                      self.trayicon_x, self.trayicon_y, 
                      w, h,
                      self.radius, 
                      self.arrow_width, self.arrow_height, self.offset,
                      pos_type=self.tray_pos_type)
        gaussian_blur(self.surface, SAHOW_VALUE)
        self.surface_cr.set_source_rgba( # set sahow color.
                *alpha_color_hex_to_cairo((self.sahow_color)))
        self.surface_cr.fill_preserve()
        gaussian_blur(self.surface, SAHOW_VALUE)
        # border.
        # out border.
        self.surface_cr.clip()
        cairo_popover(self, self.surface_cr, 
                      self.trayicon_x + self.trayicon_border, 
                      self.trayicon_y + self.trayicon_border, 
                      w, h + 1, 
                      self.radius, 
                      self.arrow_width, self.arrow_height, self.offset,
                      pos_type=self.tray_pos_type)
        self.surface_cr.set_source_rgba( # set out border color.
                *alpha_color_hex_to_cairo(self.border_out_color))
        self.surface_cr.set_line_width(self.border_width)
        self.surface_cr.fill()
        # in border.
        self.surface_cr.reset_clip()
        padding_h = 0.7 
        cairo_popover(self, self.surface_cr, 
                      self.trayicon_x + self.trayicon_border, 
                      self.trayicon_y + self.trayicon_border, 
                      w, h + padding_h, 
                      self.radius, 
                      self.arrow_width, self.arrow_height, self.offset,
                      self.tray_pos_type) 
        self.surface_cr.set_source_rgba(0, 0, 0, 0.7)
        self.surface_cr.set_line_width(self.border_width)
        self.surface_cr.fill()

    def expose_event_draw(self, cr):
        if self.surface:
            cr.set_source_surface(self.surface, 0, 0)
            cr.paint()
        
    def set_pos_type(self, pos_type):
        self.tray_pos_type = pos_type
        padding_top, padding_bottom = 0, 0
        #
        if pos_type == gtk.POS_TOP:
            padding_top = self.arrow_height
        else:
            padding_bottom = self.arrow_height 
        #
        self.main_ali.set_padding(
                self.ali_size + int(self.trayicon_x + padding_top),
                int(self.ali_size + self.trayicon_x + padding_bottom),
                int(self.ali_size + self.trayicon_x),
                int(self.ali_size + self.trayicon_x))

#######################################################################


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
        self.text_size = 10
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
        width_padding = 12
        height_padding = 10
        self.resize(1, 1)
        text_size = get_text_size("我们", text_size=self.text_size)
        #
        self.set_size_request(size[0] + width_padding + self.ali_left + self.ali_right, 
                              text_size[1] + height_padding + self.ali_top + self.ali_bottom)

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
        return True

class WrapLabel(gtk.Button):
    def __init__(self):
        gtk.Button.__init__(self)

        self.connect("expose-event", 
                     self.top_text_btn_expose_event, "#FFFFFF")

    def top_text_btn_expose_event(self, widget, event, font_color):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        text = widget.get_label()
        font_size = 12
        size = get_text_size(text, font_size)
        size_padding = get_text_size("a", font_size)
        size_padding = size_padding[0] * 35

        draw_text(cr, 
                  text,
                  rect.x,
                  rect.y + rect.height/2 - size[1]/2,
                  font_size,
                  font_color,
                  markup=text)

        widget.set_size_request(size[0], size[1])
        return True

from dtk.ui.init_skin import init_theme
init_theme()

DSC_UPDATE_MONITOR_NAME = 'com.linuxdeepin.softwarecenter_update_monitor'
DSC_UPDATE_MONITOR_PATH = '/com/linuxdeepin/softwarecenter_update_monitor'

DSC_SERVICE_NAME = "com.linuxdeepin.softwarecenter"
DSC_SERVICE_PATH = "/com/linuxdeepin/softwarecenter"

ACTION_INSTALL = 1
ACTION_UNINSTALL = 2
ACTION_UPGRADE = 3

ACTION_STR = {
        ACTION_INSTALL: "安装",
        ACTION_UPGRADE: "升级",
        ACTION_UNINSTALL: "卸载"
        }

class TipWindow(dbus.service.Object):
    def __init__(self, session_bus):
        dbus.service.Object.__init__(self, session_bus, DSC_UPDATE_MONITOR_PATH)
        icon_path = os.path.join(get_parent_dir(__file__, 3), 'image/logo48.png')
        self.status_icon = gtk.status_icon_new_from_file(icon_path)
        self.status_icon.connect("activate", self.show)
        self.status_icon.connect("popup-menu", self.show)
        self.win  = TrayIconWin()
        self.width = 150
        self.height = 70
        self.win.resize(self.width, self.height)
        self.win.move(1366-self.width-160, 768-self.height-30)
        self.label = WrapLabel()
        info = ("软件中心\n正在下载: 80.5%")
        self.label.set_label(info)
        label_align = self.create_align((0.5, 0.5, 1, 1), (3, 3, 5, 0))
        label_align.add(self.label)
        self.win.add_plugin(label_align)
        gtk.timeout_add(5000, self.show)

    def update_info(self, s):
        self.status_icon.set_tooltip_markup(s)

    def run(self):
        self.start_dsc_backend()
        gtk.main()

    def show(self, status_icon=None, button=None, activate_time=None):
        pass
        #self.win.set_redraw_on_allocate(True)

        #screen, rect, cons = self.status_icon.get_geometry()

        #if self.win.allocation.width != 1:
            #cal_width = self.win.allocation.width
            #print cal_width
        #else:
            #cal_width = self.width

        #self.win.offset = cal_width / 2

        #if self.win.allocation.height != 1:
            #cal_height = self.win.allocation.height
        #else:
            #cal_height = self.height

        #if (rect.x-self.win.offset+cal_width) <= screen.get_width():
            #if (rect.y - cal_height -20) > 0:
                #self.win.move(rect.x-self.win.offset, rect.y - cal_height -20)
            #else:
                #self.win.move(rect.x-self.win.offset, rect.y+20)
        #else:
            #self.win.offset = cal_width - (screen.get_width() - rect.x)
            #if (rect.y - cal_height - 20) > 0:
                #self.win.move(rect.x-self.win.offset, rect.y - cal_height - 20)
            #else:
                #self.win.move(rect.x-self.win.offset, rect.y+20)
        #self.win.show_all()

    def create_align(self, init, padding):
        align = gtk.Alignment(*init)
        align.set_padding(*padding)
        return align

    def start_dsc_backend(self):
        if is_dbus_name_exists(DSC_SERVICE_NAME, False):
            print "running..."
            #self.label.set_label("软件中心后端正在运行...")
            self.update_info("软件中心后端正在运行...")

            self.system_bus = dbus.SystemBus()
            bus_object = self.system_bus.get_object(DSC_SERVICE_NAME, DSC_SERVICE_PATH)
            self.bus_interface = dbus.Interface(bus_object, DSC_SERVICE_NAME)
            gtk.timeout_add(2000, lambda :self.system_bus.add_signal_receiver(
                    self.backend_signal_receiver, 
                    signal_name="update_signal", 
                    dbus_interface=DSC_SERVICE_NAME, 
                    path=DSC_SERVICE_PATH))
        else:
            print "error..."
            #self.label.set_label("出错了!\n软件中心的后端已退出")
            self.update_info("出错了!\n软件中心的后端已退出")
            gtk.timeout_add(3000, gtk.main_quit)
            #self.show()

    def backend_signal_receiver(self, messages):
        for message in messages:
            (signal_type, action_content) = message

            if signal_type == "download-start":
                (pkg_name, action_type) = action_content
                if action_type == ACTION_INSTALL:
                    pass
                elif action_type == ACTION_UPGRADE:
                    pass
                #self.label.set_label("开始下载...")
                self.update_info("开始下载...")
            
            elif signal_type == "download-update":
                (pkg_name, action_type, percent, speed, finish_number, total, downloaded_size, total_size) = action_content
                if action_type == ACTION_INSTALL:
                    pass
                elif action_type == ACTION_UPGRADE:
                    pass
                #self.label.set_label("正在下载：%i%% \n已完成：%s/%s (%s/%s)" % (
                    #percent, 
                    #utils.bit_to_human_str(downloaded_size), 
                    #utils.bit_to_human_str(total_size),
                    #finish_number+1,
                    #total,
                    #))
                self.update_info("正在下载：%i%% \n已完成：%s/%s (%s/%s)" % (
                    percent, 
                    utils.bit_to_human_str(downloaded_size), 
                    utils.bit_to_human_str(total_size),
                    finish_number+1,
                    total,
                    ))

            elif signal_type == "download-finish":
                (pkg_name, action_type) = action_content
                if action_type == ACTION_INSTALL:
                    pass
                elif action_type == ACTION_UPGRADE:
                    pass
                #self.label.set_label("下载完成")
                self.update_info("下载完成")

            elif signal_type == "download-failed":
                (pkg_name, action_type, error) = action_content
                #self.label.set_label("下载失败，2秒钟后退出...")
                self.update_info("下载失败，2秒钟后退出...")
                gtk.timeout_add(2000, gtk.main_quit)

            elif signal_type == "action-start":
                (pkg_name, action_type) = action_content
                #self.label.set_label("开始%s" % ACTION_STR[action_type])
                self.update_info("开始%s" % ACTION_STR[action_type])

            elif signal_type == "action-update":
                (pkg_name, action_type, percent, status) = action_content
                if int(float(percent)) != 100:
                    #self.label.set_label("正在%s - %i%%" % (ACTION_STR[action_type], percent))
                    self.update_info("正在%s - %i%%" % (ACTION_STR[action_type], percent))
                else:
                    #self.label.set_label("%s完成，2秒钟后退出" % ACTION_STR[action_type])
                    self.update_info("%s完成，2秒钟后退出" % ACTION_STR[action_type])
                    gtk.timeout_add(2000, gtk.main_quit)

            elif signal_type == "action-finish":
                (pkg_name, action_type, pkg_info_list) = action_content
                #self.label.set_label("%s完成，2秒钟后退出" % ACTION_STR[action_type])
                self.update_info("%s完成，2秒钟后退出" % ACTION_STR[action_type])
                gtk.timeout_add(2000, gtk.main_quit)

            elif signal_type == "action-failed":
                (pkg_name, action_type, pkg_info_list, errormsg) = action_content
                #self.label.set_label("%s失败，2秒钟后退出" % ACTION_STR[action_type])
                self.update_info("%s失败，2秒钟后退出" % ACTION_STR[action_type])
                gtk.timeout_add(2000, gtk.main_quit)

if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    
    if is_dbus_name_exists(DSC_UPDATE_MONITOR_NAME):
        print "Update MONITOR is running"
        bus_object = session_bus.get_object(DSC_UPDATE_MONITOR_NAME,
                                            DSC_UPDATE_MONITOR_PATH)
        bus_interface = dbus.Interface(bus_object, DSC_UPDATE_MONITOR_NAME)
        bus_interface.hello()
    else:
        bus = dbus.service.BusName(DSC_UPDATE_MONITOR_NAME, session_bus)
        win = TipWindow(session_bus)
        try:
            win.run()
        except:
            if hasattr(win, 'bus_interface'):
                win.bus_interface.request_quit()
