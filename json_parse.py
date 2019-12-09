#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import schedule
import time
import datetime
import requests


t_sched = dict()

dataDir = 'data'
classId = '954'
className = ''


#date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')

def oneMinute():
    print(datetime.datetime.now().ctime())

def getJSON(url):
    """getJSON receives the Untis schedule as JSON and returns it as text
    url is the url"""
    #payload = {'cookie': 'schoolname="_ZW1pbC1wb3NzZWhsLXNjaHVsZQ=="'}
    headers = {'content-type': 'application/json', 'accept': 'application/json', 'cookie': 'schoolname="_ZW1pbC1wb3NzZWhsLXNjaHVsZQ=="'}
    r = requests.get(url, headers=headers)
    return r.text

def getMonday():
    """ getMonday returns the date of Monday for this week. next week if weekend"""
    today = datetime.date.today()
    if today.weekday() >= 4:
        return today + datetime.timedelta(days=7-today.weekday())
    else:
        return today
    
def parseJSON(file):
    """
    parseJSON parses the untis json response and returns a dict.
    It takes either a string or a file as input.
    """

    elements = dict({'subjects':dict(), 'rooms':dict()})
    lessons = dict()
    subs = dict()
    t_sched = dict()
    if type(file) == str:
        data = json.loads(file)
    else:
        data = json.load(file)

    if not 'data' in data:
        t_sched['Error'] = {'msg':'no data'}
        return t_sched

    for el in data["data"]["result"]["data"]['elements']:
        raume = elements['subjects']
        facher = elements['rooms']
        if el['type'] == 3:
            fach = {'type':el['type'],'name':el['displayname'],'longName':el['longName']}
            raume.update({el['id'] : fach})
        elif el['type'] == 4:
            raum = {'type':el['type'],'name':el['displayname'],'longName':el['longName']}
            facher.update({el['id'] : raum})
        
        elif el['type'] == 1:
            className = el['displayname']


    for p in data["data"]["result"]["data"]["elementPeriods"][classId]:
        lesson = {'lessonId': p['lessonId'], 'date': p['date'], 'startTime': p['startTime'], 'endTime': p['endTime']}
        lesson.update(cellState = p['cellState'])

        for e in p['elements']: # for all elements in lesson
            
            if e['type'] == 4:
                lesson.update(roomName = elements['rooms'][e['id']]['name'])
            elif e['type'] == 3:
                lesson.update(prettyName = elements['subjects'][e['id']]['longName'])

        lessons.update({p['id'] : lesson})

        if p['cellState'] != 'STANDARD':
            subs.update({p['id'] : lesson})

    t_sched.update({'lessons' : lessons})
    t_sched.update({'subs' : subs})
    t_sched.update(name = className)
    t_sched.update(classId = classId)

    return t_sched

def printSubs(s):
    """ printSubs prints all lessons witch are not STANDARD.
    Pass in the subs dict. """
    for sub in s:
        date_time_obj = datetime.datetime.strptime(str(s[sub]['date']), '%Y%M%d')
        # print('Fach: {0}'.format(s[sub]['prettyName']))
        # print('-> Am: {0}'.format(date_time_obj.strftime('%d.%M.%Y')))
        # print('-> Grund: {0}'.format(s[sub]['cellState']))
        # print('*' * 10)
        print('am {0} faellt "{1}" aus! - {2}'.format(date_time_obj.strftime('%d.%M.%Y'), s[sub]['prettyName'], s[sub]['cellState'] ))

def findNext(s):
    """
    findNext returns a dict with the next lesson.
    Pass in the lessons dict.
    returning dict contains lessonID-> lessonId of the next lesson, second-> seconds until next lesson,
    datetime-> begin of next lesson
    """
    now = datetime.datetime.now()
    delta = datetime.timedelta(weeks=1)
    t_startTime = datetime.datetime
    lessonId = 0
    
    for sub in s:
        t_date = datetime.datetime.strptime(str(s[sub]['date']), '%Y%m%d') #s[sub]['date']
        if len(str(s[sub]['startTime'])) < 4:
            t = '0' + str(s[sub]['startTime'])
        else:
            t = str(s[sub]['startTime'])
            
        t_time = datetime.datetime.strptime(t, '%H%M').time() #s[sub]['date']
        t_next = datetime.datetime.combine(t_date,t_time)
        
        t_delta = t_next - now
        if t_delta < delta:
            delta = t_delta
            lessonId = sub
            t_startTime = t_time

    t_next = {'lessonId':lessonId, 'seconds': delta.seconds, 'datetime':t_startTime}
    return t_next

def main():

    # use saved json for testing
    with open(dataDir + "/mese_FEV19_nextweek.json", "r") as f:
        t_sched = parseJSON(f)


    # construct request URL:
    url = 'https://mese.webuntis.com/WebUntis/api/public/timetable/weekly/data?elementType=1&elementId=954&date={0}&formatId=1'.format(getMonday())

    # get all the data
    #t_sched = parseJSON(getJSON(url))
    if 'Error' in t_sched: # check for error and exit
        print("error: {0}".format(t_sched['Error']['msg']))
        exit()
        
    # save data to file
    with open(dataDir + '/t_sched.json', 'w') as outfile: # write t_sched to file
        json.dump(t_sched, outfile, indent=1)

    #print(json.dumps(t_sched, indent=1))
    #print(json.dumps(elements, indent=1))
    #print('Subs: {0}'.format(len(t_sched['subs'])))
    printSubs(t_sched['subs'])

    nextLesson = findNext(t_sched['lessons'])
    print('Die naechste Stunde ist "{0}" und beginnt um {1} Uhr'.format(t_sched['lessons'][nextLesson['lessonId']]['prettyName'], nextLesson['datetime'].strftime('%H:%M'))   )


    # print(oneMinute())
    # schedule.every(10).minutes.do(oneMinute)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

if __name__ == '__main__':
    main()