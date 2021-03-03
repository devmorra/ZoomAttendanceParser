import sys
import tkinter as tk
import csv
import copy
import datetime
from datetime import datetime
from datetime import timedelta



# end-goal - have Zoom API export meeting reports to S3 bucket
# set up lambda function which takes in the report
# exports a parsed report to google drive & sends an email to the instructor(s)
# exports attendance to salesforce (most fuzzy part, can't find a lot of documentation on salesforce attendance API)

# general logic:
# read list of learners and their aliases from a file, potentially from salesforce later (probably not)
# based on name in the log, associate the line with a learner based off aliases
# if it's an unrecognized alias, keep track of it
# create dictionary with key of alias, value of associated student
# perhaps it can later be assigned to a learner, and update the learner file directly
# load log file
# scan log file line by line
# for each learner that now has lines assigned to it, determine the timeframes they were present in the class
# https://stackoverflow.com/questions/3096953/how-to-calculate-the-time-interval-between-two-time-strings
# split timeframes up
# if the learner logs in past the class start time plus a leniency threshold, mark tardy
# if the learner logs less than a threshold of minutes during the whole call, mark absent
# if the learner's time attended is beneath the duration of the meeting minus a tardy leniency threshold, mark tardy
# >>> potentially send an email to the learners if they're marked late or tardy?
#

class Timeframe:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.duration = end - start
    def recalcDuration(self):
        self.duration = self.end - self.start
    def __lt__(self, other):
        # used for sorting the timeframes
        return self.start < other.start


class Attendee:
    def __init__(self, timeFormat, parser):
        self.name = ''
        self.parser = parser  # "parent" parser object, to pull info about the breaks from
        self.aliases = []
        self.lines = []
        self.timeframes = []
        self.hrtimeframes = []      # debug
        self.timeframescopy = []    # debug
        self.hrtimeframescopy = []  # debug
        self.timeFormat = timeFormat
        self.firstLogin = "HH:MM:SSAM/PM"
        self.timeInCall = timedelta()
        self.status = ''  # present, tardy, or absent - should tardy be split between late join and missing > threshold?

    def loadFromLine(self, line):
        splitLine = line.split("=")
        self.name = splitLine[0]
        # self.aliases = \
        aliasList = splitLine[1].split(",")
        for alias in aliasList:
            alias = alias.replace("\n", "").strip().lower()
            self.aliases.append(alias)
        self.aliases.append(self.name.lower())


    def addTimeFrame(self, login, logout):
        self.timeframes.append(Timeframe(login, logout))


    def sortTimeFrames(self):
        self.timeframes = sorted(self.timeframes)  # https://docs.python.org/3/howto/sorting.html


    def mergeOverlappingTimeframes(self):
        i = 0
        # check frame 0 and frame 1
        # if merged, remove old frame 1, check frame 0 and new frame 1
        # if not merged, move to checking frame 1 and 2
        # repeat
        self.timeframescopy = copy.deepcopy(self.timeframes)
        while i < len(self.timeframes) - 1:
            # year, month, day, hour, minute, second
            f1 = self.timeframes[i]
            f1start = f1.start
            f1end = f1.end
            f2 = self.timeframes[i+1]
            f2start = f2.start
            f2end = f2.end
            # if the timeframes overlap
            x = (f2start < f1end)
            y =(f2end > f1end)
            if f2start < f1end:
                # print(f"Merged \n{f1.start.strftime('%H:%M:%S')} - {f1.end.strftime('%H:%M:%S')} with
                # \n{f2.start.strftime('%H:%M:%S')} - {f2.end.strftime('%H:%M:%S')}",end=" ")
                if f2end > f1end:
                    self.timeframes[i].end = f2end
                # self.timeframes[i][1] = self.timeframes[i+1][1]
                # print(f"to new frame \n{self.timeframes[i].start.strftime('%H:%M:%S')}
                # - {self.timeframes[i].end.strftime('%H:%M:%S')} for {self.name}")
                self.timeframes[i].recalcDuration()
                del self.timeframes[i+1]
            else:
                i += 1

    def createHumanReadableTFs(self):
        # for debug purposes, perhaps for use in the google sheet
        for tf in self.timeframes:
            self.hrtimeframes.append([tf.start.strftime('%H:%M:%S'), tf.end.strftime('%H:%M:%S')])
        for tf in self.timeframescopy:
            self.hrtimeframescopy.append([tf.start.strftime('%H:%M:%S'), tf.end.strftime('%H:%M:%S')])

    def calculateTimeInCall(self):
        self.sortTimeFrames()
        self.mergeOverlappingTimeframes()
        if len(self.timeframes) > 0:
            self.firstLogin = self.timeframes[0].start
        for timeframe in self.timeframes:
            # a = timeframe.end
            # b = timeframe.start
            # tfduration = timeframe.end - timeframe.start
            self.timeInCall += timeframe.duration

    # unused?
    def setLines(self, lines):
        self.lines = lines


    def getLines(self):
        return self.lines


