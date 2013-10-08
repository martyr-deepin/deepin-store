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
import errno
import hashlib
import traceback
import apt_pkg
from utils import log
from constant import DOWNLOAD_STATUS_NOTNEED, DOWNLOAD_STATUS_ERROR, ACTION_UPGRADE
import apt.debfile as debfile
from events import global_event

def get_deb_download_info(cache, deb_file):
    try:
        deb_package = debfile.DebPackage(deb_file, cache)
        
        if not (deb_package.compare_to_version_in_cache() == deb_package.VERSION_NONE):
            log("%s: package has installed" % deb_file)
            return DOWNLOAD_STATUS_ERROR
        elif not deb_package.check_breaks_existing_packages():
            log("%s: install package will break existing package" % deb_file)
            return DOWNLOAD_STATUS_ERROR
        elif not deb_package.check_conflicts():
            log("%s: package conflicts with existing packages" % deb_file)
            return DOWNLOAD_STATUS_ERROR
        else:
            deb_package.check()
            (install_packages, remove_packages, unauthenticated_packages) = deb_package.required_changes
            
            depend_packages = []
            depend_ok = True
            
            for depend in deb_package.depends:
                for (pkg_name, require_version, version_operator) in depend:
                    print "***: %s %s" % (cache[pkg_name].versions, require_version)
                    newest_version = cache[pkg_name].versions[0].version
                    if apt_pkg.check_dep(newest_version, version_operator, require_version):
                        depend_packages.append(pkg_name)
                    else:
                        depend_ok = False
                        log("Check depend %s failed" % (pkg_name))
                        return DOWNLOAD_STATUS_ERROR
        
            if depend_ok:        
                for pkg_name in install_packages + depend_packages:
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
        log(str(traceback.format_exc()))
        
        return DOWNLOAD_STATUS_ERROR

def get_cache_pkg(cache, pkg_name):
    try:
        return (pkg_name, cache[pkg_name])
    except:
        try:
            pkg_name += ':i386'
            return (pkg_name, cache[pkg_name])
        except:
            return (pkg_name, None)

def get_upgrade_download_info_with_new_policy(cache, pkg_names):
    cache._depcache.init()
    failed_analyze_pkgs = []
    dependence = []
    try:
        for name in pkg_names:
            new_name, pkg = get_cache_pkg(cache, name)
            if not pkg:
                failed_analyze_pkgs.append(name)
                global_event.emit('parse-download-error', name, ACTION_UPGRADE)
            else:
                if cache.is_pkg_upgradable(new_name):
                    pkg.mark_upgrade()
                elif not cache.is_pkg_installed(new_name):
                    pkg.mark_install()
    except Exception, e:
        global_event.emit('parse-packages-failed', e)
    dependence = cache.get_changes()
    all_upgrade_pkg_names = [pkg.name for pkg in dependence]
    cache._depcache.init()
    if dependence == []:
        return (DOWNLOAD_STATUS_NOTNEED, failed_analyze_pkgs, all_upgrade_pkg_names)
    else:
        return (check_pkg_download_info(dependence), failed_analyze_pkgs, all_upgrade_pkg_names)

def get_pkg_download_info(cache, pkg_name):
    dependence = get_pkg_dependence(cache, pkg_name)
    if dependence == []:
        return DOWNLOAD_STATUS_NOTNEED
    elif dependence == -1:
        return DOWNLOAD_STATUS_ERROR
    else:
        return check_pkg_download_info(dependence)

def get_pkg_dependence(cache, pkg_name):
    try:
        pkg = cache[pkg_name]
    except:
        try:
            pkg_name = pkg_name+":i386"
            pkg = cache[pkg_name]
        except:
            return -1

    if cache.is_pkg_upgradable(pkg_name):
        pkg.mark_upgrade()
    elif not cache.is_pkg_installed(pkg_name):
        pkg.mark_install()
        
    # Get package information.
    pkgs = sorted(cache.get_changes(), key=lambda pkg: pkg.name)
    cache._depcache.init()
    return pkgs

def get_pkg_own_size(cache, pkg_name):
    try:
        pkg = cache[pkg_name]
        version = pkg.candidate
        return int(version.installed_size)
    except:
        try:
            pkg_name = pkg_name+":i386"
            pkg = cache[pkg_name]
            version = pkg.candidate
            return int(version.installed_size)
        except:
            return 0
    
def check_pkg_download_info(pkgs):
    total = len(pkgs)
    if len(pkgs) >= 1:
        pkgs = [pkg for pkg in pkgs if not pkg.marked_delete and not pkg_file_has_exist(pkg)]
        
        if len(pkgs) == 0:
            return DOWNLOAD_STATUS_NOTNEED
        else:
            try:
                urls = []
                hash_infos = []
                pkg_sizes = []
                names = []
                
                for pkg in pkgs:
                    version = pkg.candidate
                    hashtype, hashvalue = get_hash(version)
                    pkg_uris = version.uris
                    pkg_size = int(version.size)
                    
                    urls.append(pkg_uris[0])
                    hash_infos.append((hashtype, hashvalue))
                    pkg_sizes.append(pkg_size)
                    names.append(pkg.name)
                    
                return (names, urls, hash_infos, pkg_sizes, total)
            except Exception, e:
                print "get_pkg_download_info error: %s" % (e)
                log(str(traceback.format_exc()))
                
                return DOWNLOAD_STATUS_ERROR
    else:
        return DOWNLOAD_STATUS_NOTNEED
    
def get_cache_archive_dir():
    return apt_pkg.config.find_dir("Dir::Cache::Archives")    

def get_filename(version):
    '''Get file name.'''
    return os.path.basename(version.filename)

def pkg_file_has_exist(pkg):
    # Check whether file have downloaded complete.
    candidate = pkg.candidate
    pkg_name = get_filename(candidate)
    pkg_path = os.path.join(get_cache_archive_dir(), pkg_name)
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

def get_pkg_dependence_file_path(cache, pkg_name):

    cache_archive_dir = get_cache_archive_dir()
    file_paths = []
    try:
        pkg = cache[pkg_name]
    except:
        try:
            pkg_name = pkg_name + ":i386"
            pkg = cache[pkg_name]
        except:
            return file_paths

    if cache.is_pkg_upgradable(pkg_name):
        pkg.mark_upgrade()
    elif not cache.is_pkg_installed(pkg_name):
        pkg.mark_install()
        
    # Get package information.
    pkgs = sorted(cache.get_changes(), key=lambda pkg: pkg.name)
    cache._depcache.init()
    file_paths.append(os.path.join(cache_archive_dir, get_filename(pkg.candidate)))
    for pkg in pkgs:
        file_paths.append(os.path.join(cache_archive_dir, get_filename(pkg.candidate)))
    return file_paths

if __name__ == "__main__":
    from apt_cache import AptCache
    cache = AptCache()
    
    # deb_package = debfile.DebPackage("/test/Download/geany_1.22+dfsg-2_amd64.deb", cache)
    # print deb_package.VERSION_NONE, deb_package.VERSION_OUTDATED, deb_package.VERSION_SAME, deb_package.VERSION_NEWER
    # print deb_package.compare_to_version_in_cache()
    # print deb_package.check()
    # print deb_package.check_breaks_existing_packages()
    # print deb_package.check_conflicts()

    for path in get_pkg_dependence_file_path(cache, "kingsoft-office"):
        print path
