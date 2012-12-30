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

import os
import sys
import errno
import hashlib
import traceback
import apt_pkg
import apt
from constant import DOWNLOAD_STATUS_NOTNEED, DOWNLOAD_STATUS_ERROR
import apt.debfile as debfile

def get_deb_download_info(cache, deb_file):
    try:
        deb_package = debfile.DebPackage(deb_file, cache)
        
        if not deb_package.check():
            print "package has installed"
            return DOWNLOAD_STATUS_ERROR
        elif not deb_package.check_breaks_existing_packages():
            print "install package will break existing package"
            return DOWNLOAD_STATUS_ERROR
        elif not deb_package.check_conflicts():
            print "package conflicts with existing packages"
            return DOWNLOAD_STATUS_ERROR
        else:
            depend_packages = []
            depend_ok = True
            for depend in deb_package.depends:
                for (pkg_name, require_version, version_operator) in depend:
                    for pkg_version in cache[pkg_name].versions:
                        if apt_pkg.check_dep(pkg_version.version, version_operator, require_version):
                            depend_packages.append(pkg_name)
                        else:
                            depend_ok = False
                            print "Check depend %s failed" % (pkg_name)
                            return DOWNLOAD_STATUS_ERROR
        
            if depend_ok:        
                (install_packages, remove_packages, unauthenticated_packages) = deb_package.required_changes
                
                for pkg_name in depend_packages + install_packages:
                    pkg = cache[pkg_name]
                    if not pkg.installed:
                        pkg.mark_install()
                    
                for pkg_name in remove_packages:
                    pkg = cache[pkg_name]
                    if pkg.installed:
                        pkg.mark_uninstall()
                    
                # Get package information.
                pkgs = sorted(cache.get_changes(), key=lambda pkg: pkg.name)
                return check_pkg_download_info(pkgs)
    except Exception, e:
        print "get_deb_download_info error: %s" % (e)
        traceback.print_exc(file=sys.stdout)
        
        return DOWNLOAD_STATUS_ERROR

def get_pkg_download_info(cache, pkg_name):
    # Mark package in apt cache.
    if pkg_name in cache:
        try:
            pkg = cache[pkg_name]
            if not pkg.installed:
                pkg.mark_install()
            elif pkg.is_upgradable:
                pkg.mark_upgrade()
                
            # Get package information.
            pkgs = sorted(cache.get_changes(), key=lambda pkg: pkg.name)
            return check_pkg_download_info(pkgs)
        
        except Exception, e:
            print "get_pkg_download_info error: %s" % (e)
            traceback.print_exc(file=sys.stdout)
            
            return DOWNLOAD_STATUS_ERROR
    else:
        raise Exception("%s is not found" % pkg_name)
    
def check_pkg_download_info(pkgs):
    if len(pkgs) >= 1:
        pkgs = [pkg for pkg in pkgs if not pkg.marked_delete and not pkg_file_has_exist(pkg)]
        
        if len(pkgs) == 0:
            return DOWNLOAD_STATUS_NOTNEED
        else:
            try:
                urls = []
                hash_infos = []
                pkg_sizes = []
                
                for pkg in pkgs:
                    version = pkg.candidate
                    hashtype, hashvalue = get_hash(version)
                    pkg_uris = version.uris
                    pkg_size = int(version.size)
                    
                    urls.append(pkg_uris[0])
                    hash_infos.append((hashtype, hashvalue))
                    pkg_sizes.append(pkg_size)
                    
                return (urls, hash_infos, pkg_sizes)
            except Exception, e:
                print "get_pkg_download_info error: %s" % (e)
                traceback.print_exc(file=sys.stdout)
                
                return DOWNLOAD_STATUS_ERROR
    else:
        return DOWNLOAD_STATUS_NOTNEED
    
ARCHIVE_DIR = apt_pkg.config.find_dir("Dir::Cache::Archives")    
DEB_CACHE_DIR = os.path.join(ARCHIVE_DIR, "deepin-software-center-cache")
    
def get_filename(version):
    '''Get file name.'''
    return os.path.basename(version.filename)

def pkg_file_has_exist(pkg):
    # Check whether file have downloaded complete.
    candidate = pkg.candidate
    pkg_name = get_filename(candidate)
    pkg_path = os.path.join(ARCHIVE_DIR, pkg_name)
    if not os.path.exists(pkg_path) or os.stat(pkg_path).st_size != candidate.size:
        return False
    
    # Hash check 
    hash_type, hash_value = get_hash(pkg.candidate)
    try:
        return check_hash(pkg_path, hash_type, hash_value)
    except IOError, e:
        if e.errno != errno.ENOENT:
            print "Failed to check hash for %s: %s" % (pkg_name, e)
        return False
    
def get_hash(version):
    '''Get hash value.'''
    if version.sha256:
        return ("sha256", version.sha256)
    elif version.sha1:
        return ("sha1", version.sha1)
    elif version.md5:
        return ("md5", version.md5)
    else:
        return (None, None)
    
def check_hash(path, hash_type, hash_value):
    '''Check hash value.'''
    hash_fun = hashlib.new(hash_type)
    with open(path) as f:
        while 1:
            bytes = f.read(4096)
            if not bytes:
                break
            hash_fun.update(bytes)
    return hash_fun.hexdigest() == hash_value

if __name__ == "__main__":
    apt_pkg.init()
    cache = apt.Cache()
    
    (total_size, pkg_infos) = get_pkg_download_info(cache, "eric")

    import pprint
    pprint.pprint(pkg_infos)
