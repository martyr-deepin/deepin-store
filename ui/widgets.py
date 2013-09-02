#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011~2012 Deepin, Inc.
#               2011~2012 Kaisheng Ye
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
import pango
from utils import get_common_image, get_common_image_pixbuf
from ui_utils import set_widget_vcenter
from constant import LANGUAGE
from skin import app_theme
#from ui_utils import draw_alpha_mask
from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.utils import get_content_size, is_in_rect
from dtk.ui.label import Label
from dtk.ui.button import CloseButton
from dtk.ui.utils import color_hex_to_cairo, set_clickable_cursor
from dtk.ui.theme import ui_theme

class ActionButton(Label):
    def __init__(self, 
                 text, 
                 enable_gaussian=False, 
                 text_color=ui_theme.get_color("link_text"),
                 ):
        '''
        Initialize LinkButton class.
        
        @param text: Link content.
        @param link: Link address.
        @param enable_gaussian: To enable gaussian effect on link, default is True.
        @param text_color: Link color, just use when option enable_gaussian is False.
        '''
        Label.__init__(self, text, text_color, enable_gaussian=enable_gaussian, text_size=9,
                       gaussian_radious=1, border_radious=0, underline=True)
        self.callback_action = None

        set_clickable_cursor(self)
        self.connect('button-press-event', self.button_press_action)

    def button_press_action(self, widget, e):
        if self.callback_action:
            self.callback_action()

