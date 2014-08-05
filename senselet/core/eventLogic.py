"""
Define the logic operators to combine multiple event rules.
"""

import queue, threading
from operator import itemgetter
from . import event
from functools import reduce

def andEvent(self, other):
    def andInputs():
        for tuples in combineGenerators([self.values,other.values]):
            value = reduce(lambda x,y: x and y[1] == True, tuples, True)
            date = max(tuples, key=itemgetter(0))[0]
            #and with None returns None, skip None since we only want data after we have data from all streams
            if value is None:
                continue
            yield (date, value)
    return event.Event(inputData=andInputs)
event.Event.andEvent = andEvent

def orEvent(self, other):
    def orInputs():
        for tuples in combineGenerators([self.values,other.values]):
            value = reduce(lambda x,y: x or y[1] == True, tuples, False)
            date = max(tuples, key=itemgetter(0))[0]
            #False or None returns None, True or None returns true
            if value is None:
                continue
            yield (date, value)
    return event.Event(inputData=orInputs)
event.Event.andEvent = andEvent



"""
Combines multiple generators into a single tuples string. Upon an input the generator outputs the last value for every input.
"""        
def combineGenerators(genlist):
    n=len(genlist)
    dataQueue = [queue.Queue() for i in range(n)]
    values = [(None,None) for i in range(n)]
    buf = [(None,None) for i in range(n)]
    timestamps = [0 for i in range(n)]
    stop = False
    def run_one(source,i):
        for item in source(): dataQueue[i].put(item)

    def run_all():
        thrlist = []
        #create individual threads for the inputs
        i=0
        for source in genlist:
            t = threading.Thread(target=run_one,args=(source,i,))
            t.start()
            thrlist.append(t)
            i+=1

        for t in thrlist: t.join()
        for i in range(len(dataQueue)): dataQueue[i].put(StopIteration)

    def getNext():
        """
        This function is quite hard to grasp. It uses a 2-stage approach to make sure data is outputted in-order.
        Data is outputted on each point. There's a lag of n-1 items, with n the number of inputs.
        Note that for in-order we're interested in new items with the lowest timestamp. This is important to grasp!
        1. read a value from the QUEUES into the buffer from the input with the lowest timestamp
        2. now update the values with the value from the BUFFER
        Nota bene: on items from multiple inputs with the EXACT same timestamp it outputs a new value FOR EACH INPUT where ONLY ONE of the values is updated!
        """
        #block on the queue with the lowest timestamp (or None)
        i = timestamps.index(min(timestamps))
        x = dataQueue[i].get()
        #ouch, some stupid stopping code. TODO: improve
        if x is StopIteration:
            buf[i] = StopIteration
            return
        #end ouch
        
        date,value = x[0],x[1]
        
        timestamps[i] = date
        buf[i] = (date,value)
        
        #now that the buffer is updated, update the values
        i = buf.index(min(buf, key=itemgetter(0)))
        values[i] = buf[i]

    
    threading.Thread(target=run_all).start()
    while True:
        #block until there's something to process
        getNext()

        yield values
        #TODO: when to stop? now we stop as soon as one input stops.
        if buf.count(StopIteration) > 0:
            return