#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: audit_post_codes.py
---------------------------

This program audits the postal codes in openstreetmap file
of London. To validate the postal codes, regular expression
is used which conforms to the way postal codes are in UK.
If a particular postal code doesn't match the regular
expression, that element will be left out of the database.

For further reference of valid postal codes in London:
https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom#Validation
"""

import re
import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import json

OSM_FILE = 'london_england.osm'
OUTPUT_FILE = 'output_post_codes.json'

POST_CODES = re.compile(r"""[A-Z]{2}\d[A-Z]\ \d[A-Z]{2}
                        |   [A-Z]\d[A-Z]\ \d[A-Z]{2}
                        |   [A-Z]\d\ \d[A-Z]{2}
                        |   [A-Z]\d{2}\ \d[A-Z]{2}
                        |   [A-Z]{2}\d\ \d[A-Z]{2}
                        |   [A-Z]{2}\d{2}\ \d[A-Z]{2}""", re.VERBOSE)

def is_post_code(tag):
    """
    Usage: if is_post_code(tag): ...

    Returns whether the key value of tag element is of type post code.
    """
    return tag.attrib['k'] in ["addr:postcode", "postcode", "postal_code"]

def audit_post_code(invalid_post_codes, post_code):
    """
    Usage: audit_post_codes(invalid_post_codes, "TW8 9GS")

    Updates a set of invalid post codes , with a post code
    if the post code is not a valid UK postal code.
    """
    matches = POST_CODES.findall(post_code)
    # print post_code
    if (len(matches) == 0):
        invalid_post_codes.add(post_code)

def audit_post_codes(osm_file=OSM_FILE):
    invalid_post_codes = set()

    with open(osm_file, 'r') as file:
        context = ET.iterparse(file, events=("start", "end"))
        context = iter(context)
        event, root = context.next()

        for event, element in context:
            if event == "end" and element.tag in ["node", "way"]:
                for tag in element.iter("tag"):
                    if is_post_code(tag):
                        audit_post_code(invalid_post_codes, tag.attrib['v'])

                root.clear()

    with open(OUTPUT_FILE, 'w') as output_file:
        pprint.pprint(invalid_post_codes)
        post_codes = {'post_codes': list(invalid_post_codes)}
        json.dump(post_codes, output_file)

if __name__ == '__main__':
    audit_post_codes()
