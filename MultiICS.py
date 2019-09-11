#!/usr/bin/env python3

from flask import Flask, request, Response, send_file
import requests
import os
import sys
import azure.mgmt.batchai.models.azure_blob_file_system_reference
import xmltodict, json
from lxml import etree

# name the flask app
#app = Flask(__name__)

#@app.route("/", methods=['GET'])
def GetEventsRequest():
    """ Handles the flask request
    """
    nameprefix = request.args.get('namePrefix')
    dateStart = request.args.get('nameprefix')
    dateEnd = request.args.get('dateEnd')


def GetMultiEventICSFile(namePrefix, synonymPrefix, dateStart, dateEnd):
    """ Get a list of events based on a search criteria nd return the events in a single ICS calendar file.
    """

    url = "https://eventor.orienteering.asn.au/api/events?fromDate={0}&toDate={1}".format(dateStart, dateEnd)
    
    apikey =  os.environ.get('EventorAPIKey')

    response = requests.get(
        url=url,
        headers={
               'User-Agent': 'eventor-bot',
               'ApiKey': apikey
            },
    )


    # loop through all the events limiting to the name
    #o = xmltodict.parse(response.content)
    #json.dumps(o)
    
    root = etree.fromstring(response.content)

    if (synonymPrefix):
        xpath = "/EventList/Event[(starts-with(Name,'{0}')) or (starts-with(Name,'{1}'))]/EventId".format(namePrefix, synonymPrefix)
    else:
        xpath = "/EventList/Event[starts-with(Name,'{0}')]/EventId".format(namePrefix)

    eventids = root.xpath(xpath)
    print("Searched and found {0} events".format(len(eventids)))


    from ics import Calendar

    mainCal= None
    for eventid in eventids:
        icsURL = "https://eventor.orienteering.asn.au/Events/ICalendar/{0}".format(eventid.text)
        c = Calendar(requests.get(icsURL).text)
        if mainCal is None:
            mainCal = c
        else:
            for event in c.events: 
                mainCal.events.add(event)

    print("Writing combined {0} events".format(len(mainCal.events)))        
    with open('{0}.ics'.format(namePrefix), 'w',newline='') as f:
        f.writelines(mainCal)
        print(str(mainCal))

    # create a new file
    #return send_file(filename, mimetype='text/calendar')

if __name__ == '__main__':
    #app.run(debug=True,host='0.0.0.0',port=80)
    sys.path.insert(0, os.path.abspath('..'))

    #from clint.arguments import Args
    #from clint.textui import puts, colored, indent

    import argparse

    parser = argparse.ArgumentParser(description='Example with non-optional arguments')

    parser.add_argument('namePrefix', action="store")
    parser.add_argument('-s', '--synonym', action="store", dest="synonymPrefix", help='alternative name for event')
    parser.add_argument('startDate', action="store")
    parser.add_argument('endDate', action="store")


    args = parser.parse_args()
    GetMultiEventICSFile(args.namePrefix, args.synonymPrefix, args.startDate, args.endDate)
