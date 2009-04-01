#!/usr/bin/env python
import re
import csv
import urllib2
from BeautifulSoup import BeautifulSoup

def clean(str):
    str = str.replace('&nbsp;', ' ').replace('&amp;', 'and').strip()

    # Cleanup some country names
    if str == 'Bosnia- Herzegovina':
        str = 'Bosnia-Herzegovina'
    elif str == "China, Peoples' Republic of":
        str = "China, People's Republic of"
    elif str == 'Congo, Democratic Republic of':
        str = 'Congo, Democratic Republic of the'
    elif str == 'Congo, Republic of':
        str = 'Congo, Republic of the'
    elif str in ['Poland (Government-in- exile)',
                 'Poland (Government-in-exile)',
                 'Poland (government-in- exile)']:
        str = 'Poland (government-in-exile)'
    elif str == 'U.S.S.R.':
        str = 'USSR'

    return str

def scrape():
    """Grab US State Department lists of visits to the US by foreign
    heads of state and dump them to a CSV file."""
    out = csv.writer(open('./visits.csv', 'w'))
    out.writerow(['date', 'country', 'visitor', 'description'])
    base_url = "http://www.state.gov/r/pa/ho/c1792.htm"
    base_site = BeautifulSoup(urllib2.urlopen(base_url).read())

    years = ['1874-1939', '1940-1944', '1945-1949']
    years.extend(map(lambda y: str(y), range(1950, 2008)))

    for year in years:
        # Find detailed listing
        link = base_site.find(text=year).findPrevious('a')
        list = BeautifulSoup(urllib2.urlopen(link['href']))

        for row in list.find("table").findAll("tr")[1:]:
            cols = row.findAll('td')
            if cols and len(cols) == 4:
                non_empty = re.compile(".+")
                date = clean(cols[0].find(text=non_empty))
                visitor = clean(cols[1].find(text=non_empty))
                country = clean(cols[2].find(text=non_empty))
                description = clean(cols[3].find(text=non_empty))
                out.writerow([date, country, visitor, description])

if __name__ == "__main__":
    scrape()
