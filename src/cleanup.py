#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb

con = mdb.connect('localhost', 'testuser', 'test623', 'testdb');

with con:
    
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS Images")
    cur.execute("DROP TABLE IF EXISTS Writers")
    print 'cleanup finished'
