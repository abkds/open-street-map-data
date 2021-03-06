#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: create_db.py
---------------------------

This script creates a connection to a postgresql database and
creates the tables for the open street map data.

It assumes that a database has been already created and connects
to an existing database.
"""

import psycopg2
import sys

CREATE_NODE = """
CREATE TABLE nodes (
    id BIGINT PRIMARY KEY,
    lat NUMERIC,
    lon NUMERIC,
    username TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    moment TIMESTAMP
);
"""

CREATE_NODE_TAGS = """
CREATE TABLE node_tags (
    node_id BIGINT REFERENCES nodes (id),
    key TEXT,
    value TEXT,
    type TEXT
);
"""

CREATE_WAY = """
CREATE TABLE ways (
    id BIGINT PRIMARY KEY,
    username TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    moment TIMESTAMP
);
"""

CREATE_WAY_TAGS = """
CREATE TABLE way_tags (
    way_id BIGINT REFERENCES ways (id),
    key TEXT,
    value TEXT,
    type TEXT
);
"""

CREATE_WAY_NODES = """
CREATE TABLE way_nodes (
    way_id BIGINT REFERENCES ways (id),
    node_id BIGINT REFERENCES nodes (id),
    position INTEGER,
    PRIMARY KEY (way_id, node_id, position)
);
"""

con = None

try:
    # Connection to an exisiting database
    con = psycopg2.connect("dbname=osm_playground user=abkds")

    # Open a cursor to perform db operations
    cur = con.cursor()

    # Create the tables
    cur.execute(CREATE_NODE);
    cur.execute(CREATE_NODE_TAGS);
    cur.execute(CREATE_WAY);
    cur.execute(CREATE_WAY_NODES)
    cur.execute(CREATE_WAY_TAGS);

    # Commit the changes
    con.commit()

except psycopg2.DatabaseError, e:

    if con:
        con.rollback()

    print "Error %s" % e
    sys.exit(1)

finally:

    if con:
        con.close()
