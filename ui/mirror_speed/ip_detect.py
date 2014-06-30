#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
#from bottle import route, run
import GeoIP
import math
import sqlite3
import re
import urllib2  

current_dir = os.path.dirname(os.path.realpath(__file__))
mirrors_db_path = os.path.join(current_dir, "mirrors.db")
city_data_path = os.path.join(current_dir, "GeoLiteCity.dat")

OFFICIAL_MAIN_SITE="packages.linuxdeepin.com"
official_mirror = None
EARTH_RADIUS=6378.137

class Mirror(object):
    def __init__(self, hostname, ip_addr, country, city, latitude, longitude):
        self.hostname = hostname
        self.ip_addr = ip_addr
        self.country = country
        self.city = city
        self.latitude = latitude
        self.longitude = longitude

    @classmethod
    def load(cls, db):
        global official_mirror
        mirrors = []
        database = sqlite3.connect(db)
        db_cursor = database.cursor()
        db_cursor.execute("select hostname, ip, country, city, latitude, longitude from mirrors")
        result = db_cursor.fetchall()
        db_cursor.close()
        database.close()
        for record in result:
            m = Mirror(record[0], record[1], record[2], record[3], record[4], record[5])
            mirrors.append(m)
            if record[0] == OFFICIAL_MAIN_SITE:
                official_mirror = m
        return mirrors

MIRRORS= Mirror.load(mirrors_db_path)

def rad(d):
   return d * math.pi / 180.0

def get_distance(lat1,lng1,lat2,lng2):
    a = rad(lat1) - rad(lat2)
    b = rad(lng1) - rad(lng2)
    s = 2 * math.asin(math.sqrt(math.pow(math.sin(a/2), 2) + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.pow(math.sin(b/2),2)))
    s = s * EARTH_RADIUS
    if s < 0:
        return -s
    else:
        return s

def get_nearest_mirrors(mirrors=MIRRORS):
    ip_addr = getip()
    print "Current user IP:", ip_addr
    gic = GeoIP.open(city_data_path, 1)
    record = gic.record_by_addr(ip_addr)
    latitude = record['latitude']
    longitude = record['longitude']
    
    if not (latitude and longitude):
        return [official_mirror.hostname]

    distance_list = []
    for mirror in mirrors:
        if mirror.latitude and mirror.longitude:
            distance = get_distance(latitude, longitude, mirror.latitude, mirror.longitude)
            distance_list.append((distance, mirror.hostname))

    distance_list_sorted = sorted(distance_list, key=lambda distance: distance[0])[:5]
    return_list = []
    for (index, t) in enumerate(distance_list_sorted):
        if index < 5:
            return_list.append(t[1])
        else:
            break
    return return_list

def getip():  
    return re.search('\d+\.\d+\.\d+\.\d+',urllib2.urlopen("http://www.whereismyip.com").read()).group(0)
    #中间的那个http地址因不同的IP查询网站而group内容不一样，如果是http://whois.ipcn.org/的话，可能就group(1)了

if __name__ == "__main__":
    print get_nearest_mirrors()

"""
@route("/")
def root():
    my_ip = request.environ.get('REMOTE_ADDR')
    return my_ip

@route("/hello")
def hello():
    return "Hello World"

@route ("/bestmirror")
@route ("/bestmirror/")
@route ("/bestmirror/<ip_addr>")
def best_mirror(ip_addr=None):
    if not ip_addr:
        return OFFICIAL_MAIN_SITE
    else:
        nearest_mirror = get_nearest_mirror(ip_addr)
        return nearest_mirror.hostname

if __name__ == "__main__":
    run(host='0.0.0.0', port=8000, debug=True, reloader=True)
"""
