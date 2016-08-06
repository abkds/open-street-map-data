#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: update_street_names.py
---------------------------

This program updates the street names extracted from openstreetmap
file of London. All the potential errors as identified by auditing
would be used to modify and update the street names accordingly.

Fetches the information from db and updates the street names to match
uniform format.

Remove all brackets.

Each word of street names will be correctly capitalized to maintain
uniformity in names.

There are data points of the following types within the data,
<val='Cobham Avenue',<Priority; inDataSet: false, inStandard: false, selected: false>>

"""

import pprint
import psycopg2
import psycopg2.extras
import sys
import re

mapping = {
    "Ave": "Avenue",
    "Rd": "Road",
    "Rd.": "Road",
    "Road,": "Road",
    "St.": "Street",
    "St": "Street",
    "Sq": "Square",
    "Sr": "Street",
    "Ln": "Lane",
    "Rpad": "Road",
    "Strret": "Street",
    "Rad": "Road",
    "Avenuen": "Avenue",
    "Place?": "Place",
    "By-pass": "Bypass",
    "Riad": "Road",
    "Wqalk": "Walk",
    "Road--": "Road",
    "Road3": "Road",
    "Ct": "Court",
    "Berrylands'": "Berrylands",
    "N": "North"
}

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

try:
    # Get connection to database
    con = psycopg2.connect("dbname=osm_playground user=abkds")

    # Use a dictionary cursor
    dict_cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def update_streets(records):
        updated_records = []

        def update_street(record):
            street_name = record['value']

            # Strip off whitespace characters
            street_name = street_name.strip(' ')

            # Remove brackets
            street_name = re.sub("[()]", "", street_name)

            # Capitalize each token
            tokens = street_name.split(' ')

            tokens = [token.capitalize() for token in tokens]

            # join to get the street name
            street_name = ' '.join(tokens)

            # Use regex to match the street type
            m = street_type_re.search(street_name)

            # pprint.pprint(street_name)
            street_type = m.group()

            # special case if data ends with 'false>>'
            # note: the regex used here to find the value of street
            # is highly specific to this case, and shouldn't be
            # used elsewhere
            #
            # example:
            #   <val='Cobham Avenue',<Priority; inDataSet: false, inStandard: false, selected: false>>
            # Comparing with False>> since we capitalized the tokens
            if m.group() == 'False>>':
                street_name = re.findall(r"'(.*)'", street_name)[0]

            # update the street type using mapping
            if street_type in mapping:
                street_name = street_name[:m.start()] + mapping[street_type]

            # create a deep copy
            record_ = record.copy()

            #pprint.pprint(street_name)

            # update record with street name
            record_['value'] = street_name

            # update to the records
            updated_records.append(record_)

        for record in records:
            update_street(record)

        return updated_records

    # Fetch street name from db
    #
    # Update the street names as per the mapping of incorrect names
    # created by auditing the osm file.
    dict_cur.execute("SELECT * FROM way_tags WHERE key = 'street' AND type = 'addr';")
    records = dict_cur.fetchall()
    updated_records = update_streets(records)

    # delete old records
    dict_cur.execute("DELETE FROM way_tags WHERE key = 'street' AND type = 'addr';")
    pprint.pprint(updated_records)

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
