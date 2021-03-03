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
        self.isValid = True


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
        self.lastLogoff = "HH:MM:SSAM/PM"
        self.timeInCall = timedelta()
        self.status = ''  # present, tardy, or absent - should tardy be split between late join and missing > threshold?


    def removeBreakOverlaps(self, breaks):
        # calling timeframes sessions here
        # if a session overlaps a break
        # case 1: no overlap, session remain untouched

        # compare each break to each session
        for br in breaks:
            i = 0
            while i < len(self.timeframes):
                tf = self.timeframes[i]
                if tf.isValid:
                    if br.start > tf.start and br.start < tf.end:  # if the break starts during the session
                        # case 2: break contained entirely within session, split session into 3 sessions
                        preBreakTf = Timeframe(tf.start, br.start) # this is done in both cases
                        if br.end < tf.end:  # if the break ends before the session does ex. they stay logged in during break
                            # session 1: original start - break start: valid
                            # session 2: break start - break end: invalid
                            # session 3: break end - original end: valid
                            breakTf = br
                            postBreakTf = Timeframe(br.end, tf.end)
                            self.timeframes[i] = preBreakTf
                            self.timeframes.insert(i + 1, postBreakTf)
                        # case 3: session tail end overlaps with break
                        # session start untouched, session end = break start
                        else:  # elif br.end > tf.end:  # if the break ends after their session
                            self.timeframes[i] = preBreakTf
                            # since the pre-break session got shortened already, it should be all good
                            pass
                    # case 4: session head overlaps with break
                    elif br.start < tf.start and br.end > tf.start:
                        # session becomes end of break to previous end of session
                        newTf = Timeframe(br.end, tf.end)
                        self.timeframes[i] = newTf
                    elif br.start < tf.start and br.end > tf.end:
                        self.timeframes.pop(i)

                        # session start untouched, session end = break start


        # case : session entirely within a break
                if br.start < tf.start and br.end > tf.end:
                    tf.isValid = False
        # set to invalid
        # if breakStart > tfStart and
                i += 1
        pass


    def loadFromLine(self, line: str):
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


    # add some grace period management so gaps of <1m are also merged to make it cleaner
    def mergeOverlappingTimeframes(self):
        i = 0
        # check frame 0 and frame 1
        # if merged, remove old frame 1, check frame 0 and new frame 1
        # if not merged, move to checking frame 1 and 2
        # repeat
        while i < len(self.timeframes) - 1:
            # year, month, day, hour, minute, second
            f1 = self.timeframes[i]
            f1start = f1.start
            f1end = f1.end
            f2 = self.timeframes[i+1]
            f2start = f2.start
            f2end = f2.end
            tdelta = f2start - f1end
            # if the timeframes overlap
            #if f2start < f1end:
            if tdelta < timedelta(minutes=1):
                # print(f"Merged \n{f1.start.strftime('%H:%M:%S')} - {f1.end.strftime('%H:%M:%S')} with
                # \n{f2.start.strftime('%H:%M:%S')} - {f2.end.strftime('%H:%M:%S')}",end=" ")
                if f2end > f1end:
                    self.timeframes[i].end = f2end
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
        self.timeframescopy = copy.deepcopy(self.timeframes)  # debug
        self.mergeOverlappingTimeframes()
        self.removeBreakOverlaps(self.parser.breaks)
        if len(self.timeframes) > 0:
            self.firstLogin = self.timeframes[0].start
            self.lastLogoff = self.timeframes[len(self.timeframes) - 1].end
        for timeframe in self.timeframes:
            if timeframe.isValid == True:
                self.timeInCall += timeframe.duration
        self.createHumanReadableTFs()

    # unused?
    def setLines(self, lines: [str]):
        self.lines = lines


    def getLines(self):
        return self.lines


class Parser:

    def __main__(self):
        pass

    def __init__(self, timeFormat: str, meetingdata: str, aliasdata: str):
        self.attendees = []
        self.unrecognizedAttendees = []
        self.breaks = []
        self.logDate = ''
        self.timeFormat = timeFormat
        self.aliasDictionary = {}

        self.lateArrivalLeniency = 0
        self.earlyLeaveLeniency = 0
        self.breakReturnLeniency = 0
        self.startTime = ''
        self.endTime = ''

        self.loadAliasData(aliasdata)
        self.loadMeetingData(meetingdata)
        self.loadBreaks()

    def loadBreaks(self):
        # hard coded for now
        # in the future it should be pulled from google sheets cells
        breakformat = "%m/%d/%Y %I:%M:%S %p"
        # manual data for now
        break1 = Timeframe(datetime.strptime("02/24/2021 10:30:00 AM", breakformat), datetime.strptime("02/24/2021 10:45:00 AM", breakformat))
        break2 = Timeframe(datetime.strptime("02/24/2021 12:30:00 PM", breakformat), datetime.strptime("02/24/2021 01:35:00 PM", breakformat))
        break3 = Timeframe(datetime.strptime("02/24/2021 02:30:00 PM", breakformat), datetime.strptime("02/24/2021 02:45:00 PM", breakformat))
        self.breaks.append(break1)
        self.breaks.append(break2)
        self.breaks.append(break3)

    # def readCSV(self, path):
    #     with open(path, newline='') as csvfile:
    #         dialect = csv.Sniffer().sniff(csvfile.read(1024))
    #         csvfile.seek(0)
    #         reader = csv.reader(csvfile,dialect)

    def loadAliasData(self, data):
        for line in data:
            a = Attendee(self.timeFormat, self)
            a.loadFromLine(line)
            self.attendees.append(a)
            for alias in a.aliases:
                self.aliasDictionary[alias] = a

    def loadMeetingData(self, data):  # load lines and remove the first line which doesn't contain useful data
        if "Meeting ID" in data[0]:
            self.logDate = datetime.strptime(data[1].split(",")[2], self.timeFormat)
        userDataStart = 0
        for line in data:
            if "Name (Original Name)" in line:
                break
            userDataStart += 1
        if self.logDate == '':
            self.logDate = datetime.strptime(data[userDataStart + 1].split(",")[2], self.timeFormat)
        sessions = data[userDataStart:]
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
                recognizedPair = self.recognizedAlias(alias)  # grabs if the alias is recognized or not and what the a
                if recognizedPair[0]:
                    self.aliasDictionary[recognizedPair[1]].addTimeFrame(loginTime, logoutTime)
                else:
                    # track unrecognized alias and its timeframe
                    uAttendee = Attendee(self.timeFormat, self)
                    uAttendee.name = alias
                    if alias not in uAttendee.aliases:
                        uAttendee.aliases.append(alias)
                    uAttendee.addTimeFrame(loginTime, logoutTime)
                    self.aliasDictionary[alias] = uAttendee
                    self.unrecognizedAttendees.append(uAttendee)

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
            # matches partial aliases ex: Aliases "John" and "Doe" would both recognize "John Doe"
            if a in alias:
                return [True, a]
        return [False, "unrecognized"]


    # interaction will probably be done through google sheets instead of a GUI application
    # class MainApplication(tk.Frame):
    #     def __init__(self, parent, *args, **kwargs):
    #         tk.Frame.__init__(self, parent, *args, **kwargs)
