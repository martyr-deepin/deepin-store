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

import gtk
import gobject
import json
from skin import app_theme
from message_bar import MessageBar
from dtk.ui.draw import draw_text, draw_pixbuf, draw_vlinear
from dtk.ui.constant import DEFAULT_FONT_SIZE
from dtk.ui.utils import cairo_state, is_in_rect, get_content_size, container_remove_all
from constant import BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS
from dtk.ui.treeview import TreeView, TreeItem
#from dtk.ui.star_view import StarBuffer
from star_buffer import DscStarBuffer
from item_render import (render_pkg_icon, render_pkg_name, STAR_SIZE, get_star_level, get_icon_pixbuf_path,
                         ITEM_INFO_AREA_WIDTH, NAME_SIZE,
                         ITEM_STAR_AREA_WIDTH,
                         ITEM_BUTTON_AREA_WIDTH, ITEM_BUTTON_PADDING_RIGHT,
                         ITEM_HEIGHT,
                         ITEM_PADDING_X,
                         ITEM_PADDING_Y,
                         ITEM_PADDING_MIDDLE,
                         ICON_SIZE,
                         )
from events import global_event
from nls import _
from widgets import LoadingBox
import utils

def handle_dbus_error(*error):
    print "handle_dbus_error: ", error

LOAD_ITEMS_NUMBER = 20

