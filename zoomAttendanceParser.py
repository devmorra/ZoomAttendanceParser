import sys
import tkinter as tk
import csv
from datetime import datetime
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
    def calculateTimeInCall(self):
        timeFormat = "%m/%d/%Y %I:%M:%S %p"
        # use the timeframes they were in the class to calculate how long they were in
        # use logins, a pair of the time they logged in with the time they logged out
        # ex: [[9:30AM, 10:30AM],[11:45AM, 4:00PM]]

        # for loginPair in logins:
        #     login = loginPair[0]
        #     logoff = loginPair[1]
        #     self.timeInCall += datetime.strptime(logoff, timeFormat) \
        #     - datetime.strptime(login, timeFormat)

        # to check for overlapping logins in the case of multiple devices
        # store all login ranges, sort them by start time
        # compare end time of last range with start time of the next range
        # if they overlap, subtract the time they overlap from their time in the call
        # since it was counted twice and subtracted once they're still counted as there during that time
        pass
    def setLines(self, l):
        self.lines = l
    def getLines(self):
        return self.lines

class Parser:

    def __main__(self):
        pass

    def __init__(self):
        self.attendees = []
        self.aliasDictionary = {}
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
        lines = file.readlines()[1:] # load lines and remove the first line which doesn't contain useful data

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