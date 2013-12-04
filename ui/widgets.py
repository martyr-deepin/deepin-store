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
import time
from datetime import datetime

from utils import get_common_image, get_common_image_pixbuf, get_common_locale_image_pixbuf
from ui_utils import set_widget_vcenter
from constant import LANGUAGE
from skin import app_theme
from nls import _

from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.label import Label
from dtk.ui.button import CloseButton, Button
from dtk.ui.utils import color_hex_to_cairo, set_clickable_cursor
from dtk.ui.theme import ui_theme
from dtk.ui.constant import ALIGN_MIDDLE
from dtk.ui.dialog import DialogBox, DIALOG_MASK_SINGLE_PAGE
import dtk.ui.utils as dutils

class ActionLabel(Label):
    def __init__(self):
        pass

class HumanTimeTip(gtk.VBox):
    def __init__(self, timestamp):
        gtk.VBox.__init__(self)
        self.timestamp = timestamp
        self.label = Label()
        self.pack_start(self.label, False, False)

        try:
            timestamp = float(self.timestamp)
            self.label.set_text(self.to_huamn_str(timestamp))
        except:
            self.label.set_text(self.timestamp)

        gtk.timeout_add(1000, self.tick)

    def to_huamn_str(self, timestamp):
        now = time.time()
        interval = int(now - timestamp)
        if interval < 60:
            return _("Just now")
        else:
            mins = interval / 60
            if mins < 60:
                if mins == 1:
                    return _("One minute ago")
                else:
                    return _("%s minutes ago") % mins
            else:
                hours = mins / 60
                if hours < 24:
                    if hours == 1:
                        return _("One hour ago")
                    else:
                        return _("%s hours ago") % hours
                else:
                    days = hours / 24
                    if days == 1:
                        return _("Yesterday")
                    else:
                        datetime_obj = datetime.fromtimestamp(timestamp)
                        return datetime_obj.strftime("%Y-%m-%d")

    def tick(self):
        try:
            timestamp = float(self.timestamp)
            self.label.set_text(self.to_huamn_str(timestamp))
        except:
            pass
        return True

class TextLoading(gtk.VBox):
    """A text with dot end loading widget"""

    total_dot_number = 4

    def __init__(self, text, text_size=10, text_color="#003399"):
        gtk.VBox.__init__(self)
        self.text = text
        self.draw_text = self.text
        self.text_size = text_size
        self.text_color = text_color
        size = dutils.get_content_size(self.text + "." * self.total_dot_number, text_size)
        self.set_size_request(*size)
        self.dot_number = 0

        self.connect("expose-event", self.on_expose_event)

        gtk.timeout_add(600, self.loading_loop)

    def change_text(self, text):
        self.text = text
        self.draw_text = text
        size = dutils.get_content_size(self.text + "." * self.total_dot_number, self.text_size)
        self.set_size_request(*size)
        self.dot_number = 0
        self.queue_draw()

    def loading_loop(self):
        if self.dot_number == self.total_dot_number:
            self.dot_number = 0
        else:
            self.dot_number += 1
        self.draw_text = self.text + "." * self.dot_number
        self.queue_draw()
        return True

    def on_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.get_allocation()
        draw_text(cr, 
                self.draw_text, 
                rect.x, 
                rect.y, 
                rect.width, 
                rect.height, 
                text_color=self.text_color,
                text_size=self.text_size,
                )
        return True

class ImageBox(gtk.VBox):
    def __init__(self, img_path, width=None, height=None):
        gtk.VBox.__init__(self)

        self.img_path = img_path
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(self.img_path)
        
        if not width:
            width = self.pixbuf.get_width()
        if not height:
            height = self.pixbuf.get_height()

        self.set_size_request(width, height)
        self.connect("expose-event", self.on_expose_event)

    def change_image(self, img_path):
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(img_path)
        self.queue_draw()

    def on_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.get_allocation()
        draw_pixbuf(cr,
                    self.pixbuf,
                    rect.x,
                    rect.y,
                    )    
        return True

class ActionButton(Label):
    def __init__(self, 
                 text, 
                 callback_action=None,
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
        self.callback_action = callback_action

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
        self.end_info_label = Label("")
        self.info_callback_button = ActionButton('')

        self.close_button = CloseButton()

        self.pack_start(self.info_image_box, False, False)
        self.pack_start(self.info_label)

        self.pack_end(self.close_button, False, False)
        self.pack_end(self.info_callback_button, False, False)
        self.pack_end(self.end_info_label, False, False)

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

    def update_end_info(self, info):
        self.end_info_label.set_text(info)

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

        self.failed_dpixbuf = get_common_locale_image_pixbuf("network", "failed.png")
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("button-press-event", self.on_button_press)
        
        self.normal_text_dcolor = app_theme.get_color("labelText")
        self.hover_text_dcolor = app_theme.get_color("globalItemHighlight")
        self.prompt_text = _("Click to refresh")
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
        
        _width, _height = dutils.get_content_size(self.prompt_text)
        
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
            if dutils.is_in_rect((event.x, event.y), self.text_rect):
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
        
        self.failed_dpixbuf = get_common_locale_image_pixbuf("network", "timeout.png")
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("button-press-event", self.on_button_press)
        
        self.normal_text_dcolor = app_theme.get_color("labelText")
        self.hover_text_dcolor = app_theme.get_color("globalItemHighlight")
        self.prompt_text = _("Click to refresh")
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
        
        _width, _height = dutils.get_content_size(self.prompt_text)
        
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
            if dutils.is_in_rect((event.x, event.y), self.text_rect):
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

class ConfirmDialog(DialogBox):
    '''
    Simple message confirm dialog.
    
    @undocumented: click_confirm_button
    @undocumented: click_cancel_button
    '''
	
    def __init__(self, 
                 title, 
                 message, 
                 default_width=330,
                 default_height=145,
                 confirm_callback=None, 
                 cancel_callback=None, 
                 cancel_first=True, 
                 message_text_size=9,
                 ):
        '''
        Initialize ConfirmDialog class.
        
        @param title: Title for confirm dialog.
        @param message: Confirm message.
        @param default_width: Dialog width, default is 330 pixel.
        @param default_height: Dialog height, default is 145 pixel.
        @param confirm_callback: Callback when user click confirm button.
        @param cancel_callback: Callback when user click cancel button.
        @param cancel_first: Set as True if to make cancel button before confirm button, default is True.
        @param message_text_size: Text size of message, default is 11.
        '''
        # Init.
        DialogBox.__init__(self, title, default_width, default_height, DIALOG_MASK_SINGLE_PAGE, close_callback=self.hide)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.label_align = gtk.Alignment()
        self.label_align.set(0.5, 0.5, 0, 0)
        self.label_align.set_padding(0, 0, 8, 8)
        self.label = Label(message, text_x_align=ALIGN_MIDDLE, text_size=message_text_size)
        
        self.confirm_button = Button(_("OK"))
        self.cancel_button = Button(_("Cancel"))
        
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        
        # Connect widgets.
        self.body_box.pack_start(self.label_align, True, True)
        self.label_align.add(self.label)
        
        if cancel_first:
            self.right_button_box.set_buttons([self.cancel_button, self.confirm_button])
        else:
            self.right_button_box.set_buttons([self.confirm_button, self.cancel_button])
        
    def click_confirm_button(self):
        '''
        Internal function to handle click confirm button.
        '''
        if self.confirm_callback != None:
            self.confirm_callback()        
        
        self.hide()
        
    def click_cancel_button(self):
        '''
        Internal function to handle click cancel button.
        '''
        if self.cancel_callback != None:
            self.cancel_callback()
        
        self.hide()