class SearchPage(gtk.VBox):
    '''
    class docs
    '''

    def __init__(self, data_manager):
        '''
        init docs
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.data_manager = data_manager

        self.keywords = []
        self.all_pkg_names = []
        self.message_bar = MessageBar(18)

        self.content_box = gtk.VBox()

        self.treeview = TreeView(enable_drag_drop=False, expand_column=0)

        self.cute_message_image = gtk.VBox()
        self.cute_message_pixbuf = utils.get_common_locale_image_pixbuf("info", "noresult.png")
        self.cute_message_image.connect("expose-event", self.expose_cute_message_image)

        self.content_box.pack_start(self.message_bar, False, False)
        self.content_box.pack_start(self.treeview)

        self.loading_box = LoadingBox()

        self.pack_start(self.loading_box, True, True)

        self.treeview.connect("items-change", self.update_message_bar)
        self.treeview.draw_mask = self.draw_mask

    def expose_cute_message_image(self, widget, event):
        if self.cute_message_pixbuf:
            cr = widget.window.cairo_create()
            rect = widget.allocation

            cr.set_source_rgba(1, 1, 1, 0)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

            draw_pixbuf(
                cr,
                self.cute_message_pixbuf,
                rect.x + (rect.width - self.cute_message_pixbuf.get_width()) / 2,
                rect.y + (rect.height - self.cute_message_pixbuf.get_height()) / 2,
                )

    def update_message_bar(self, treeview):
        if len(treeview.visible_items) > 0:
            self.message_bar.set_message(
                    " ".join(self.keywords) + ": " +
                    _("%s applications searched") % len(self.all_pkg_names))
            container_remove_all(self)
            self.pack_start(self.content_box)
            global_event.emit("update-current-status-pkg-page", treeview)
        else:
            container_remove_all(self)
            self.pack_start(self.cute_message_image)

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
                     [(0, ("#FFFFFF", 0.9)),
                      (1, ("#FFFFFF", 0.9)),]
                     )

    def update(self, keywords):
        self.keywords = keywords
        self.treeview.delete_all_items()
        self.all_pkg_names = self.data_manager.search_query(keywords)

        if self.all_pkg_names:
            if len(self.all_pkg_names) > LOAD_ITEMS_NUMBER:
                self.load_new_items(self.all_pkg_names[:LOAD_ITEMS_NUMBER])
            else:
                self.load_new_items(self.all_pkg_names)
        else:
            self.update_message_bar(self.treeview)

        self.treeview.scrolled_window.connect('vscrollbar-state-changed', self.scrolled_window_vscrollbar_handler)

    def scrolled_window_vscrollbar_handler(self, widget, state):
        if state == "bottom":
            current_item_number = len(self.treeview.visible_items)
            all_pkgs_number = len(self.all_pkg_names)
            start = current_item_number
            if current_item_number < all_pkgs_number and (current_item_number+LOAD_ITEMS_NUMBER) < all_pkgs_number:
                end = current_item_number+LOAD_ITEMS_NUMBER
            elif current_item_number < all_pkgs_number and (current_item_number+LOAD_ITEMS_NUMBER) >= all_pkgs_number:
                end = all_pkgs_number
            else:
                return
            self.load_new_items(self.all_pkg_names[start:end])

    def load_new_items(self, pkg_names):
        if pkg_names:
            items = []
            for pkg_name in pkg_names:
                items.append(SearchItem(pkg_name, self.data_manager, self.keywords))
            self.treeview.add_items(items)
            #global_event.emit("show-pkg-view", self.page_box)
        else:
            self.update_message_bar(self.treeview)

gobject.type_register(SearchPage)

class SearchItem(TreeItem):
    '''
    class docs
    '''

    def __init__(self, pkg_name, data_manager, keywords):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        self.pkg_name = pkg_name
        self.data_manager = data_manager
        self.keywords = keywords
        self.icon_pixbuf = None

        (self.alias_name, self.short_desc, self.long_desc, star) = data_manager.get_pkg_search_info(self.pkg_name)
        info = self.data_manager.get_item_pkg_info(self.pkg_name)
        self.alias_name = info[1]
        self.short_desc = info[2]
        self.long_desc = info[3]

        self.star_level = get_star_level(5.0)
        self.star_buffer = DscStarBuffer(pkg_name)

        self.grade_star = 0

        self.highlight_string = get_match_context('\n'.join([self.short_desc, self.long_desc]), self.keywords)

        self.button_status = BUTTON_NORMAL

        ### TODO: is_installed status
        self.install_status = "uninstalled"
        self.desktops = []
        self.data_manager.get_pkg_installed(self.pkg_name, self.handle_pkg_status)

    def handle_pkg_status(self, status, success):
        if success:
            self.install_status= str(status)
            try:
                self.desktops = json.loads(self.install_status)
                self.desktops = self.data_manager.get_pkg_desktop_info(self.desktops)
            except:
                pass
            self.emit_redraw_request()
        else:
            utils.global_logger.logerror("%s: get_pkg_installed handle_dbus_error" % self.pkg_name)
            utils.global_logger.logerror(status)

    def render_info(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

        # Render icon.
        if self.icon_pixbuf == None:
            self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(
                    get_icon_pixbuf_path(utils.get_origin_name(self.pkg_name)))

        render_pkg_icon(cr, rect, self.icon_pixbuf)

        # Render name.
        render_pkg_name(cr, rect, get_match_context(self.alias_name, self.keywords), rect.width)

        # Render search result.
        with cairo_state(cr):
            text_padding_left = ITEM_PADDING_X + ICON_SIZE + ITEM_PADDING_MIDDLE
            text_padding_right = 10
            text_padding_y = ITEM_PADDING_Y + DEFAULT_FONT_SIZE * 2
            text_width = rect.width - text_padding_left - text_padding_right
            text_height = 30

            cr.rectangle(rect.x, rect.y + text_padding_y, rect.width, text_height)
            cr.clip()

            draw_text(
                cr,
                self.highlight_string,
                rect.x + text_padding_left,
                rect.y + text_padding_y,
                text_width,
                text_height,
                text_size=DEFAULT_FONT_SIZE,
                wrap_width=text_width,
                )

    def render_pkg_status(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

        # Render star.
        self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))

        # Draw button.
        name = ""
        draw_str = ""
        if self.install_status == "uninstalled":
            name = "button/install_small"
        elif self.install_status == "unknown":
            draw_str = _("Not found")
        else:
            if self.desktops:
                name = "button/start_small"
            else:
                draw_str = _("Installed")

        # Render button.

        if name:
            if self.button_status == BUTTON_NORMAL:
                status = "normal"
            elif self.button_status == BUTTON_HOVER:
                status = "hover"
            elif self.button_status == BUTTON_PRESS:
                status = "press"

            pixbuf = app_theme.get_pixbuf("%s_%s.png" % (name, status)).get_pixbuf()
            draw_pixbuf(
                cr,
                pixbuf,
                rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
                rect.y + (rect.height - pixbuf.get_height()) / 2
                )
        else:
            str_width, str_height = get_content_size(draw_str, 10)
            draw_text(
                cr,
                draw_str,
                rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - str_width,
                rect.y + (rect.height - str_height) / 2,
                rect.width,
                str_height,
                wrap_width=rect.width
                )

    def is_in_button_area(self, column, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (self.get_column_widths()[column] - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
                                (ITEM_HEIGHT - pixbuf.get_height()) / 2,
                                pixbuf.get_width(),
                                pixbuf.get_height()
                                )))

    def is_in_star_area(self, column, offset_x, offset_y):
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (0,
                                (ITEM_HEIGHT - STAR_SIZE) / 2,
                                ITEM_STAR_AREA_WIDTH,
                                STAR_SIZE)))

    def is_in_icon_area(self, column, offset_x, offset_y):
        return (column == 0
                and is_in_rect((offset_x, offset_y),
                               (ITEM_PADDING_X,
                                ITEM_PADDING_Y,
                                self.icon_pixbuf.get_width(),
                                self.icon_pixbuf.get_height()
                                )))

    def is_in_name_area(self, column, offset_x, offset_y):
        (name_width, name_height) = get_content_size(self.alias_name, NAME_SIZE)
        return (column == 0
                and is_in_rect((offset_x, offset_y),
                               (ITEM_PADDING_X + ICON_SIZE + ITEM_PADDING_MIDDLE,
                                ITEM_PADDING_Y,
                                name_width,
                                name_height,
                                )))

    def get_height(self):
        return ITEM_HEIGHT

    def get_column_widths(self):
        return [ITEM_INFO_AREA_WIDTH,
                ITEM_STAR_AREA_WIDTH + ITEM_BUTTON_AREA_WIDTH]

    def get_column_renders(self):
        return [self.render_info,
                self.render_pkg_status]

    def unselect(self):
        pass

    def select(self):
        pass

    def unhover(self, column, offset_x, offset_y):
        pass

    def hover(self, column, offset_x, offset_y):
        pass

    def motion_notify(self, column, offset_x, offset_y):
        if column == 0:
            if self.is_in_icon_area(column, offset_x, offset_y) or self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)
            else:
                global_event.emit("set-cursor", None)
        else:
            if self.is_in_star_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)

                times = offset_x / STAR_SIZE
                self.grade_star = times * 2 + 2

                self.grade_star = min(self.grade_star, 10)
                self.star_buffer.star_level = self.grade_star

                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
            else:
                if self.desktops:
                    if self.is_in_button_area(column, offset_x, offset_y):
                        self.button_status = BUTTON_HOVER

                        if self.redraw_request_callback:
                            self.redraw_request_callback(self, True)
                    else:
                        self.button_status = BUTTON_NORMAL

                        if self.redraw_request_callback:
                            self.redraw_request_callback(self, True)

                global_event.emit("set-cursor", None)

                if self.star_buffer.star_level != self.star_level:
                    self.star_buffer.star_level = self.star_level

                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)

    def get_offset_with_button(self, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        popup_x = self.get_column_widths()[1] - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width() / 2
        popup_y = (ITEM_HEIGHT - pixbuf.get_height()) / 2
        return (offset_x, offset_y, popup_x, popup_y)

    def button_press(self, column, offset_x, offset_y):
        if column == 0:
            if self.is_in_icon_area(column, offset_x, offset_y) or self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)
                global_event.emit("set-cursor", None)
        else:
            if self.is_in_star_area(column, offset_x, offset_y):
                global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
            elif self.is_in_button_area(column, offset_x, offset_y):
                if self.desktops:
                    global_event.emit("start-pkg", self.alias_name, self.desktops, self.get_offset_with_button(offset_x, offset_y))

                    self.button_status = BUTTON_PRESS
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self, True)
                else:
                    global_event.emit("install-pkg", [self.pkg_name])

                    self.button_status = BUTTON_PRESS
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self, True)
            else:
                global_event.emit("switch-to-detail-page", self.pkg_name)

    def button_release(self, column, offset_x, offset_y):
        if self.desktops:
            if self.is_in_button_area(column, offset_x, offset_y):
                if self.button_status != BUTTON_HOVER:
                    self.button_status = BUTTON_HOVER

                    if self.redraw_request_callback:
                        self.redraw_request_callback(self, True)
            else:
                if self.button_status != BUTTON_NORMAL:
                    self.button_status = BUTTON_NORMAL

                    if self.redraw_request_callback:
                        self.redraw_request_callback(self, True)

    def single_click(self, column, offset_x, offset_y):
        pass

    def double_click(self, column, offset_x, offset_y):
        pass

    def release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> if self.pixbuf:
        >>>     del self.pixbuf
        >>>     self.pixbuf = None
        >>>
        >>> return True

        This is TreeView interface, you should implement it.

        @return: Return True if do release work, otherwise return False.

        When this function return True, TreeView will call function gc.collect() to release object to release memory.
        '''
        if self.icon_pixbuf:
            del self.icon_pixbuf
            self.icon_pixbuf = None

        return True

