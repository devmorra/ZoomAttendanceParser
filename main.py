# taken/adapted from https://github.com/billydh/zoom-reporting/blob/central/main.py

from zoomAttendanceParser import Parser  # , Attendee
from googleSheetsHandler import GoogleSheetsHandler
import os
import datetime
import sys
import time
import json

from timeit import default_timer as timer

# from googl import Googl
from zoomRequest import ZoomRequester


def startOfWeek(date):
    dayNum = date.weekday()
    delta = datetime.timedelta(days=-dayNum)
    weekStart = date + delta
    return weekStart

def endOfWeek(date):
    dayNum = date.weekday()
    delta = datetime.timedelta(days=6 - dayNum)
    weekEnd = date + delta
    return weekEnd


def startOfWeekString(date):
    day = startOfWeek(date)
    startString = day.strftime("%m/%d/%y")
    return startString


def endOfWeekString(date):
    day = endOfWeek(date)
    endString = day.strftime("%m/%d/%y")
    return endString


# ZOOM_API_KEY = # os.environ.get("ZOOM_API_KEY")
# ZOOM_API_SECRET = # os.environ.get("ZOOM_API_SECRET")
# ZOOM_MEETING_ID = # os.environ.get("ZOOM_MEETING_ID")

# SERVICE_ACCOUNT_FILE = f".secrets/{os.listdir('.secrets')[0]}"
# SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"]
start = timer()

timeFormat = "%Y-%m-%dT%H:%M:%SZ"


secretContents = open(os.path.abspath("zoomSecrets.txt")).read().split(",")
z = ZoomRequester(secretContents[0], secretContents[1])
ztoken = z.generate_jwt_token()



with open (os.path.abspath("centralSheetID.txt"), "r") as f:
    centralSheetID = f.read()

gsh = GoogleSheetsHandler()
centralData = gsh.getMeetingsFromCentralSheet(centralSheetID)
try:
    print(sys.argv[1], sys.argv[2])
except:
    print("Please provide the date and either 'central' or the number of the row that should be parsed from the central sheet")

try:
    targetDate = datetime.datetime.strptime(sys.argv[1], "%m-%d-%y")
except:
    print("Invalid date format provided.\n Please use MM-DD-YY with zero-padding")
    exit()

dateArray = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

for line in centralData:
    # data from sheet for this particular cycle
    cycleName = line[1]
    emails = line[2].split(",")
    for email in emails:
        email.replace(" ", "")
    folderID = line[3]
    spreadsheetID = line[4]
    endDate = line[5]
    daysRunning = line[6]


    # today = datetime.datetime.today()
    # todayIndex = datetime.datetime.today().weekday()
    # todaysWeekday = today.strftime("%A")  # convert datetime number to string of the weekday
    targetDateWeekday = targetDate.strftime("%A")

    #if todaysWeekday in daysRunning:  # see if the class is run on that day
    if targetDateWeekday in daysRunning:
        # set desired spreadsheet name to the given week + the cycle name + Attendance
        outputTitle = f"{startOfWeekString(targetDate)} - {endOfWeekString(targetDate)} {cycleName} Attendance"
        aliasData = gsh.getAttendeesAndAliasData(spreadsheetID)
        meetingID = gsh.getCellData(spreadsheetID, "Settings", "A2").replace(" ", "")
        meetResponse = z.get_meeting_participants(meetingID)
        timeZoneOffset = int(gsh.getCellData(spreadsheetID, "Settings", "C9"))
        parser = Parser(timeFormat, timeZoneOffset, aliasData, meetResponse)
        parser.parseMeetingResponse()

        sebDict = gsh.getStartEndBreakDict(spreadsheetID, parser.logDate)
        parser.loadStartEndBreakDict(sebDict)
        parser.calculateAttendeesTimeInCall()
        if parser.logDate == targetDate.date():
            startTimeString = parser.startTime.strftime("%H:%M")
            gsh.createAndSetSpreadsheet(folderID, outputTitle)
            outputID = gsh.spreadsheet.id
            worksheetTitle = f"{targetDateWeekday} {targetDate.strftime('%m/%d/%y')}"
            logWorksheetTitle = f"{targetDateWeekday} {targetDate.strftime('%m/%d/%y')} log"
            gsh.createAndSetWorksheet(outputID, worksheetTitle, None)
            gsh.worksheet.clear()
            gsh.writeMatrixToCells(outputID, worksheetTitle, "A1", parser.attendeesDataToMatrix())
            gsh.applyStandardFormatting(outputID, worksheetTitle, startTimeString)

            gsh.createAndSetWorksheet(outputID, logWorksheetTitle, None)
            gsh.worksheet.clear()
            gsh.writeMatrixToCells(outputID, logWorksheetTitle, "A1", parser.meetingResponseToMatrix())
            gsh.autoResizeCells(outputID, logWorksheetTitle)


            currentWorksheetTitles = []
            # remove the default Sheet1 if it exists
            for ws in gsh.spreadsheet.worksheets():
                currentWorksheetTitles.append(ws.title)
            if "Sheet1" in currentWorksheetTitles:
                gsh.spreadsheet.del_worksheet(gsh.setWorksheet("Sheet1"))
            print("Sleeping for 100 seconds to avoid API rate limit")
            time.sleep(100)
        else:
            print("No log found for specified date, skipping.")
        #else:
            #gsh.writeMatrixToCells(outputID, worksheetTitle, "A1", [["No meeting found on this date."]])
        # gsh.shareSheetToEmails(outputID, emails)
    else:
        print(f"{cycleName} does not have class on {dateArray[targetDate.weekday()]}")



# parser.formatDataForCells

end = timer()
print(end - start)
print("Done")
