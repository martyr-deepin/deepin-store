#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
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


import gobject    
import os


class Config(gobject.GObject):
    __gsignals__ = {
        "config-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING))
        }

    def __init__(self, ini_path):
        gobject.GObject.__init__(self)
        self.ini_path = ini_path
        self.section_bool = False
        self.argv_bool = False        
        self.section_dict = {}
        self.argv_save_ch = ""
        self.section_save_ch = ""
        
        # init function.
        try:
            self.fp = open(ini_path, "r")
            self.init_config()                                            
        except Exception, e:    
            print "%s" % (e)
        
        
            
    def init_config(self):        
        
        while True:
            ch = self.fp.read(1)
            
            if not ch: # Read over.
                break
            
            if self.section_bool:
                if "[" == ch:
                    self.fp.seek(-2, 1)
                    token_enter_bool = self.fp.read(1)
                    ch = self.fp.read(1)
                    if ("\n" == token_enter_bool) and ("[" == ch):
                        self.section_save_ch = ""
                        self.section_bool = False
                        self.fp.seek(-1, 1)
                    else:    
                        self.argv_save_ch += ch
                        
                else:# Read argv.        
                    if "\n" == ch:
                        self.split(self.argv_save_ch, "=")
                        self.argv_save_ch = ""
                    else:    
                        self.argv_save_ch += ch
                    
            else:        
                if "[" == ch:                
                    while True:                    
                        ch = self.fp.read(1)                    
                    
                        if "\n" == ch:
                            self.section_dict[self.section_save_ch] = {} # save section name.
                            break
                    
                        if "]" == ch:
                            self.section_bool = True                       
                        else:
                            if ch != "[":
                                self.section_save_ch += ch
                            
    def split(self, string, token):        
        temp_save_num = []
        temp_num = 0
        # scan token.
        for ch in string:
            if ch == token and (" " == string[temp_num-1]):
                temp_save_num.append(temp_num)       
            temp_num += 1
        if temp_save_num:
            argv_name = string[0:temp_save_num[0]].strip()
            argv_value = string[temp_save_num[0]+1:].strip()
            self.section_dict[self.section_save_ch][argv_name] = argv_value
            
    def set(self, section, argv, value):
        section = str(section)
        argv    = str(argv)
        value   = str(value)
        
        if not self.section_dict.has_key(section):
            self.section_dict[section] = {argv:str(value)}
        else:    
            if not self.section_dict[section].has_key(argv):
                self.section_dict[section][argv] = str(value)
            else:    
                self.section_dict[section][argv] = str(value)
                
        self.emit("config-changed", section, argv, value)         
                
    def get(self, section, argv):
        section = str(section)
        argv    = str(argv)
        
        if self.section_dict.has_key(section):
            if self.section_dict[section].has_key(argv):                
                return self.section_dict[section][argv] 
            
    def get_argvs(self, section):    
        section = str(section)
        
        if self.section_dict.has_key(section):
            return self.section_dict[section]
        
    def get_argv_bool(self, section, argv):    
        section = str(section)
        argv    = str(argv)
        if self.section_dict.has_key(section):
            if self.section_dict[section].has_key(argv):
                return True
        return None    
    
    def modify_argv(self, section, argv, new_argv, new_value):
        section = str(section)
        argv    = str(argv)
        
        if self.section_dict.has_key(section):
            if self.section_dict[section].has_key(argv):
                del self.section_dict[section][argv]
                self.section_dict[section][new_argv] = new_value
                return True
        return None    
    
    def save(self):
        fp = open(self.ini_path, "w")
        for section_key in self.section_dict.keys():
            section_string = "[%s]" % (section_key)
            fp.write(section_string + "\n") # Save section.
            for argv_key in self.section_dict[section_key]:                
                argv_string = "%s = %s" % (argv_key, self.section_dict[section_key][argv_key])
                fp.write(argv_string + "\n") # Save argv.                     


