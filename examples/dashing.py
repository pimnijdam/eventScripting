'''
Created on Mar 10, 2013

@author: pim
'''
from senselet.core import Event, eventExpression, eventMethod
from senselet.events import commonsense
from senselet.events import senseapi
import json
import requests
import datetime
from operator import itemgetter


credentials = json.load(open("credentials.json"))
api = senseapi.SenseAPI()
if not api.AuthenticateSessionId(credentials["me"]["user"], senseapi.MD5Hash(credentials["me"]["password"])):
    print("Couldn't login: ".format(api.getResponse()))
session = commonsense.Session(api)
me = session.me()

#widgetBaseUrl = "http://pimdashboard.herokuapp.com:80/widgets/"
widgetBaseUrl = "http://localhost:3030/widgets/"
oauthToken = "YOUR_AUTH_TOKEN"
@eventExpression("toWidget")
def toWidget(date,value, widget):
    body = {"auth_token": oauthToken, "value": value}
    requests.post(widgetBaseUrl+widget, data=json.dumps(body))
    return value

@eventExpression("karmaToWidgetList")
def karmaToWidgetList(date, value, widget):
    items = []
    x=json.loads(value)
    x = sorted(iter(x.items()), key=itemgetter(1), reverse=True)
    for (user, karma) in x:
        items.append({"label":user,"value":karma})
    body = {"auth_token": oauthToken, "items": items}
    requests.post(widgetBaseUrl+widget, data=json.dumps(body))
    return value

bigBang = datetime.datetime.fromtimestamp(0)
me.event().sensor("karma (QA)").description("sense-android-library").karmaToWidgetList("karma-android-lib").realTime(30, bigBang).makeItSo()
me.event().sensor("karma (QA)").description("commonsense-rest").karmaToWidgetList("karma-rest").realTime(30, bigBang).makeItSo()
me.event().sensor("karma (QA)").description("aim").karmaToWidgetList("karma-aim").realTime(30, bigBang).makeItSo()
#me.event().sensor("daily activity time").attach(lambda d, x: round(float(x) / 60)).toWidget("time_active").realTime(30, bigBang).makeItSo()
#me.event().sensor("daily work time").attach(lambda d, x: round(float(x) / 3600)).toWidget("time_at_sense").realTime(30, bigBang).makeItSo()