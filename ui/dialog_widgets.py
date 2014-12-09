#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011~2013 Deepin, Inc.
#               2011~2013 Kaisheng Ye
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

import math
import gtk

import utils
from nls import _
from events import global_event

from dtk.ui.dialog import DialogBox
from dtk.ui.label import Label
from dtk.ui.utils import container_remove_all
from dtk.ui.button import Button
from dtk.ui.draw import draw_pixbuf

class WaitingDialog(DialogBox):
    def __init__(self, hide_callback=None):
        self.hide_callback = hide_callback
        self.dialog_width = 330
        DialogBox.__init__(
                self,
                title="",
                default_width=self.dialog_width,
                default_height=145,
                mask_type=0,
                close_callback=self.close_action,
                modal=True,
                window_hint=gtk.gdk.WINDOW_TYPE_HINT_DIALOG,
                window_pos=None,
                skip_taskbar_hint=True,
                resizable=False,
                window_type=gtk.WINDOW_TOPLEVEL,
                )

        self.waiting_animation = gtk.VBox()
        self.waiting_animation.set_size_request(36, 36)
        self.waiting_bg_pixbuf = utils.get_common_image_pixbuf("waiting/waiting_bg.png")
        self.waiting_fg_pixbuf = utils.get_common_image_pixbuf("waiting/waiting_fg.png")
        self.waiting_animation.connect("expose-event", self.expose_waiting)
        self.counter = 1
        self.factor = math.pi/10
        gtk.timeout_add(50, self.on_timer)

        self.label = Label(
            _("Speed testing will finish only after one minute, please wait."),
            text_size=10,
            wrap_width=self.dialog_width- 36 - 60,
            )

        self.waiting_hbox = gtk.HBox()
        self.waiting_hbox.pack_start(self.waiting_animation, False, False)
        self.waiting_hbox.pack_start(self.label, False, False)

        self.center_align = gtk.Alignment()
        self.center_align.set(0.5, 0.5, 0, 0)
        self.center_align.set_padding(0, 0, 8, 8)
        self.body_box.add(self.center_align)

        global_event.register_event("mirror-test-finished", self.show_result)

    def show_waiting(self):
        container_remove_all(self.right_button_box.button_box)
        container_remove_all(self.center_align)
        self.center_align.add(self.waiting_hbox)
        self.show_all()

    def show_result(self, mirror):
        container_remove_all(self.center_align)
        message = Label(
                _('Test is completed, the fastest mirror source is "%s", switch now?') % mirror.name,
                text_size=10,
                wrap_width=self.dialog_width - 100,
                )
        self.center_align.add(message)

        self.confirm_button = Button(_("OK"))
        self.confirm_button.connect("clicked", self.confirm_button_callback, mirror)
        self.cancel_button = Button(_("Cancel"))
        self.cancel_button.connect("clicked", self.cancel_button_callback)

        self.right_button_box.set_buttons([self.confirm_button, self.cancel_button])

        self.show_all()

    def cancel_button_callback(self, widget):
        self.hide_all()
        if self.hide_callback:
            self.hide_callback()
            self.hide_callback = None

    def confirm_button_callback(self, w, mirror):
        global_event.emit("start-change-mirror", mirror)
        self.hide_all()
        if self.hide_callback:
            self.hide_callback()
            self.hide_callback = None

    def close_action(self):
        global_event.emit("cancel-mirror-test")
        self.hide_all()
        if self.hide_callback:
            self.hide_callback()
            self.hide_callback = None

    def on_timer(self):
        if self.counter < 2 * math.pi/self.factor:
            self.counter += 1
        else:
            self.counter = 1
        self.waiting_animation.queue_draw()
        return True

    def expose_waiting(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        cr.translate(rect.x, rect.y)
        draw_pixbuf(cr, self.waiting_bg_pixbuf)
        cr.translate(rect.width/2, rect.height/2)
        cr.rotate(self.counter * self.factor)
        draw_pixbuf(cr, self.waiting_fg_pixbuf, -rect.width/2, -rect.height/2)

