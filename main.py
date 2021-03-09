# taken/adapted from https://github.com/billydh/zoom-reporting/blob/central/main.py

from zoomAttendanceParser import Parser  # , Attendee
from googleSheetsHandler import GoogleSheetsHandler
import os
import datetime
import calendar
from timeit import default_timer as timer

# from googl import Googl
from zoomRequest import ZoomRequester

# ZOOM_API_KEY = # os.environ.get("ZOOM_API_KEY")
# ZOOM_API_SECRET = # os.environ.get("ZOOM_API_SECRET")
# ZOOM_MEETING_ID = # os.environ.get("ZOOM_MEETING_ID")

# SERVICE_ACCOUNT_FILE = f".secrets/{os.listdir('.secrets')[0]}"
# SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"]
start = timer()

timeFormat = "%Y-%m-%dT%H:%M:%SZ"


secretContents = open(os.path.abspath("zoomSecrets.txt")).read().split(",")
gsh = GoogleSheetsHandler()
z = ZoomRequester(secretContents[0], secretContents[1])
ztoken = z.generate_jwt_token()


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



centralData = gsh.getMeetingsFromCentralSheet("1w_hveJ7vAscC6IV4-P0-ZjovewLCI-lEb3WMkYfag_Q")
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

    dateArray = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = datetime.datetime.today()
    todayIndex = datetime.datetime.today().weekday()
    todaysWeekday = dateArray[todayIndex]  # convert datetime number to string of the weekday
    if todaysWeekday in daysRunning:  # see if the class is run on that day
        outputTitle = f"{startOfWeekString(today)} - {endOfWeekString(today)} {cycleName} Attendance"
        aliasData = gsh.getAttendeesAndAliasData(spreadsheetID)
        meetingID = gsh.getCellData(spreadsheetID, "Settings", "A2").replace(" ", "")
        meetResponse = z.get_meeting_participants(meetingID)
        timeZoneOffset = int(gsh.getCellData(spreadsheetID,"Settings", "C9"))
        parser = Parser(timeFormat, timeZoneOffset, aliasData)
        parser.parseMeetingResponse(meetResponse)
        sebDict = gsh.getStartEndBreakDict(spreadsheetID, parser.logDate)
        parser.loadStartEndBreakDict(sebDict)
        parser.calculateAttendeesTimeInCall()
        # for attendee in parser.attendees:
        #     attendee.calculateTimeInCall()
        #     print(f"{attendee.name} in call for {attendee.timeInCall}, entered at {attendee.firstLogin}, left at {attendee.lastLogoff}")
        gsh.createAndSetSpreadsheet(folderID, outputTitle)
        outputID = gsh.spreadsheet.id
        worksheetTitle = f"{todaysWeekday} {today.strftime('%m/%d/%y')}"
        gsh.createAndSetWorksheet(outputID, worksheetTitle, todayIndex)
        gsh.worksheet.clear()
        # grab spreadsheetID based on title if it exists, if it doesn't exist, create it
        # folder settings should auto share it to the correct people
        # if sheet {todaysWeekday} doesn't exist in the spreadsheet, make it
        # if it does, select it
        # write the data

        # spreadsheet based on week
        # if the spreadsheet doesn't exist, make it
        # worksheet based on data
        # if the worksheet doesn't exist (it probably doesn't), add it
        gsh.writeMatrixToCells(outputID, worksheetTitle, "A1", parser.attendeesDataToMatrix())
        gsh.shareSheetToEmails(outputID, emails)


# parser.formatDataForCells

end = timer()
print(end - start)
print("Done")
