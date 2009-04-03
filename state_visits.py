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

    return str.encode('ascii', 'replace')

def parse_date(date):
    months = ["January","February","March","April","May","June","July",
              "August","September","October","November","December"]
    month_re = '|'.join(months)

    date = date.replace('206', '2006').replace('July 68', 'July 8')
    date = date.replace('October 2023', 'October 20-23')
    date = date.replace('December 14 and 15', 'December 14-15')

    match = re.search('(%s)\s{0,}(\d{1,2})[,.;]{0,1}\s+(\d{4})' % month_re, date)
    if match:
        month = months.index(match.group(1)) + 1
        return dt.date(int(match.group(3)),
                       month,
                       int(match.group(2))).isoformat()

    match = re.search('(%s)\s{0,}(\d{1,2})-\s{0,}(\d{1,2})[,.;]{0,1}\s+(\d{4})' % month_re, date)
    if match:
        month = months.index(match.group(1)) + 1
        d1 = dt.date(int(match.group(4)), month, int(match.group(2)))
        d2 = dt.date(int(match.group(4)), month, int(match.group(3)))
        return "%s to %s" % (d1.isoformat(), d2.isoformat())

    match = re.search("(%s)\s{0,}(\d{1,2})-\s{0,}(%s)\s+(\d{1,2})[,.;]{0,1}\s+(\d{4})" % (month_re, month_re), date)
    if match:
        m1 = months.index(match.group(1)) + 1
        m2 = months.index(match.group(3)) + 1
        d1 = dt.date(int(match.group(5)), m1, int(match.group(2)))
        d2 = dt.date(int(match.group(5)), m2, int(match.group(4)))
        return "%s to %s" % (d1.isoformat(), d2.isoformat())

    match = re.search("(%s)\s{0,}(\d{1,2})-\s{0,}(\d{1,2}) and (%s)\s+(\d{1,2})-\s{0,}(\d{1,2})[,.;]{0,1}\s+(\d{4})" % (month_re, month_re), date)
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

def in_visits(filename):
    """Grab US State Department lists of visits to the US by foreign
    heads of state and dump them to a CSV file."""
    out = csv.writer(open(filename, 'w'))
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
                    print "Skipping: %s" % str(row)
                    continue
                visitor = clean(cols[1].find(text=non_empty))
                country = clean(cols[2].find(text=non_empty))
                description = clean(cols[3].find(text=non_empty))
                out.writerow([date, country, visitor, description])

def get_text(elem):
    str = ""
    for text in elem.findAll(text=True):
        str += text
    return str

def out_visits(url, filename):
    """Grab US State Department lists of visits by the President and the
    Secretary of State to foreign countries."""
    out = csv.writer(open(filename, 'w'))
    out.writerow(['date', 'country', 'city', 'visitor', 'description'])

    list = BeautifulSoup(urllib2.urlopen(url).read())

    for link in list.find('div', id='body-row02').findAll('a'):
        visitor = link.string.strip()

        visit_list = BeautifulSoup(urllib2.urlopen(link['href']).read())

        if visitor in ['Condoleezza Rice', 'George W. Bush']:
            # New style
            for visit in visit_list.findAll('tr'):
                if not (visit.td and visit.td.p and visit.td.p.string):
                    continue
                date = parse_date(clean(visit.td.p.string))
                if not date:
                    continue

                country = clean(get_text(visit.findAll('td')[1].p))
                city = clean(get_text(visit.findAll('td')[2].p))
                description = clean(get_text(visit.findAll('td')[3].p))
                out.writerow([date, country, city, visitor, description])
        else:
            for visit in visit_list.find('div', id='centerblock').findAll('p'):
                if len(visit.contents) < 5:
                    continue

                date = parse_date(clean(visit.find(text=True)))
                if not date:
                    print "Skipping: %s" % str(visit)
                    continue

                country = clean(visit.findAll(text=True)[1])

                if len(visit.contents) == 7:
                    city = clean(visit.findAll(text=True)[2])
                    description = clean(visit.findAll(text=True)[3])
                else:
                    city = ""
                    description = clean(visit.findAll(text=True)[2])

                #print date
                out.writerow([date, country, city, visitor, description])

if __name__ == "__main__":
    in_visits("incoming_visits.csv")
    out_visits("http://www.state.gov/r/pa/ho/c1792.htm",
               "./presidential_visits.csv")
    out_visits("http://www.state.gov/r/pa/ho/trvl/ls/index.htm",
               "./secretary_visits.csv")