class BottomTipBar(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        
        self.info_image_box = gtk.VBox()
        self.info_image_box.set_size_request(24, 24)
        self.info_image_box.connect('expose-event', self.expose_info_image_box)

        self.info_label = Label("")
        self.info_callback_button = ActionButton('')

        self.close_button = CloseButton()

        self.pack_start(self.info_image_box, False, False)
        self.pack_start(self.info_label)
        self.pack_start(self.info_callback_button, False, False)
        self.pack_start(self.close_button, False, False)

        self.connect('expose-event', self.expose)

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        cr.set_source_rgb(*color_hex_to_cairo('#cccccc'))
        cr.rectangle(rect.x, rect.y, rect.width, 1)
        cr.fill()

        cr.set_source_rgb(*color_hex_to_cairo('#ffffff'))
        cr.rectangle(rect.x, rect.y+1, rect.width, 1)
        cr.fill()

        cr.set_source_rgb(*color_hex_to_cairo('#fff9c9'))
        cr.rectangle(rect.x, rect.y+2, rect.width, rect.height-2)
        cr.fill()

    def expose_info_image_box(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        msg_pixbuf = get_common_image_pixbuf("msg/msg1.png")
        pix_width = msg_pixbuf.get_width()
        pix_height = msg_pixbuf.get_height()
        draw_pixbuf(cr,
                    msg_pixbuf,
                    rect.x + (rect.width-pix_width)/2,
                    rect.y + (rect.height-pix_height)/2,
                    )

    def update_info(self, info, callback_name='', callback_action=None):
        self.info_label.set_text(info)
        self.info_callback_button.set_text(callback_name)
        self.info_callback_button.callback_action = callback_action

class LoadingBox(gtk.VBox):
    
    def __init__(self):
        super(LoadingBox, self).__init__()
        
        loading_pixbuf = gtk.gdk.PixbufAnimation(get_common_image("loading.gif"))
        loading_image = gtk.Image()
        loading_image.set_from_animation(loading_pixbuf)
        
        main_box = gtk.VBox(spacing=5)
        main_box.pack_start(loading_image)
        self.add(set_widget_vcenter(main_box))

class NetworkConnectFailed(gtk.EventBox):
    
    def __init__(self, callback=None):
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.ENTER_NOTIFY_MASK |
                        gtk.gdk.LEAVE_NOTIFY_MASK
                        )

        
        self.connect("expose-event", self.on_expose_event)
        
        if LANGUAGE == "zh_CN":
            prefix = "cn"
        elif LANGUAGE in ["zh_HK", "zh_TW"]:    
            prefix = "tw"
        else:    
            prefix = "en"
            
        self.failed_dpixbuf = gtk.gdk.pixbuf_new_from_file(get_common_image("network/failed_%s.png" % prefix))
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("button-press-event", self.on_button_press)
        
        self.normal_text_dcolor = app_theme.get_color("labelText")
        self.hover_text_dcolor = app_theme.get_color("globalItemHighlight")
        self.prompt_text = "点击此处刷新"
        self.text_padding_y = 5
        self.text_padding_x = 5
        self.text_rect = None
        self.is_hover = False
        self.press_callback = callback
        
    def on_expose_event(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        failed_pixbuf = self.failed_dpixbuf
        #draw_alpha_mask(cr, rect.x, rect.y, rect.width, rect.height, "layoutLeft")
        pixbuf_offset_x = (rect.width - failed_pixbuf.get_width()) / 2 
        pixbuf_offset_y = (rect.height - failed_pixbuf.get_height()) / 2 - 20
        icon_x = rect.x + pixbuf_offset_x
        icon_y = rect.y + pixbuf_offset_y
        draw_pixbuf(cr, failed_pixbuf, icon_x, icon_y)
        
        text_y = icon_y + failed_pixbuf.get_height() + self.text_padding_y
        text_x = icon_x + self.text_padding_x
        
        _width, _height = get_content_size(self.prompt_text)
        
        self.text_rect = gtk.gdk.Rectangle(text_x - rect.x, text_y - rect.y,
                                           rect.x + rect.width -  text_x - pixbuf_offset_x,
                                           _height)
        
        if self.is_hover:        
            text_color = self.hover_text_dcolor.get_color()
        else:    
            text_color = self.normal_text_dcolor.get_color()
            
        draw_text(cr, self.prompt_text, text_x, text_y, self.text_rect.width, _height,
                  text_color=text_color, 
                  underline=True, 
                  alignment=pango.ALIGN_CENTER)
        return True
    
    def on_motion_notify(self, widget, event):
        if self.text_rect is not None:
            if is_in_rect((event.x, event.y), self.text_rect):
                self.is_hover = True
            else:    
                self.is_hover = False
            self.queue_draw()  
            
    def on_button_press(self, widget, event):        
        if self.is_hover:
            if self.press_callback:
                self.press_callback()
                self.is_hover = False
                self.queue_draw()
                
class NetworkConnectTimeout(gtk.EventBox):
    
    def __init__(self, callback=None):
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.ENTER_NOTIFY_MASK |
                        gtk.gdk.LEAVE_NOTIFY_MASK
                        )

        
        self.connect("expose-event", self.on_expose_event)
        
        if LANGUAGE == "zh_CN":
            prefix = "cn"
        elif LANGUAGE in ["zh_HK", "zh_TW"]:    
            prefix = "tw"
        else:    
            prefix = "en"
            
        self.failed_dpixbuf = get_common_image_pixbuf("network/timeout_%s.png" % prefix)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("button-press-event", self.on_button_press)
        
        self.normal_text_dcolor = app_theme.get_color("labelText")
        self.hover_text_dcolor = app_theme.get_color("globalItemHighlight")
        self.prompt_text = "点击此处刷新"
        self.text_padding_y = 5
        self.text_padding_x = 5
        self.text_rect = None
        self.is_hover = False
        self.press_callback = callback
        
    def on_expose_event(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        failed_pixbuf = self.failed_dpixbuf
        #draw_alpha_mask(cr, rect.x, rect.y, rect.width, rect.height, "layoutLeft")
        pixbuf_offset_x = (rect.width - failed_pixbuf.get_width()) / 2 
        pixbuf_offset_y = (rect.height - failed_pixbuf.get_height()) / 2 - 20
        icon_x = rect.x + pixbuf_offset_x
        icon_y = rect.y + pixbuf_offset_y
        draw_pixbuf(cr, failed_pixbuf, icon_x, icon_y)
        
        text_y = icon_y + failed_pixbuf.get_height() + self.text_padding_y
        text_x = icon_x + self.text_padding_x
        
        _width, _height = get_content_size(self.prompt_text)
        
        self.text_rect = gtk.gdk.Rectangle(text_x - rect.x, text_y - rect.y,
                                           rect.x + rect.width -  text_x - pixbuf_offset_x,
                                           _height)
        
        if self.is_hover:        
            text_color = self.hover_text_dcolor.get_color()
        else:    
            text_color = self.normal_text_dcolor.get_color()
            
        draw_text(cr, self.prompt_text, text_x, text_y, self.text_rect.width, _height,
                  text_color=text_color, 
                  underline=True, 
                  alignment=pango.ALIGN_CENTER)
        return True
    
    def on_motion_notify(self, widget, event):
        if self.text_rect is not None:
            if is_in_rect((event.x, event.y), self.text_rect):
                self.is_hover = True
            else:    
                self.is_hover = False
            self.queue_draw()  
            
    def on_button_press(self, widget, event):        
        if self.is_hover:
            if self.press_callback:
                self.press_callback()
                self.is_hover = False
                self.queue_draw()

