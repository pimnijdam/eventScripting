'''
Created on Mar 7, 2013

@author: pim
'''
from  senselet.core import eventMethod, eventExpression
from datetime import time as dayTime, timedelta
import senselet
from senselet.events import commonsense
import datetime
import json
from senselet.events import senseapi

credentials = json.load(open("credentials.json"))
api = senseapi.SenseAPI()
if not api.AuthenticateSessionId(credentials["me"]["user"], senseapi.MD5Hash(credentials["me"]["password"])):
    print("Couldn't login: ".format(api.getResponse()))
session = commonsense.Session(api)
me = session.me()

#define our own condition
@eventExpression("isAbove")
def isAbove(date, value, threshold):
    return value > threshold
       
@eventMethod("sumDailyValue")
def sumDaylyValue(self):
    state={}
    state['value'] = 0
    state ['lastDay'] = None
    def addValue(date, value, state):
        today = date.date()
        if today == state['lastDay']:
            state['value'] += value
        else:
            #another day, reset count
            state['value'] = value
        state['lastDay'] = today
        return state['value']
    self.attach(addValue, state)

bigBang=datetime.datetime.fromtimestamp(0)

#coaching for activity
me.event().isIdle().forTime(timedelta(hours=1)).onBecomeTrue().onTimeIsBetween(dayTime(11), dayTime(21)).sendMail("pim@sense-os.nl", "Get up", "Move! you lazy couch potato.").realTime(30).makeItSo()

activityCountId = session.createSensorOnce("daily activity time", "daily activity time", "integer")
me.event().isActive().timeTrue().sumDailyValue().saveToSensor(activityCountId).realTime(30, fromDate=bigBang).makeItSo()

me.event().sensor("daily activity time").isAbove(45 * 60).onBecomeTrue().sendMail("pim@sense-os.nl", "Goal reached", "You've reached your goal of one 45 minutes of activity today!").realTime(30).makeItSo()
me.event().isActive().forTime(timedelta(minutes=15)).onBecomeTrue().sendMail("pim@sense-os.nl", "Goal reached", "You reached your goal of 15 minutes continuous activity.").realTime(30).makeItSo()

#coaching for work
senseHQ = senselet.location.Position(address="Lloydstraat 5, Rotterdam, Netherlands")
workTimeId = session.createSensorOnce("daily work time", "@sense", "integer")
me.event().isNear(senseHQ).timeTrue().sumDailyValue().saveToSensor(workTimeId).realTime(30, fromDate=bigBang).makeItSo()
me.event().sensor("daily work time").isAbove(9 * 60 * 60).onBecomeTrue().sendMail("pim@sense-os.nl", "Time to relax", "Go home, you've really worked enough for today.").realTime(30).makeItSo()