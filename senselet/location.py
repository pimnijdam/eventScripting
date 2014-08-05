'''
Created on Feb 17, 2013

@author: pim
'''
from math import radians, cos, sin, asin, sqrt
import json
from geopy import geocoders
from senselet.core import eventExpression, eventMethod
from datetime import timedelta
import requests

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = list(map(radians, [lon1, lat1, lon2, lat2]))
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    return km * 1000

class Position(object):
    def __init__(self, *args, **kwargs):
        address = kwargs.get("address")
        jsonvalue = kwargs.get("json")
        
        if len(args) == 2:
            self.lat = args[0]
            self.lon = args[1]
        elif address is not None:
            g = geocoders.OpenMapQuest()
            place, (lat, lon) = g.geocode(address)
            self.lat = lat
            self.lon = lon
        elif jsonvalue is not None:
            value = json.loads(jsonvalue)
            self.lat = float(value['latitude'])
            self.lon = float(value['longitude'])
        else:
            raise ValueError()
        
    def distance(self, pos2):
        return distance(self, pos2)
    
    def reverseGeoCode(self):
        return reverseGeoCode(self.lat, self.lon)
    
def reverseGeoCode(lat,lon):
    """
    Return (displayName, addresss, type)
    """
    response = requests.get("http://nominatim.openstreetmap.org/reverse?format=json&zoom=18&addressdetails=1&lat={}&lon={}".format(lat,lon))
    if not response:
        raise Exception("Reverse geo lookup failed")

    return (response.json()['display_name'], response.json()['address'], response.json()['osm_type'])
    

def distance(pos1,pos2):
        return haversine(pos1.lat,pos1.lon, pos2.lat,pos2.lon)

@eventExpression("distanceTo")
def distanceTo(date,value,refPos):
    x = json.loads(value)
    pos = Position(float(x['latitude']), float(x['longitude']))
    return distance(pos, refPos)

@eventMethod("onNear")
def onNear(self,pos,radius=200):
    self.sensor("position")
    def onNear(date,x,pos):
        return x if pos.distance(Position(json=x)) < radius else None
    self.attach(onNear)


@eventMethod("isNear")
def isNear(self,pos,radius=200):
    self.sensor("position")
    def isNear(date,value,pos):
        return pos.distance(Position(json=value)) < radius
    self.attach(isNear,pos)    

@eventMethod("arrivedAt")
def arriviedAt(self, location):
    self.isNear(location).onBecomeTrue()    

@eventMethod("departedFrom")
def departedFrom(self, location):
    return self.isNear(location).onBecomeFalse()

@eventExpression("addAddressDetails")
def addAddressDetails(date, value):
    displayName, address, addressType = reverseGeoCode(value['latitude'], value['longitude'])
    value['address'] = displayName
    value['address details'] = address
    value['address type'] = addressType
    return value

@eventMethod("onImmobile")
def onImmobile(self, radius=50):
    state = {}
    state['position'] = None
    def mobile(date,value):
        x = json.loads(value)
        pos = Position(float(x['latitude']), float(x['longitude']))
        if 'position' not in state:
            state['position'] = pos
            return None
        if pos.distance(state['position']) < radius:
            return value
        else:
            state['position'] = pos
            return None
    self.attach(mobile,state)
