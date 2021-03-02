import sys
import tkinter as tk
import csv
import copy
import datetime
from datetime import time
from datetime import timedelta

# try:
#     droppedFile = sys.argv[1]
# except IndexError:
#     print("Please drag and drop the attendance ")
# print(droppedFile)
# #readCSV(droppedFile)
# input("")

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
# subtract break times and lunch from their attendance time as some learners log out during those times especially lunch
# if the learner logs in past the class start time plus a leniency threshold, mark tardy
# if the learner logs less than a threshold of minutes during the whole call, mark absent
# if the learner's time attended is beneath the duration of the meeting minus a tardy leniency threshold, mark tardy
# >>> potentially send an email to the learners if they're marked late or tardy?
#




class Attendee:
    def __init__(self):
        self.name = ''
        self.aliases = []
        self.lines = []
        self.timeframes = []
        self.timeframescopy = []
        self.timeFormat = "%I:%M:%S"
        self.firstLogin = "HH:MM:SSAM/PM"
        self.timeInCall = 0
        self.status = ''  # present, tardy, or absent - should tardy be split between late join and missing > threshold?

    def loadFromLine(self, line):
        s = ''
        splitLine = line.split("=")
        self.name = splitLine[0]
        # self.aliases = \
        aliasList = splitLine[1].split(",")
        for alias in aliasList:
            alias = alias.replace("\n", "").strip().lower()
            self.aliases.append(alias)
        self.aliases.append(self.name.lower())
    def addTimeFrame(self, login, logout):
        self.timeframes.append([login, logout])
    def sortTimeFrames(self):
        self.timeframes = sorted(self.timeframes, key=lambda time: time[0])  # https://docs.python.org/3/howto/sorting.html
    def mergeOverlappingTimeframes(self):
        i = 0
        # check frame 0 and frame 1
        # if merged, remove old frame 1, check frame 0 and new frame 1
        # if not merged, move to checking frame 1 and 2
        # repeat
        self.timeframescopy = copy.deepcopy(self.timeframes)
        while i < len(self.timeframes) - 1:  # not sure if this is the correct criteria, we'll see
            # year, month, day, hour, minute, second
            f1 = self.timeframes[i]
            f1start = f1[0]
            f1end = f1[1]
            f2 = self.timeframes[i+1]
            f2start = f2[0]
            f2end = f2[1]
            if f2start < f1end and f2end > f1end:  # if the timeframes overlap and frame 2's end is further than f1's end
                print(f"Merged {f1} with {f2}",end=" ")
                self.timeframes[i][1] = self.timeframes[i+1][1]
                print(f"to new frame {self.timeframes[i]} for {self.name}")
                del self.timeframes[i+1]
            else:
                i += 1


    def calculateTimeInCall(self):
        # self.mergeOverlappingTimeframes(self)
        pass


        # to check for overlapping logins in the case of multiple devices
        # store all login ranges, sort them by start time
        # compare end time of last range with start time of the next range
        # if they overlap, subtract the time they overlap from their time in the call
        # since it was counted twice and subtracted once they're still counted as there during that time

        # OR? check if end time of one timeframe overlaps with the beginning of another.
        # If it does, merge them into a new timeframe and remove the old timeframes
        # eg: 9:00 - 9:30 + 9:10 - 9:40 becomes 9:00-9:40
        # this one seems better

        # use the timeframes they were in the class to calculate how long they were in
        # use logins, a pair of the time they logged in with the time they logged out
        # ex: [[9:30AM, 10:30AM],[11:45AM, 4:00PM]]

        # for loginPair in timeframes:
        #     login = loginPair[0]
        #     logoff = loginPair[1]
        #     self.timeInCall += datetime.strptime(logoff, timeFormat) \
        #     - datetime.strptime(login, timeFormat)

    def setLines(self, l):
        self.lines = l
    def getLines(self):
        return self.lines

class Parser:

    def __main__(self):
        pass

    def __init__(self):
        self.attendees = []
        self.unknown = []
        self.aliasDictionary = {}
        self.timeFormat = "%I:%M:%S"
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
            a = Attendee()
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
                loginTime = datetime.datetime.strptime(splitline[2].split(" ")[1], self.timeFormat).time() # gross
                if splitline[2].split(" ")[2] == "PM":
                    loginTime = time(loginTime.hour+12,loginTime.minute,loginTime.second)
                logoutTime = datetime.datetime.strptime(splitline[3].split(" ")[1], self.timeFormat).time()#  + splitline[3].split(" ")[2]
                if splitline[3].split(" ")[2] == "PM":
                    logoutTime = time(logoutTime.hour+12,logoutTime.minute,logoutTime.second)

                recognizedPair = self.recognizedAlias(alias) # this is kinda weird and ugly
                if recognizedPair[0]:
                #if alias in self.aliasDictionary:  # faster but less comprehensive
                    self.aliasDictionary[recognizedPair[1]].addTimeFrame(loginTime, logoutTime)
                else:
                    # track unknown alias and its timeframe
                    self.unknown.append([alias, loginTime, logoutTime])
    def recognizedAlias(self, alias):
        for a in self.aliasDictionary:
            if a in alias:
                # print(f"{alias} recognized as {a}")
                return [True, a]
        # print(f"{alias} not recognized!!!!!@$?!@$%?!@%?!@")
        return [False, "unknown"]



    # class MainApplication(tk.Frame):
    #     def __init__(self, parent, *args, **kwargs):
    #         tk.Frame.__init__(self, parent, *args, **kwargs)
    def calcInClassTime(self, attendee):
        # subtract break times and lunch from their attendance time as some learners log out during those times especially lunch
        # if the learner logs in past the class start time plus a leniency threshold, mark tardy
        # if the learner logs less than a threshold of minutes during the whole call, mark absent
        # if the learner's time attended is beneath the duration of the meeting minus a tardy leniency threshold, mark tardy
        # >>> potentially send an email to the learners if they're marked late or tardy?
        #for line in attendee.lines
        pass