class Parser:

    def __main__(self):
        pass

    def __init__(self, timeFormat):
        self.attendees = []
        self.unrecognizedAttendees = []
        self.aliasDictionary = {}
        self.timeFormat = timeFormat
    def readCSV(self, path):
        with open(path, newline='') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile,dialect)
    def loadAttendeesAndAliasFromPath(self, path):
        # read list of learners and their aliases from a file, potentially from salesforce later (probably not)
        # stores attendees in self.attendees
        # also sets up the alias dictionary to associate the attendees with their aliases
        file = open(path, "r")
        lines = file.readlines()
        for line in lines:
            a = Attendee(self.timeFormat, self)
            a.loadFromLine(line)
            self.attendees.append(a)
            for alias in a.aliases:
                self.aliasDictionary[alias] = a


    def loadMeetDataFromPath(self, path):
        file = open(path, "r")
        lines = file.readlines()  # load lines and remove the first line which doesn't contain useful data
        sessions = lines[1:]
        for line in sessions:
            # in the meeting file:
            # [0] = Attendee alias
            # [1] = email, if applicable
            # [2] = login time
            # [3] = logout time
            # [4] = time in minutes
            # [5] = Host or not, no = host/co-host, yes = attendee
            splitline = line.split(",")
            if splitline[5] == "Yes\n" or splitline[5] == "Yes":  # only track attendance for guests, not hosts
                alias = splitline[0].lower()
                # grab only the "HH:MM:SS AM/PM"
                loginTime = datetime.strptime(splitline[2], self.timeFormat)
                logoutTime = datetime.strptime(splitline[3], self.timeFormat)
                # if splitline[2].split(" ")[2] == "PM":
                #     loginTime = datetime.strptime(splitline[2].split(" ")[1], self.timeFormat)
                # else:
                #     loginTime = datetime.strptime(splitline[2].split(" ")[1], self.timeFormat)
                # if splitline[3].split(" ")[2] == "PM":
                #     logoutTime = datetime.strptime(splitline[3].split(" ")[1], self.timeFormat)
                # else:
                #     logoutTime = datetime.strptime(splitline[3].split(" ")[1], self.timeFormat)

                recognizedPair = self.recognizedAlias(alias) # this is kinda weird and ugly
                if recognizedPair[0]:
                #if alias in self.aliasDictionary:  # faster but less comprehensive
                    self.aliasDictionary[recognizedPair[1]].addTimeFrame(loginTime, logoutTime)
                else:
                    # track unrecognized alias and its timeframe
                    uAttendee = Attendee(self.timeFormat, self)
                    uAttendee.name = alias
                    self.aliasDictionary[alias] = uAttendee
                    self.unrecognizedAttendees.append(uAttendee)
    def recognizedAlias(self, alias):
        for a in self.aliasDictionary:
            if a in alias:
                return [True, a]
        return [False, "unrecognized"]


    # interaction will probably be done through google sheets
    # class MainApplication(tk.Frame):
    #     def __init__(self, parent, *args, **kwargs):
    #         tk.Frame.__init__(self, parent, *args, **kwargs)
