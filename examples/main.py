'''
Created on Feb 17, 2013

@author: pim
'''

from senselet.events import commonsense
from senselet.events import senseapi
from senselet.location import Position
import json
import math
from  senselet.core import eventMethod, eventExpression, eventAction 
from datetime import timedelta

from subprocess import call
credentials = json.load(open("credentials.json"))

#define our own condition

@eventMethod("isIdle")
def isIdle(self):
    self.sensor("acceleration")
    def isIdle(date, jsonValue):
        value = json.loads(jsonValue)
        x,y,z = float(value.get("x-axis")), float(value.get("y-axis")), float(value.get("z-axis"))
        
        magnitude = math.sqrt(x**2+y**2+z**2)
        return magnitude < 2
    self.attach(isIdle)
    
@eventExpression("isAbove")
def isAbove(date,value, threshold):
    return value > threshold

@eventMethod("isAggresionDetected")
def isAggresionDetected(self):
    self.sensor("noise_sensor").isAbove(70)
    
@eventAction("speak")
def speak(msg):
    #TODO: properly escape value or use a pipe from python directly to festival
    call('echo "{}" | festival --tts'.format(msg), shell=True)
    

def timeoutDemo(user1,user2):
    senseHQ = Position(address="Lloydstraat 5, Rotterdam, Netherlands")
    
    #define when a timeout is needed
    user1IsAtSense = user1.event().isNear(senseHQ)
    user2IsAtSense = user2.event().isNear(senseHQ)
    needTimeout = user1IsAtSense.andEvent(user2IsAtSense).andEvent(user1.event().isAggresionDetected()).forTime(60).onBecomeTrue()
    
    #define action upon timeout
    needTimeout.printMsg("Houston we have a problem!")
    
    #event to cooldown
    user1IsCool = user1.event().isNear(senseHQ).isFalse().forTime(10*60)
    user2IsCool = user2.event().isIdle().forTime(10*60)

    cooledDownEvent = needTimeout.andEvent(user1IsCool).andEvent(user2IsCool)
    cooledDownEvent.onBecomeTrue().printMsg("Both users are cooled down.")
    
    #and make the events happen
    cooledDownEvent.makeItSo()


def main():
    senseHQ = Position(address="Lloydstraat 5, Rotterdam, Netherlands")
    #setup
    credentials = json.load(open("credentials.json"))
    api = senseapi.SenseAPI()
    if not api.AuthenticateSessionId(credentials["me"]["user"], senseapi.MD5Hash(credentials["me"]["password"])):
        print("Couldn't login: ".format(api.getResponse()))
        return
    session = commonsense.Session(api)
    me = session.me()
    jp = session.user("jp@sense-os.nl")
    
    
    
    #some location based triggers
    me.event().arrivedAt(senseHQ).speak("Elvis has left the building!").run()
    return
    me.event().departedFrom(senseHQ).printMsg("See you later, alligator!").makeItSo()
    
    

    #warning signal
    me.event().isNear(senseHQ).andEvent(jp.event().isNear(senseHQ)).onBecomeTrue().printMsg("Run for your live!").makeItSo()
    
    #trapped
    me.event().isNear(senseHQ).andEvent(jp.event().isNear(senseHQ)).forTime(timedelta(minutes=5)).onBecomeTrue().printMsg("You're trapped!").makeItSo()

    #pim.newEvent().realTime(30).isIdle().forTime(60*60).onBecomeTrue().sendNotification(deviceToken, "Couch potato!").makeItSo()

if __name__ == '__main__':
    #pim = User("pimtest2", credentials["pimtest2"]["password"])
    #jp = User("jp@sense-os.nl", credentials["jp@sense-os.nl"]["password"])
    #timeoutDemo(pim,jp)
    main()
