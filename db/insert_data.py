#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: insert_data.py
---------------------------

This script creates a connection to a postgresql database and
inserts the data from csv generated into the approriate tables.
"""

import os
import psycopg2
import sys

NODES_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'nodes.csv')
NODE_TAGS_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'node_tags.csv')
WAYS_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'ways.csv')
WAY_NODES_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'way_nodes.csv')
WAY_TAGS_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'way_tags.csv')

file_table_tuples = [
    (NODES_PATH, 'nodes'),
    (NODE_TAGS_PATH, 'node_tags'),
    (WAYS_PATH, 'ways'),
    (WAY_NODES_PATH, 'way_nodes'),
    (WAY_TAGS_PATH, 'way_tags')
]

try:
    # Connection to an exisiting database
    con = psycopg2.connect("dbname=osm_playground user=abkds")

    # Open a cursor to perform db operations
    cur = con.cursor()

    # Copy csv data to respective tables
    for file_table in file_table_tuples:
        with open(file_table[0]) as f:
            sql_copy = "COPY %s FROM STDIN WITH (FORMAT CSV, HEADER, QUOTE '\"')" % (file_table[1])
            cur.copy_expert(sql_copy, f)

    con.commit()

except psycopg2.DatabaseError, e:

    if con:
        con.rollback()

    print "Error %s" % e
    sys.exit(1)

finally:

    if con:
        con.close()
