'''
Created on Feb 16, 2013

@author: pim
'''
import threading
import queue
import datetime
import traceback
"""
A proxy to facilitate some weird syntax. Probably a bad idea, don't count on this being around in the future.
"""
class Proxy(object):
    def __init__(self, proxied, default=None):
        self.proxied = proxied
        self.default = default

    def __getattr__(self, key):
        try:
            return getattr(self.proxied, key)
        except AttributeError:
            if self.default:
                self.default(key, allowMulti=True)
            return self 

"""
Wrapper for events 
"""
class Event(object):
    def __init__(self, inputData=None, continueOnException=True):
        self.inputData = inputData
        self._pipeline = []
        self._inputEvents = []
        self.continueOnException = continueOnException
    
    def attach(self, function, *args, **kwargs):
        self._pipeline.append((function, args, kwargs))
        return self
        

    """
    Invoked before actually running this event. This method is provided so it can be conveniently overridden by subclasses.
    """
    def _prepare(self):
        origin = self.inputData.__name__ if self.inputData is not None else "Unknown"
        structure =  "{}: {}".format("Event",origin)
        for (stage, args, kwargs) in self._pipeline:
            structure += " -> {}()".format(stage.__name__)
        print(structure)

    def _run(self):
        if self.inputData is None:
            raise Exception("No input data for event!")
                  
        for (date,value) in self.inputData:
            stopped = False
            for (stage, args, kwargs) in self._pipeline:
                try:
                    newValue = stage(date,value,*args, **kwargs)
                except Exception as e:
                    print("Exception in function {}:".format(stage.__name__))
                    print(traceback.format_exc())
                    if self.continueOnException:
                        break #continue with the next data point
                    raise
                if newValue is None:
                    stopped = True
                    break
                else:
                    value = newValue
            if stopped:
                continue

    def run(self):
        self._prepare()
        self._run()


    """
    DOESN"T WORK, THREAD IS NEVER STOPPED!
    Get values, reusing the run method, at the cost of an extra thread. 
    """
    def _never_stopping_values(self):
        q = queue.Queue()
        def queueWriter(date,value,state):
            q.put((date,value))
            return value
            
        self.attach(queueWriter)
        self.makeItSo()
        while True:
            item = q.get()
            if item is StopIteration: return
            yield item
    
    """
    Execute and yield values
    """
    def values(self):
        self._prepare()
        for (date,value) in self.inputData:
            stopped = False
            for (stage, args, kwargs) in self._pipeline:
                try:
                    newValue = stage(date,value,*args, **kwargs)
                except Exception as e:
                    print("Exception in function {}:".format(stage.__name__))
                    print(traceback.format_exc())
                    if self.continueOnException:
                        break #continue with the next data point
                    raise
                if newValue is None:
                    stopped = True
                    break
                else:
                    value = newValue
            if stopped:
                continue
            yield (date,value)
    
    """
    Execute the event in a thread
    """
    def makeItSo(self):
        self._prepare()
        t = threading.Thread(target=self._run)
        t.start()
        
"""
Decorator to provide some syntactic sugar. This decorator:
- patches the Event object with the function
- returns self to allow method chaining

example:

@eventMethod("isNear")
def isNear(self,referencePosition):
    self.distanceFrom(referencePosition)
    self.attach(lambda date,distance: distance < 100)

Event().isNear(referencePosition).otherFuncion()

Note that eventMethods are omnipotent, they can have state.

Trust me, the code is fine. Don't mess with it!
"""
def eventMethod(name):
    def wrap(f):
        def wrapped_f(self, *args,**kwargs):
            f(self, *args,**kwargs)
            return self
        print("Declaring method Event.{}".format(name))
        setattr(Event, name, wrapped_f)
        return wrapped_f
    return wrap