gobject.type_register(SearchItem)

import re

def highlight_keyword(match):
    COLOR_PRE_STRING = "<span foreground=\"#00AAFF\">"
    COLOR_POST_STRING = "</span>"
    return "%s%s%s" % (COLOR_PRE_STRING, match.string[match.start():match.end()], COLOR_POST_STRING)

def get_match_context(content, keywords):
    OMIT_STRING = "..."

    regex_string = ("(%s)" % ('|'.join(keywords))).encode("string-escape")

    regex = re.compile(regex_string, re.I)

    # Need encode utf8 before regex search, otherwise GTK+'s unicode string can't work.
    lines = content.encode("utf8").split("\n")

    match_lines = []
    found_keyword = False
    for (line_index, line) in enumerate(lines):
        matches = map(lambda m: m, regex.finditer(line))
        if len(matches) >= 1:
            found_keyword = True
            match_lines.append(re.sub(regex, highlight_keyword, line))
        else:
            if len(match_lines) == 0 or match_lines[-1] != OMIT_STRING:
                match_lines.append(OMIT_STRING)

    if found_keyword:
        return ' '.join(match_lines)
    else:
        return content

if __name__ == "__main__":
    test = '''
一个简单而功能强大的音乐播放器
 Bluemindo 是一个相当简单但功能强大的音乐播放器，用 Python/PyGTK 编写，使用 GStreamer 作为解码器。
 .
 With Bluemindo you can:
  * automatically download lyrics, album-covers, or a picture of the
    artist, for the current playing song;
  * choose between five different view modes (lightweight, basic,
    normal, full or albums);
  * use plugins;
  * get desktop notifications (requires python-notify);
  * update Gajim's status message (requires python-dbus);
  * send music to your Jabber account (requires python-xmpp) or to
    your Last.fm profile.
  * listen to webradios and ShoutCast
'''

    print get_match_context(test, ["Python", "播放器"])
