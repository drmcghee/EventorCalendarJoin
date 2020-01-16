#!/usr/bin/env python3

#from flask import Flask, request, Response, send_file
import requests
import os
import sys
#import xmltodict, json
from lxml import etree

# name the flask app - this is when I get the time to turn into a website
#app = Flask(__name__)
#@app.route("/", methods=['GET'])
# def GetEventsRequest():
#     """ Handles the flask request
#     """
#     nameprefix = request.args.get('namePrefix')
#     dateStart = request.args.get('nameprefix')
#     dateEnd = request.args.get('dateEnd')


def GetMultiEventICSFile(orgIds, namePrefix, synonymPrefix, locationPrefix,dateStart, dateEnd):
    """ Get a list of events based on a search criteria nd return the events in a single ICS calendar file.
    """

    if(orgIds):   
        print("Searching eventor for events between {0} and {1} for organisationIds {2}".format(dateStart,dateEnd, orgIds))
        url = "https://eventor.orienteering.asn.au/api/events?fromDate={0}&toDate={1}&organisationIds={2}".format(dateStart, dateEnd,orgIds)
    else:      
        print("Searching eventor for events between {0} and {1}".format(dateStart,dateEnd))
        url = "https://eventor.orienteering.asn.au/api/events?fromDate={0}&toDate={1}".format(dateStart, dateEnd)
    
    apikey =  os.environ.get('EventorAPIKey')

    response = requests.get(
        url=url,
        headers={
               'User-Agent': 'eventor-bot',
               'ApiKey': apikey
            },
    )
    ProcessXMLintoICS(response.content, namePrefix, synonymPrefix, locationPrefix)



def ProcessXMLintoICS(xmlstring, namePrefix, synonymPrefix, locationPrefix):
    # loop through all the events limiting to the name
    #o = xmltodict.parse(response.content)
    #json.dumps(o)
    
    root = etree.fromstring(xmlstring)
    alleventcount = int(root.xpath('count(/EventList/Event)'))
    print("A total of {0} events found for this period ".format(alleventcount))

    if (alleventcount==0):
        print("Exiting - No events to process")
    else:
        if (namePrefix):
            if (synonymPrefix):
                xpath = "/EventList/Event[(starts-with(Name,'{0}')) or (starts-with(Name,'{1}'))]/EventId".format(namePrefix, synonymPrefix)
            else:
                xpath = "/EventList/Event[starts-with(Name,'{0}')]/EventId".format(namePrefix)
        else:
            xpath = "/EventList/Event/EventId"

        eventids = root.xpath(xpath)
        eventcount = len(eventids)
        print("Found {0} events -- prefix {1} or synonym {2}".format(eventcount, namePrefix, synonymPrefix))

        if (eventcount==0):
            print("Exiting - No named events to process -- prefix {1} or synonym {2}".format(eventcount, namePrefix, synonymPrefix))
        else:
            ProcessEventsintoICS(root, xpath, eventcount, namePrefix, synonymPrefix, locationPrefix)

def ProcessEventsintoICS(root, xpath, eventcount, namePrefix, synonymPrefix, locationPrefix):
    # if no prefix then just look for location
    if (namePrefix):
        # also add the eventor message location if available
        if (synonymPrefix):
            xpath += " | /EventList/Event[(starts-with(Name,'{0}')) or (starts-with(Name,'{1}'))]/HashTableEntry[(Key='Eventor_Message') and contains(Value,'{2}') ]/Value".format(namePrefix, synonymPrefix, locationPrefix)
        else:
            xpath += " | /EventList/Event[starts-with(Name,'{0}')]/HashTableEntry[(Key='Eventor_Message') and contains(Value, '{1}'}) ]/Value".format(namePrefix, locationPrefix)
    else:
          xpath += " | /EventList/Event/HashTableEntry[(Key='Eventor_Message') and contains(Value, '{0}') ]/Value".format(locationPrefix)


    eventids = root.xpath(xpath)
    locCount = len(eventids)-eventcount
    print("Found {0} locations".format(locCount))

    # create a list of event locations
    eventdata = {}

    # for each event then add a location based on the eventid
    for eventid in eventids:
        if (eventid.tag=='EventId'):  
            eventdata[eventid.text] = ""
            lasteventid = eventid.text
        if (eventid.tag=="Value"):
            # default is no location
            location = "location unknown (not found in the eventor message)"
            # look for end of lines
            if "\n" in eventid.text:
                # split into lines looking for location
                eventormessagelines = eventid.text.split('\n')
                for line in eventormessagelines:
                    if (line.startswith(locationPrefix)):
                        location =  line.replace(locationPrefix,"")
                        break
            else:
                # look in the text for prefix
                if locationPrefix in eventid.text:
                    location = eventid.text.replace(locationPrefix,"")
            eventdata[lasteventid] = location    

    # now the locations are extracted properly add each location to an event in the calendar
    from ics import Calendar
    mainCal= None
    for key, value in eventdata.items():     
            # get the calendar from eventor
            icsURL = "https://eventor.orienteering.asn.au/Events/ICalendar/{0}".format(key)   
            print("Reading ICS file for event id {0}".format(key))  
            c = Calendar(requests.get(icsURL).text)

            # create main calendar if it doesn't exist
            if mainCal is None:
                mainCal = c
                for event in c.events: 
                    event.location = value
            else:
                for event in c.events: 
                    event.location = value
                    mainCal.events.add(event)
            # for the calendar to be used it must be published
            c.method = "PUBLISH"    
            # TODO: add in  X-WR-CALNAME e.g. "Sydney Summer Series Season 29 "Map Running Sydney"


    print("Writing combined {0} events".format(len(mainCal.events)))    

    if (namePrefix):
        filename = namePrefix
    else:
        filename = "OrganisationEvents"

    with open('{0}.ics'.format(filename), 'w',newline='') as f:
        f.writelines(mainCal)
        print(str(mainCal))

    # create a new file
    #return send_file(filename, mimetype='text/calendar')

if __name__ == '__main__':
    #app.run(debug=True,host='0.0.0.0',port=80)
    sys.path.insert(0, os.path.abspath('..'))

    import argparse

    parser = argparse.ArgumentParser(description='Arguments for eventor caldendar')

    parser.add_argument('-o', '--organisationIds', action="store", dest="orgIds", help='comma separated list fo organisationIds name for event')
    parser.add_argument('-p', '--prefix', action="store", dest='namePrefix', help='prefix of event name')
    parser.add_argument('-s', '--synonym', action="store", dest="synonymPrefix", help='alternative name for event')
    parser.add_argument('-l', '--location', action="store", dest="locationPrefix", help='identifier in the eventor message for location')
    parser.add_argument('startDate', action="store")
    parser.add_argument('endDate', action="store")


    args = parser.parse_args()
    GetMultiEventICSFile(args.orgIds, args.namePrefix, args.synonymPrefix, args.locationPrefix,args.startDate, args.endDate)