"""
Decorator to provide even more syntactic sugar. This decorator:
- patches the Event object with the name
- returns self to allow method chaining
- attaches the function to the Event pipeline

example:

@eventExpression("isNear")
def isNearFunction(date,value,referencePosition)
    return referencePosition.distanceTo(value) < 100

Event().isNear(referencePosition)
Note that eventExpressions are stateless

Trust me, the code is fine. Don't mess with it!
"""
def eventExpression(name):
    def wrap(f):
        def wrapped_f(self, *args, **kwargs):
            self.attach(f,*args, **kwargs)
            return self
        setattr(Event, name, wrapped_f)
        print("Declaring expression Event.{}".format(name))
        return wrapped_f
    return wrap

"""
Decorator to provide even more syntactic sugar. This decorator:
- patches the Event object with the name
- returns self to allow method chaining
- wraps the method in a function that retains the value to allow functions after the action to work on the same 

example:

@eventAction("sendChat")
def sendChat(date,value,msg)
    sendChatMessage("{}: {}".format(date,msg))
        
Event().sendChat("Hi there")
Note that eventActions don't transform the input

Trust me, the code is fine. Don't mess with it!
"""
def eventAction(name):
    def wrap(f):
        def wrapped_f(self, *args, **kwargs):
            def returnValueWrapper(date, value): 
                f(*args, **kwargs)
                return value
            self.attach(returnValueWrapper)
            return self
        setattr(Event, name, wrapped_f)
        print("Declaring action Event.{}".format(name))
        return wrapped_f
    return wrap

###  Basic 'on' events  ###
@eventMethod("onChanged")
def onChanged(self):
    def func(date,value,state):
        prev = state.get('value')
        changed = prev is None or value != prev
        state['value'] = value
        if changed:
            return value
        else:
            return None
        self.attach(func, {})

@eventMethod("onUnchanged")
def onUnhanged(self):
    def func(date,value,state):
        prev = state.get('value')
        changed = prev is None or value != prev
        state['value'] = value
        if changed:
            return None
        else:
            return value
        self.attach(func, {})
    
@eventMethod("onBecomeTrue")
def onBecomeTrue(self):
    state = {'prev':False}
    def onBecomeTrue(date,value,state):
        prev = state.get('prev')
        state['prev'] = value
        if value and not prev:
            return value
        else:
            return None
    self.attach(onBecomeTrue,state)
    
@eventMethod("onBecomeFalse")
def onBecomeFalse(self):
    state = {'prev':True}
    def onBecomeFalse(date,value,state):
        prev = state.get('prev')
        state['prev'] = value
        if not value and prev:
            return value
        else:
            return None
    self.attach(onBecomeFalse,state)

@eventExpression("onTrue")
def onTrue(date,value):
    return True if value else None

###  basic time related conditions  ###

@eventMethod("forTime")
def forTime(self, time):
    if not isinstance(time, datetime.timedelta):
        raise TypeError("Argument should be a datetime.timedelta object")
    def forTime(date,value,state):
        since = state.get("since")
        if value:
            if since is not None:
                return date - since >= time
            else:
                state["since"] = date
        elif since is not None:
            del state["since"]
        return False
    self.attach(forTime, {})

###  Boolean logic  ###

@eventExpression("isFalse")
def isFalse(date,value):
    return not value

###  Actions  ###

@eventMethod("do")
def do(self, func, *args, **kwargs):
    def wrapper(date,value):
        func(*args, **kwargs)
    self.attach(wrapper)

@eventAction("printMsg")
def printMsg(msg):
    print(msg)

#helps to debug
@eventExpression("printValue")
def printValue(date, value):
    print("{}:{}".format(date, value))
    return value

@eventMethod("accumulate")
def accumulate(self):
    """
        Accumulate value. Behaviour depends on input:
        TODO: make the code work like the comment
        - float and int are summed
        - for a set each element is summed
        - for an array with numbers each element is summed
    """
    state = {"value":0}
    def accumulate(date,value,state):
        state["value"] += value
        return state["value"]
    self.attach(accumulate, state)
    
@eventMethod("timeTrue")
def timeTrue(self):
    state={"last":None}
    def timeTrue(date, value,state):
        ret = 0
        if value and state["last"] is not None:
            ret = (date - state["last"]).total_seconds()
        state["last"] = date if value else None
        return ret
    self.attach(timeTrue,state)
