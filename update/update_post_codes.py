#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: update_post_code.py
---------------------------

This script validates the post codes in the London area for
correctness. All invalid codes are then removed from the database.
Fetches the post codes from db and validates them. If invalid it
is discarded.

For further reference of valid postal codes in London:
https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom#Validation

A regex is used to validate the post codes.

Steps used to modify the post codes.

1. Make the post code upper case.
2. If there is no space in the post code, put a space three places
before the back, and then validate.
3. If not validated, discard.
"""

import pprint
import psycopg2
import psycopg2.extras
import sys
import re

MIN_VALID_POST_CODE_LENGTH = 5

POST_CODES = re.compile(r"""^[A-Z]{2}\d[A-Z]\ \d[A-Z]{2}$
                        |   ^[A-Z]\d[A-Z]\ \d[A-Z]{2}$
                        |   ^[A-Z]\d\ \d[A-Z]{2}$
                        |   ^[A-Z]\d{2}\ \d[A-Z]{2}$
                        |   ^[A-Z]{2}\d\ \d[A-Z]{2}$
                        |   ^[A-Z]{2}\d{2}\ \d[A-Z]{2}$""", re.VERBOSE)

try:
    # Get connection to database
    con = psycopg2.connect("dbname=osm_playground user=abkds")

    # Use a dictionary cursor
    dict_cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def update_post_codes(records):
        updated_records = []
        def update_post_code(record):
            post_code = record['value']

            # make the post code upper case
            post_code = post_code.upper()

            record_ = record.copy()

            # check to see if it contains space
            # if not insert at 3 places from behind.
            # all UK post codes have a 3 letter ending
            if ' ' in post_code:
                m = POST_CODES.search(post_code)

                if m is not None:
                    # this post code is fine
                    record_['value'] = post_code
                    updated_records.append(record_)
            else:
                if len(post_code) >= MIN_VALID_POST_CODE_LENGTH:
                    post_code = post_code[:-3] + ' ' + post_code[-3:]
                    m = POST_CODES.search(post_code)

                    if m is not None:
                        record_['value'] = post_code
                        updated_records.append(record_)


        for record in records:
            update_post_code(record)

        return updated_records

    # Fetch post codes information from db
    dict_cur.execute("SELECT * FROM way_tags WHERE key = 'postcode' and type = 'addr';")
    records = dict_cur.fetchall()
    updated_records = update_post_codes(records)

    # delete old records
    dict_cur.execute("DELETE FROM way_tags WHERE key = 'postcode' AND type = 'addr';")
    pprint.pprint(updated_records)

    print len(updated_records)
    # push updated records
    dict_cur.executemany("""INSERT INTO way_tags(way_id, key, value, type) VALUES (%(way_id)s, %(key)s, %(value)s, %(type)s)""", updated_records)
    con.commit()

except psycopg2.DatabaseError, e:

    if con:
        con.rollback()

    print "Error %s" % e
    sys.exit(1)

finally:

    if con:
        con.close()
