'''
Created on Mar 10, 2013

@author: pim
'''
from github import Github, GithubException
from senselet.core import Event, eventExpression, eventMethod
from senselet.events import commonsense
from senselet.events import senseapi
import copy
import time
import datetime
import json

#setup
credentials = json.load(open("credentials.json"))
g = Github(credentials["github_token"])
api = senseapi.SenseAPI()
if not api.AuthenticateSessionId(credentials["me"]["user"], senseapi.MD5Hash(credentials["me"]["password"])):
    print("Couldn't login: ".format(api.getResponse()))
session = commonsense.Session(api)
me = session.me()


#define a generator to yield github issues
def githubIssues(repos,state="all", since=None):
    if since is None:
        for issue in repos.get_issues(state=state, sort="updated", direction="asc"):
            yield (issue.updated_at,issue)
    else:
        for issue in repos.get_issues(state=state, sort="updated", direction="asc", since=since):
            yield (issue.updated_at,issue)

def realtimeGithubIssues(repos,state="all",since=None,interval=60):
    lastDate = since
    while True:
        for (date,issue) in githubIssues(repos,state,since=lastDate):
            lastDate = date
            yield (date,issue)
        time.sleep(interval)    

@eventExpression("onPullRequest")
def onPullRequest(date,value):
    return value if value.pull_request.html_url is not None else None

@eventExpression("karmaPoints")
def karmaAdjustment(date,issue):
    #-1 for creator, +1 for closer
    return [(issue.user.login,-1), (issue.closed_by.login,1)]

@eventMethod("accumulateEach")
def accumulateEach(self):
    """
        Ugly hack, TODO: use a forEach() eventMethod preceding accumulate(). Not implemented yet
    """
    state = {}
    def accumulate(date,value,state):
        for (user,adjustment) in value:
            if user not in state:
                state[user] = 0
            state[user] += adjustment
        return copy.deepcopy(state)
    self.attach(accumulate, state)


#For each repository define events
for repos in g.get_user().get_orgs()[0].get_repos():
    sensorId = session.createSensorOnce("karma (QA)", repos.name, "integer")
    karmaRule = Event(inputData=realtimeGithubIssues(repos,"closed")).onPullRequest().karmaPoints().accumulateEach().saveToSensor(session, sensorId).makeItSo()