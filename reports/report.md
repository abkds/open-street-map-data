# OpenStreetMap Data Case Study

### Map Area
London, England

- [https://www.openstreetmap.org/relation/65606](https://www.openstreetmap.org/relation/65606)
- [http://metro.teczno.com/#london](http://metro.teczno.com/#london)

The map of London (osm file) is quite large, around ```2.4 GB```, which provides a
great opportunity to deal with a large dataset and the issues associated with it.

## Problems Encountered in the Map

Since the dataset was quite large, a sample was created for analyzing various problems in the dataset. Sample osm was around ```0.5 MB```. The sample size was good enough to find the provisional problems in the data.

- “Incorrect” postal codes (UK postal codes end in 3 characters, apart from the first part, there were various postal codes not conforming to that, example: "E15 2", "RH1 ???")
- Inconsistent postal codes (Many postal codes were not in the right format example: "SE186GD", "KT168AP")
- Inconsistent phone numbers (Phone numbers were not uniform, some started with +44,  some had '(0)' in the numbers, more than one number were clubbed together)
- "Incorrect" phone numbers (Phone numbers can only have 10, 9 or 7 digits, phone numbers with 11 digits or incomplete numbers were there)
- Abbreviated street names *("Old Dover Rd")*
- XML data within street name *("< val='Cobham Avenue',Priority; inDataSet: false, inStandard: false, selected: false >>")*

	```XML
	<tag k="addr:street" v="<val='Cobham Avenue';,<Priority; inDataSet: false, inStandard: false, selected: false>>"/>
	```

### "Incorrect" postal codes

Once the data was imported to SQL revealed that there are many postal codes that are incomplete. Example: "AL2","HA8","MK18","GU12". These are invalid post code according to the post code rules of UK. A regex was used to validate the post codes.

```python
POST_CODES = re.compile(r"""^[A-Z]{2}\d[A-Z]\ \d[A-Z]{2}$
                        |   ^[A-Z]\d[A-Z]\ \d[A-Z]{2}$
                        |   ^[A-Z]\d\ \d[A-Z]{2}$
                        |   ^[A-Z]\d{2}\ \d[A-Z]{2}$
                        |   ^[A-Z]{2}\d\ \d[A-Z]{2}$
                        |   ^[A-Z]{2}\d{2}\ \d[A-Z]{2}$""", re.VERBOSE)
```

All incorrect postal codes were then removed from the database.

### Inconsistent postal codes
Postal codes in the United Kingdom follow the rules as mentioned in the previous regex. They should be all capital. There were many postal codes where the characters were small. Some postal codes there was no space between the first and last part of the postal code. Example: *"TW208TE"*, to correct similar types of issues a space was inserted between the two parts of the postal code and then validated against the regex. If valid, the data was kept otherwise deleted from the database.


```python
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
```

### Inconsistent phone numbers
Phone numbers were highly non uniform in the database, some values had more than one number clubbed together by a separator.
Some numbers started with +44 (UK country code), 044, +044 and then there were some which had (0) in the number, after the country code. All the numbers were made uniform by stripping of *'-'*, *' '* and country codes from the number. In case of multiple numbers clubbed together, they were separated out and each number was pushed alone in the database again.

```python
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
```

### "Incorrect" phone numbers
Phone numbers can only have 10, 9 or 7 digits, phone numbers with 11 digits or incomplete numbers were there. All invalid phone numbers were removed from the database.

```python
if len(number) > 10 or len(number) < 7 or len(number) == 8:
    pass # ignore the record
elif number.startswith("20") and len(number) != 10:
    pass # ignore the record
else:
    record_['value'] = number
    record_['key'] = 'phone'
    updated_records.append(record_)
```

Again, in London numbers starting with 20 code should have ten digits. If they are less or more than that, that phone number is deleted from the database.

### Abbreviated street names
Street name abbreviations were pretty common in the dataset. To fetch the type of the street, regex was used. A mapping was created specific to the particular dataset to fix the street names. Each word of the street name was capitalized to make it more uniform.

```python
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

street_type = m.group()

# update the street type using mapping
if street_type in mapping:
    street_name = street_name[:m.start()] + mapping[street_type]
```

### XML data within street name
Various street names had the following type of value
```<tag k="addr:street" v="<val='Cobham Avenue';,<Priority; inDataSet: false, inStandard: false, selected: false>>"/>```.
To fix this a regex was used to extract out the correct value of street name and then it was pushed back again.

```python
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
```

# Sort cities by count, descending

```sql
SELECT tags.value, COUNT(*) as count
FROM (SELECT * FROM node_tags UNION ALL
      SELECT * FROM way_tags) tags
WHERE tags.key = 'city'
GROUP BY tags.value
ORDER BY count DESC;
```
```sql
SELECT value, COUNT(*) as count
FROM node_tags
WHERE tags.key = 'city'
GROUP BY value
ORDER BY count DESC;
```
```sql
SELECT value, COUNT(*) as count
FROM node_tags
WHERE tags.key = 'city'
GROUP BY value
ORDER BY count DESC;
```

Surprsingly the results have *Reading* more number of times that of *London*. But on querying each table individually it makes more sense. ```node_tags``` has *London* as the max count but ```way_tags``` have *Reading* as the max count.


```sql
       value       | count
-------------------+-------
 Reading           | 49492
 London            | 19244
 Swanley           |  6206
 Maldon            |  5707
 Horsham           |  4631
 Burnham-On-Crouch |  2424
 Heybridge         |  2399
 Walthamstow       |  1992
 Redhill           |  1434
 Rochester         |  1414     
```

```sql
    value    | count
-------------+-------
 London      |  5219
 Swanley     |  1608
 Walthamstow |  1361
 Wembley     |   697
 Colchester  |   561
 Reigate     |   547
 Luton       |   540
 Horsham     |   373
 Redhill     |   301
 Woking      |   272
```

```sql
       value       | count
-------------------+-------
 Reading           | 49302
 London            | 14025
 Maldon            |  5489
 Swanley           |  4598
 Horsham           |  4258
 Burnham-On-Crouch |  2422
 Heybridge         |  2399
 Rochester         |  1369
 Crawley           |  1299
 Houghton Regis    |  1262
```

These results confirm that the dataset contains various suburban areas around London also, like "Reading". This explains various phone numbers in which the telephone code doesn't start 20, which is telephone code for London.

# Data Overview
This section encompasses some basic statistics about the dataset and the various queries used to gather that.

### File sizes
```
london_england.osm ......... 2.4 GB
osm_playground.db .......... 2135 MB
nodes.csv ............. 876 MB
nodes_tags.csv ........ 68 MB
ways.csv .............. 91 MB
ways_tags.csv ......... 146 MB
ways_nodes.cv ......... 314 MB  
```  

### Number of nodes
```
SELECT COUNT(*) FROM nodes;
```
11210246

### Number of ways
```
SELECT COUNT(*) FROM ways;
```
1601347

### Number of unique users
```sql
SELECT COUNT(DISTINCT(users.uid))          
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) users;
```
8724

### Number of phone numbers in database
```sql
SELECT count(*)
FROM (SELECT * FROM node_tags
	  UNION ALL
      SELECT * FROM way_tags) tags
WHERE tags.key = 'phone';
```

10227

### Number of phone numbers from London area
```sql
SELECT count(*)
FROM (SELECT * FROM node_tags
	  UNION ALL
      SELECT * FROM way_tags) tags
WHERE tags.key = 'phone'
AND tags.value like '20%';
```

5313

These values also confirm that osm file covers all the nearby regions to London and
not just the London area.

### Top 10 contributing users
```sql
SELECT users.user, COUNT(*) as num
FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) users
GROUP BY users.user
ORDER BY num DESC
LIMIT 10;
```

```sql
           username           |  num   
------------------------------+--------
 The Maarssen Mapper          | 471257
 Eriks Zelenka                | 457228
 TimSC_Data_CC0_To_Andy_Allan | 448425
 ca_hoot                      | 362387
 Johnmb                       | 358202
 busdoc                       | 357044
 Essex_Boy                    | 296573
 c2r                          | 230286
 DanGregory                   | 217272
 Rondon237                    | 206046
```

The contribution from the top users is around 2 to 3 percent each. There is no
skew in terms of contribution to open street map data.

### Top 10 street name types
```sql
SELECT street_type, count(*)
AS count
FROM (
	  SELECT regexp_replace(value, '^.* ', '')
	  AS street_type
	  FROM (
	  		SELECT * FROM node_tags UNION ALL
      		SELECT * FROM way_tags
      		)
      AS tags
      WHERE key = 'street' AND type = 'addr'
      )
AS street_types
GROUP BY street_type
ORDER BY count DESC
LIMIT 10;
```

```sql
street_type | count
-------------+-------
Road        | 88610
Street      | 22186
Avenue      | 18969
Close       | 13026
Lane        |  8464
Way         |  6618
Drive       |  6515
Gardens     |  5490
Crescent    |  3739
Grove       |  3209
```

Postal codes were validated earlier.
### Top 10 postal codes
```sql
SELECT tags.value, COUNT(*) as count
FROM (SELECT * FROM node_tags
	  UNION ALL
      SELECT * FROM way_tags) tags
WHERE tags.key='postcode' AND tags.type = 'addr'
GROUP BY tags.value
ORDER BY count DESC
LIMIT 10;
```

```sql
value   | count
----------+-------
LU5 5QQ  |   156
LU5 5RJ  |   134
LU5 5PN  |   133
LU5 5RN  |   123
SW11 3TS |   105
ME19 5QG |    77
LU5 5PJ  |    74
ME7 2LP  |    69
DA7 5EY  |    68
ME7 2EH  |    67
```

## Additional Data Exploration

### Top 10 appearing amenities

```sql
SELECT value, COUNT(*) AS num
FROM node_tags
WHERE key='amenity'
GROUP BY value
ORDER BY num DESC
LIMIT 10;
```

```sql
      value       |  num  
------------------+-------
 post_box         | 13715
 bench            |  7608
 bicycle_parking  |  5959
 pub              |  5399
 restaurant       |  4337
 telephone        |  4011
 cafe             |  3304
 waste_basket     |  3198
 fast_food        |  2712
 place_of_worship |  2555
```

### Most coffee houses
```sql
SELECT value, count(*) AS count
FROM node_tags
JOIN (SELECT DISTINCT(node_id) FROM node_tags WHERE value = 'cafe') AS i
ON node_tags.node_id = i.node_id
WHERE node_tags.key = 'name'
GROUP BY value
ORDER BY count DESC
LIMIT 3;
```

```sql
value         | count
---------------+-------
Costa         |   146
Starbucks     |   144
Pret A Manger |    88
Costa Coffee  |    63
```

### Most pubs
```sql
SELECT value, count(*) AS count
FROM node_tags
JOIN (SELECT DISTINCT(node_id) FROM node_tags WHERE value = 'pub') AS i
ON node_tags.node_id = i.node_id
WHERE node_tags.key = 'name'
GROUP BY value
ORDER BY count DESC
LIMIT 5;
```

```sql
value      | count
----------------+-------
The Red Lion   |    58
The Crown      |    53
The Plough     |    46
The Royal Oak  |    43
The White Hart |    41
```

Similar queries can be made on other types of amenities as well.

### Most popular cuisine
```sql
SELECT node_tags.value, COUNT(*) as num
FROM node_tags
    JOIN (SELECT DISTINCT(node_id) FROM node_tags WHERE value='restaurant') i
    ON node_tags.node_id=i.node_id
WHERE node_tags.key='cuisine'
GROUP BY node_tags.value
ORDER BY num DESC;
```

```sql
value   | num
----------+-----
indian   | 502
italian  | 415
chinese  | 225
pizza    | 124
thai     | 119
japanese | 101
french   |  83
turkish  |  60
burger   |  56
asian    |  48
```


# Conclusion
Reviewing the London open street map, I believe that it was well cleaned for making the queries. The query results gave us good insights on the geography of London.
As confirmed by city names and the telephone numbers the London osm file contains data about all the nearby areas to London also.

# Additional Ideas
Phone numbers could have been validated more, by using some kind of APIs to validate, which check whether the phone number actually exists. But for the purposes
of this data analysis, that would have been farfetched.
