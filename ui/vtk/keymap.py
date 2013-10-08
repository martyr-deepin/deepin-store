#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Deepin, Inc.
#               2013 Hailong Qiu
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

import gtk


class Key:
    #
    shift_m   = gtk.gdk.SHIFT_MASK   # Shift
    lock_m    = gtk.gdk.LOCK_MASK    # Caps lock
    ctrl_m    = gtk.gdk.CONTROL_MASK # Ctrl
    super_m   = gtk.gdk.SUPER_MASK   #
    alt_m     = gtk.gdk.MOD1_MASK
    hyper_m   = gtk.gdk.HYPER_MASK
    is_lower    = gtk.gdk.keyval_is_lower # 小写.
    is_upper    = gtk.gdk.keyval_is_upper # 大写.
    k_2_upper   = gtk.gdk.keyval_to_upper # keyval 转大写
    k_2_lower   = gtk.gdk.keyval_to_lower # keyval 转小写
    k_2_unicode = gtk.gdk.keyval_to_unicode
    u_2_keyval  = gtk.gdk.unicode_to_keyval
    name        = gtk.gdk.keyval_name # 获取按键名 : 比如按下 右边的Ctrl,那就是 Control_R
    # 
    gtk.gdk.MOD2_MASK
    gtk.gdk.MOD3_MASK
    gtk.gdk.MOD4_MASK
    gtk.gdk.MOD5_MASK
    gtk.gdk.BUTTON1_MASK
    gtk.gdk.BUTTON2_MASK
    gtk.gdk.BUTTON3_MASK
    gtk.gdk.BUTTON4_MASK
    gtk.gdk.BUTTON5_MASK
    gtk.gdk.META_MASK
    gtk.gdk.RELEASE_MASK
    gtk.gdk.MODIFIER_MASK
    #
    gtk.gdk.keyval_convert_case
    gtk.gdk.keyval_from_name
    gtk.gdk.keymap_get_for_display
    gtk.gdk.keymap_get_default
    

def get_key_event_modifiers(key_event):
    modifiers = []
    if key_event.state & Key.ctrl_m:
        modifiers.append("Ctrl")
    if key_event.state & Key.super_m:
        modifiers.append("Super")
    if key_event.state & Key.hyper_m:
        modifiers.append("Hyper")
    if key_event.state & Key.alt_m:
        modifiers.append("Alt")
    '''
    !!!
    当按下-->>>
    Ctrl + Alt + Shift + Z
    这种是正确的行为.
    当按下Caps Lock的时候.
    Ctrl + Alt + Z
    如果此时按下了 shift, 那么:
    Ctrl + Alt + z (z就成了小写的),
    lock 和 shift 互相抵消了. (lock按下大写, shift按下变成小写, 两个等于没有按)
    '''
    if (key_event.state & Key.shift_m and 
        (len(get_key_name(key_event.keyval)) != 1 or Key.is_upper(key_event.keyval))):
        modifiers.append("Shift")
    return modifiers


def get_keyevent_name(key_event, to_upper=False):
    # 判断如果按下的是 modifier 键,如果都是直接返回空字符串
    if key_event.is_modifier: 
        return ""
    else: # 不是modifier.
        # 获取当前的状态.
        key_modifiers = get_key_event_modifiers(key_event)
        # 获取按键名.
        key_name      = get_key_name(key_event.keyval, to_upper)
        if " " == key_name:
            key_name = "Space"
        if [] == key_modifiers: 
            return key_name
        else:
            return " + ".join(key_modifiers) + " + " + key_name

def get_key_name(keyval, to_upper=False):
    if to_upper:
        key_unicode = Key.k_2_unicode(Key.k_2_upper(keyval))
    else: # 将keyval转换成unicode.
        key_unicode = Key.k_2_unicode(keyval)

    if key_unicode == 0: # 判断是否按下了是字母.
        return Key.name(keyval)
    else:
        return str(unichr(key_unicode))
        
def ctrl_mask_check(event):
    return get_key_name(event.keyval) in ["Control_L", "Control_R"]

def shift_mask_check(event):
    return get_key_name(event.keyval) in ["Shift_L", "Shift_R"]



if __name__ == "__main__":
    def key_test_functino(w, e):
        keyval = e.keyval
        state  = e.state
        #
        print get_keyevent_name(e, False)

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_size_request(500, 500)
    win.add_events(gtk.gdk.ALL_EVENTS_MASK)
    win.connect("key-press-event", key_test_functino)
    btn = gtk.Button("a")
    win.add(btn)
    win.show_all()
    gtk.main()

