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

import apt
import apt_pkg

class AptCache(object):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        apt_pkg.init()
        self.cache = apt.Cache()
    
    def get_upgrade_pkgs(self):
        pkg_infos = []
        
        for pkg in self.cache:
            if pkg.is_upgradable:
                pkg_version = pkg.versions[0].version
                pkg_infos.append(str((pkg.name, pkg_version)))
        
        # # JUST FOR DEBUG.
        # for pkg_name in ["deepin-music-player", "deepin-media-player", "deepin-screenshot"]:
        #     pkg_infos.append(str((pkg_name, self.cache[pkg_name].versions[0].version)))
                
        return pkg_infos

    def get_uninstall_pkgs(self):
        pkg_infos = []
        for pkg in self.cache:
            if pkg.is_installed:
                pkg_version = pkg.installed.version
                pkg_infos.append(str((pkg.name, pkg_version)))
                
        return pkg_infos
    
    def get_pkgs_install_version(self, pkg_names):
        return map(lambda pkg_name: self.cache[pkg_name].versions[0].version, pkg_names)

    def get_pkgs_uninstall_version(self, pkg_names):
        pkg_infos = []
        for pkg_name in pkg_names:
            pkg = self.cache[pkg_name]
            if pkg.is_installed:
                pkg_version = pkg.installed.version
            # This just happended when simulate test.
            else:
                pkg_version = pkg.versions[0].version
                
            pkg_infos.append(pkg_version)
                
        return pkg_infos
    
    def get_pkg_short_desc(self, pkg_name):
        return self.cache[pkg_name].candidate.summary.encode("utf-8", "ignore")
    
    def is_pkg_installed(self, pkg_name):
        try:
            pkg = self.cache[pkg_name]
            return pkg.is_installed
        except Exception:
            return False

if __name__ == "__main__":
    pkg_cache = AptCache()
    
    import Queue as Q
    block_signal = Q.Queue()
    if block_signal.get():
        print "finish"
