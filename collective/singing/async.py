import datetime

import persistent
import persistent.list
from zope import interface
from zope import component
from zope.app.component.hooks import getSiteManager

class IQueue(interface.Interface):
    pass

class Queue(persistent.Persistent):
    interface.implements(IQueue)

    def __init__(self):
        self.pending = persistent.list.PersistentList()
        self.finished = persistent.list.PersistentList()

    def process(self):
        num = len(self.pending)
        for job in self.pending:
            job()
            self.pending.remove(job)
            self.finished.append(job)
        return num

class Job(persistent.Persistent):
    executed = None
    title = u''

    def __init__(self, fun, *args, **kwargs):
        self._fun = fun
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        self.value = self._fun(*self._args, **self._kwargs)
        self.executed = datetime.datetime.now()

def get_queue(name):
    queue = component.queryUtility(IQueue, name)
    if queue is None:
        queue = Queue()
        sm = getSiteManager()
        sm.registerUtility(queue, provided=IQueue, name=name)
    return queue
