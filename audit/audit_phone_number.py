#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: audit_phone_number.py
---------------------------

This program audits the phone number in openstreetmap file
of London, to find any potential problems. A suitable format
for representing the phone numbers would be choosen and will
be used to modify the entire data.

Fetches the information from db and updates the selected phone
numbers to match to a selected format.

Refer: https://en.wikipedia.org/wiki/Telephone_numbers_in_the_United_Kingdom#Format
Telephone numbers in London have the following structure
20xxxxxxxx, and the country code of england is +44.
The program aims at modifying all the phone numbers in the
db to the choosen format of 20xxxxxxxx.

Since in this open street map cities are nearby Londond also,
apart from 20 there are other codes.

There are two tables namely way_tags and node_tags that contain
phone number information.

Process of handling:

1. Remove "+44" or "+ 44" from all the phone numbers. +44 is UK's
telephone code, ie redundant information.
2. Remove all the spaces or dashes from the phone numbers.
4. Push the phone number back into database
"""
import pprint
import psycopg2
import psycopg2.extras
import sys
import re

try:
    # Get connection to database
    con = psycopg2.connect("dbname=osm_playground user=abkds")

    # Use a dictionary cursor
    dict_cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def update_numbers(cur):
        updated_records = []
        def update_phone_number(record):
            # Split on the basis of a separator, if there are more than
            # one number update all of them
            if ';' in record['value']:
                numbers = record['value'].split(';')
            elif ',' in record['value']:
                numbers = record['value'].split(',')
            elif '/' in record['value']:
                numbers = record['value'].split('/')
            elif ':' in record['value']:
                numbers = record['value'].split(':')
            else:
                numbers = record['value'].split(';')

            # Left strip the number of + and 0, if number starts with
            # 440 or 44 remove it, then save the number.
            for index, number in enumerate(numbers):
                number_ = re.sub(r"[^0-9+]", "", number)
                number_ = number_.lstrip('+')
                number_ = number_.lstrip('0')
                if number_.startswith('440'):
                    numbers[index] = number_[3:]
                elif number_.startswith('44'):
                    numbers[index] = number_[2:]
                else:
                    numbers[index] = number_

            # Check if it's actually a phone number
            # There are records where the value of phone is "yes"
            # We replaced all of non digit characters with blank
            # Check against the empty starting

            # If the number is 11 digit or 8 digit or less than 7 digits
            # don't push the number. If the number starts with 20 it must
            # be a 10 digit number.

            # pprint.pprint(numbers)
            if len(numbers) > 0:
                for number in numbers:
                    record_ = record.copy()
                    if len(number) > 10 or len(number) < 7 or len(number) == 8:
                        pass # ignore the record
                    elif number.startswith("20") and len(number) != 10:
                        pass # ignore the record
                    else:
                        record_['value'] = number
                        record_['key'] = 'phone'
                        updated_records.append(record_)

        for record in records:
            update_phone_number(record)

        return updated_records

    # Fetch telephone information from db
    #
    # There are many fields where key instead of just being 'phone' is
    # 'telephone' or 'phone_1' (type = 'regular'). To cover all the telephone
    # numbers the query contains LIKE for key phone.
    #
    dict_cur.execute("SELECT * FROM node_tags WHERE key LIKE '%phone%' AND type = any(array['regular', 'contact']);")
    records = dict_cur.fetchall()
    updated_records = update_numbers(records)

    # delete old records
    dict_cur.execute("DELETE FROM node_tags WHERE key LIKE '%phone%' AND type = any(array['regular', 'contact']);")
    pprint.pprint(updated_records)

    # push updated records
    dict_cur.executemany("""INSERT INTO node_tags(node_id, key, value, type) VALUES (%(node_id)s, %(key)s, %(value)s, %(type)s)""", updated_records)
    con.commit()

except psycopg2.DatabaseError, e:

    if con:
        con.rollback()

    print "Error %s" % e
    sys.exit(1)

finally:

    if con:
        con.close()
