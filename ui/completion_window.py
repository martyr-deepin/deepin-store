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
from events import global_event
import gtk
import gobject
from dtk.ui.treeview import TreeView, TreeItem
from dtk.ui.constant import DEFAULT_FONT_SIZE
from dtk.ui.utils import (get_widget_root_coordinate, WIDGET_POS_BOTTOM_LEFT, cairo_disable_antialias, 
                          alpha_color_hex_to_cairo, get_content_size)
from dtk.ui.draw import draw_text, draw_vlinear
from dtk.ui.theme import ui_theme
from dtk.ui.popup_grab_window import PopupGrabWindow, wrap_grab_window
from dtk.ui.window import Window
from dtk.ui.entry import InputEntry
from dtk.ui.button import ImageButton

class CompletionWindow(Window):
    '''
    class docs
    '''
	
    def __init__(self, window_width, window_height):
        '''
        init docs
        '''
        # Init.
        Window.__init__(
            self,
            # shadow_visible=False,
            shape_frame_function=self.shape_completion_window_frame,
            expose_frame_function=self.expose_completion_window_frame)
        self.window_width = window_width
        self.window_height = window_height
        self.window_offset_x = 8
        self.window_offset_y = 34
        self.align_size = 2
        
        self.treeview = TreeView(
            [],
            enable_highlight=False,
            enable_multiple_select=False,
            enable_drag_drop=False,
            expand_column=0,
            )
        self.treeview.scrolled_window.tag_by_popup_grab_window = True
        self.treeview_align = gtk.Alignment()
        self.treeview_align.set(0.5, 0.5, 1, 1)
        self.treeview_align.set_padding(self.align_size, self.align_size, self.align_size, self.align_size)
        self.treeview_align.add(self.treeview)
        self.treeview.connect("press-return", self.treeview_press_return)
        self.treeview.draw_mask = self.draw_mask
        
        self.window_frame.pack_start(self.treeview_align, True, True)
        
        self.connect("realize", self.realize_completion_window)
        
        self.get_scrolledwindow = self.get_scrolledwindow
        
        wrap_grab_window(completion_grab_window, self)
        
        completion_grab_window.connect("input-method-focus-in", self.input_method_focus_in)
        completion_grab_window.connect("input-method-commit", self.input_method_commit)
        
        self.keymap = {
            "Home" : self.treeview.select_first_item,
            "End" : self.treeview.select_last_item,
            "Page_Up" : self.treeview.scroll_page_up,
            "Page_Down" : self.treeview.scroll_page_down,
            "Up" : self.treeview.select_prev_item,
            "Down" : self.treeview.select_next_item,
            }
        
    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h,
                     [(0, ("#ffffff", 0.9)),
                      (1, ("#ffffff", 0.9)),]
                     )
        
    def treeview_press_return(self, treeview, select_items):
        if len(select_items) > 0:
            completion_grab_window.popup_grab_window_focus_out()
            global_event.emit("switch-to-detail-page", select_items[0].text)
        
    def set_input_method_cursor(self):
        entry_buffer = search_entry.entry.entry_buffer
        cursor_pos = entry_buffer.get_cursor_pos(entry_buffer.get_insert_index())[0]
        (entry_x, entry_y) = search_entry.translate_coordinates(search_entry.get_toplevel(), 0, 0)
        (window_x, window_y) = search_entry.get_toplevel().window.get_origin()
        
        completion_grab_window.im.set_cursor_location(
            gtk.gdk.Rectangle(
                window_x + entry_x + cursor_pos[0],
                window_y + entry_y + cursor_pos[1],
                1,
                cursor_pos[3]))
        
    def input_method_focus_in(self, grab_window, im):
        self.set_input_method_cursor()
        
    def input_method_commit(self, grab_window, im, input_text):
        self.set_input_method_cursor()
        search_entry.set_text("%s%s" % (search_entry.get_text(), input_text))
        
    def get_scrolledwindow(self):
        return self.treeview.scrolled_window
        
    def shape_completion_window_frame(self, widget, event):
        pass
        
    def expose_completion_window_frame(self, widget, event):
        cr = widget.window.cairo_create()        
        rect = widget.allocation

        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("window_frame_outside_3").get_color_info()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("window_frame_inside_2").get_color_info()))
            cr.rectangle(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2)
            cr.fill()
            
    def show(self, search_string, pkg_names):
        search_entry.entry.entry_buffer.grab_focus_flag = True
        
        self.treeview.delete_all_items()
        self.treeview.add_items(map(lambda pkg_name: TextItem(pkg_name, search_string), pkg_names))
        self.treeview.draw_area.grab_focus()
        
        (x, y) = get_widget_root_coordinate(search_entry, WIDGET_POS_BOTTOM_LEFT, False)
        self.move(x + self.window_offset_x, y + self.window_offset_y)
        self.show_all()
        
    def realize_completion_window(self, widget):
        self.set_default_size(self.window_width, self.window_height)
        self.set_geometry_hints(
            None,
            self.window_width,       # minimum width
            self.window_height,       # minimum height
            self.window_width,
            self.window_height,
            -1, -1, -1, -1, -1, -1
            )
        
