#!/usr/bin/env python
import re
import csv
import urllib2
import datetime as dt
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

def parse_date(date):
    months = ["January","February","March","April","May","June","July",
              "August","September","October","November","December"]
    month_re = '|'.join(months)

    date = date.replace('206', '2006')

    match = re.match('(%s)\s+(\d{1,2})[,.]{0,1}\s+(\d{4})' % month_re, date)
    if match:
        month = months.index(match.group(1)) + 1
        return dt.date(int(match.group(3)),
                       month,
                       int(match.group(2))).isoformat()

    match = re.match('(%s)\s+(\d{1,2})-\s{0,}(\d{1,2})[,.]{0,1}\s+(\d{4})' % month_re, date)
    if match:
        month = months.index(match.group(1)) + 1
        d1 = dt.date(int(match.group(4)), month, int(match.group(2)))
        d2 = dt.date(int(match.group(4)), month, int(match.group(3)))
        return "%s to %s" % (d1.isoformat(), d2.isoformat())

    match = re.match("(%s)\s+(\d{1,2})-\s{0,}(%s)\s+(\d{1,2})[,.]{0,1}\s+(\d{4})" % (month_re, month_re), date)
    if match:
        m1 = months.index(match.group(1)) + 1
        m2 = months.index(match.group(3)) + 1
        d1 = dt.date(int(match.group(5)), m1, int(match.group(2)))
        d2 = dt.date(int(match.group(5)), m2, int(match.group(4)))
        return "%s to %s" % (d1.isoformat(), d2.isoformat())

    match = re.match("(%s)\s+(\d{1,2})-\s{0,}(\d{1,2}) and (%s)\s+(\d{1,2})-\s{0,}(\d{1,2})[,.]{0,1}\s+(\d{4})" % (month_re, month_re), date)
    if match:
        m1 = months.index(match.group(1)) + 1
        m2 = months.index(match.group(4)) + 1
        year = int(match.group(7))
        d1 = dt.date(year, m1, int(match.group(2)))
        d2 = dt.date(year, m1, int(match.group(3)))
        d3 = dt.date(year, m2, int(match.group(5)))
        d4 = dt.date(year, m2, int(match.group(6)))
        return "%s to %s and %s to %s" % (d1.isoformat(), d2.isoformat(),
                                   d3.isoformat(), d4.isoformat())
    return None

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
                date = parse_date(clean(cols[0].find(text=non_empty)))
                if not date:
                    continue
                visitor = clean(cols[1].find(text=non_empty))
                country = clean(cols[2].find(text=non_empty))
                description = clean(cols[3].find(text=non_empty))
                out.writerow([date, country, visitor, description])

if __name__ == "__main__":
    scrape()
