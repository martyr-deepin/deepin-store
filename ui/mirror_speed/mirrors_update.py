#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import sqlite3
import socket
import GeoIP
import chardet

current_dir = os.path.dirname(os.path.realpath(__file__))
mirrors_db_path = os.path.join(current_dir, "mirrors.db")
city_data_path = os.path.join(current_dir, "GeoLiteCity.dat")

def add_mirror(mirror_hostname, db=mirrors_db_path):
    db_conn = sqlite3.connect(db)
    db_cursor = db_conn.cursor()
    sql_select = "select * from mirrors where hostname=?"
    sql_args = (mirror_hostname, )
    db_cursor.execute(sql_select, sql_args)
    if db_cursor.fetchone():
        print "data exists for hostname:", mirror_hostname
        return

    # get mirror info from geoip
    print "fetch ip address for hostname:", mirror_hostname
    ip = socket.getaddrinfo(mirror_hostname, None)[0][4][0]
    gic = GeoIP.open(city_data_path, 1)
    record = gic.record_by_addr(ip)

    # insert data to database
    sql_insert = "insert into mirrors values (null, ?, ?, ?, ?, ?, ?)"
    if record:
        origin_sql_args = (mirror_hostname, ip, record['country_code'],
                record['city'], record['latitude'], record['longitude'])
    else:
        origin_sql_args = (mirror_hostname, ip, "", "", "", "")

    sql_args = []
    for s in origin_sql_args:
        s = str(s)
        r = chardet.detect(s)
        encoding = r["encoding"]
        if s == "":
            sql_args.append("")
        elif encoding == "ascii":
            sql_args.append(s.decode("utf-8"))
        else:
            sql_args.append(s.decode(r["encoding"]))
    sql_args = tuple(sql_args)
    print "==> [info]", sql_args

    db_cursor.execute(sql_insert, sql_args)
    db_conn.commit()

def init_db(db=mirrors_db_path, delete_table=True):
    db_conn = sqlite3.connect(db)
    db_cursor = db_conn.cursor()
    db_cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master where type='table' and name='mirrors'")
    num = db_cursor.fetchone()[0]
    if num > 0:
        if delete_table:
            db_cursor.execute("DROP TABLE mirrors")
            print "Delete old table"
            db_cursor.execute(
                "create table mirrors (id integer primary key, hostname text unique, ip text, country text, city text, latitude real, longitude real)")
    else:
        db_cursor.execute(
            "create table mirrors (id integer primary key, hostname text unique, ip text, country text, city text, latitude real, longitude real)")

    db_conn.commit()
    print "Init mirrors table"

def update(delete_table=True):
    init_db(delete_table=delete_table)
    from mirrors import get_mirrors
    mirror_list = get_mirrors()
    for m in mirror_list:
        add_mirror(m.host)

def run():
    Usage = """Usage:
    %s init
    %s update
    """ % (__file__, __file__)
    if len(sys.argv) <= 1:
        print Usage

    elif len(sys.argv) == 2:
        if sys.argv[-1] == "init":
            update()
        elif sys.argv[-1] == "update":
            update(False)
        else:
            print Usage
    else:
        print Usage

if __name__ == "__main__":
    run()