gobject.type_register(CompletionWindow)        

class CompletionGrabWindow(PopupGrabWindow):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        PopupGrabWindow.__init__(self, CompletionWindow, handle_input_method=True)

    def popup_grab_window_key_press(self, widget, event):
        if event and event.window:
            for popup_window in self.popup_windows:
                popup_window.event(event)
                
            if len(completion_window.treeview.select_rows) <= 0:
                search_entry.entry.event(event)    
            
    def popup_grab_window_key_release(self, widget, event):
        if event and event.window:
            for popup_window in self.popup_windows:
                popup_window.event(event)
            
            search_entry.entry.event(event)    
        
class TextItem(TreeItem):
    '''
    class docs
    '''
	
    def __init__(self, 
                 text, 
                 search_string,
                 text_size = DEFAULT_FONT_SIZE,
                 padding_x = 10,
                 padding_y = 6):
        '''
        init docs
        '''
        # Init.
        TreeItem.__init__(self)
        self.text = text
        self.search_string = search_string
        self.text_size = text_size
        self.padding_x = padding_x
        self.padding_y = padding_y
        (self.text_width, self.text_height) = get_content_size(self.text)
        
    def render_text(self, cr, rect):
        if self.is_hover or self.is_select:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("menu_item_select").get_color_info())
        
            # Set font color.
            font_color = ui_theme.get_color("menu_select_font").get_color()
            
            # Don't highlight when select.
            text = self.text
        else:
            # Set font color.
            font_color = ui_theme.get_color("menu_font").get_color()
            
            # Highilght match string.
            r = self.text.partition(self.search_string.lower())
            text = "%s<span foreground=\"#00AAFF\">%s</span>%s" % (r[0], r[1], r[2])
            
        draw_text(cr, 
                  text,
                  rect.x + self.padding_x, 
                  rect.y,
                  rect.width - self.padding_x * 2, 
                  rect.height,
                  text_color=font_color)
        
    def get_width(self):
        return self.text_width + self.padding_x * 2
        
    def get_height(self):
        return self.text_size + self.padding_y * 2
    
    def get_column_widths(self):
        return [-1]
    
    def get_column_renders(self):
        return [self.render_text]

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def unselect(self):
        self.is_select = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def select(self):
        self.is_select = True
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def button_press(self, column, offset_x, offset_y):
        global_event.emit("switch-to-detail-page", self.text)
    
gobject.type_register(TextItem)

search_entry = InputEntry(
    action_button=ImageButton(app_theme.get_pixbuf("entry/search_normal.png"),
                              app_theme.get_pixbuf("entry/search_hover.png"),
                              app_theme.get_pixbuf("entry/search_press.png"),))
search_entry.set_size(140, 24)

completion_grab_window = CompletionGrabWindow()
completion_window = CompletionWindow(300, 200)
