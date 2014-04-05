#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb


def read_image():
    
    fin = open("woman.jpg")    
    img = fin.read()
    
    return img
    

con = mdb.connect('localhost', 'testuser', 'test623', 'testdb')
 
with con:
    
    cur = con.cursor()
    data = read_image()
    cur.execute("CREATE TABLE Images(Id INT PRIMARY KEY, Data MEDIUMBLOB)")
    cur.execute("INSERT INTO Images VALUES(2, %s)", (data, ))
    print 'insert_images finished'

