#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: audit_street_names.py
---------------------------

This program audits the street names in openstreetmap file,
to find any potential problems in street names of various
areas of the map. If the street names are not consisistent
with one another, a particular mapping will be choosen to
rectify all the street names.
"""

import re
import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import json

OSM_FILE = 'london_england.osm'
STREET_TYPE = re.compile(r'\b\S+\.?$', re.IGNORECASE)
OUTPUT_FILE = 'output.json'

# Typical street names
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Circle", "Crescent", "Gate", "Terrace", "Grove", "Way"]


def is_street_name(tag):
    """
    Usage: if is_street_name(tag): ...

    Returns whether the key value of tag element is of type street address.
    """
    return tag.attrib['k'] == "addr:street"

def audit_street_type(street_types, street_name):
    """
    Usage: audit_street_type(street_types, "Seventh Boulevard")

    Updates a dictionary of street_types, with a street name if
    the street type is not in the expected list of street names.
    """
    matches = STREET_TYPE.findall(street_name)
    if (len(matches) > 0):
        street_type = matches[0]
        if street_type not in expected:
            street_types[street_type].append(street_name)

def audit_street(osm_file):
    street_types = defaultdict(list)
    with open(osm_file, 'r') as file:
        context = ET.iterparse(file, events=("start", "end"))
        context = iter(context)
        event, root = context.next()

        for event, element in context:
            if event == "end" and element.tag in ["node", "way"]:
                for tag in element.iter("tag"):
                    if is_street_name(tag):
                        audit_street_type(street_types, tag.attrib['v'])

                root.clear()

    with open(OUTPUT_FILE, 'w') as output_file:
        pprint.pprint(street_types)
        json.dump(street_types, output_file)

def load_street_types(input_file=OUTPUT_FILE):
	with open(input_file) as input:
		street_types = json.load(input)
		street_type_names = [k for k, v in street_types.iteritems()]
		pprint.pprint(street_type_names)



if __name__ == '__main__':
	audit_street()
