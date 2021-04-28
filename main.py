# taken/adapted from https://github.com/billydh/zoom-reporting/blob/central/main.py

from zoomAttendanceParser import Parser  # , Attendee
from googleSheetsHandler import GoogleSheetsHandler
import os
import datetime
import sys
import time
import logging

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


start = timer()
logFilePath = f"logs/"
logger = logging.getLogger("Main logger")
timeFormat = "%Y-%m-%dT%H:%M:%SZ"


secretContents = open(os.path.abspath("zoomSecrets.txt")).read().split(",")
z = ZoomRequester(secretContents[0], secretContents[1])
ztoken = z.generate_jwt_token()




with open (os.path.abspath("centralSheetID.txt"), "r") as f:
    centralSheetID = f.read().replace("\n", "")

gsh = GoogleSheetsHandler()
centralData = gsh.getMeetingsFromCentralSheet(centralSheetID)
try:
    print(sys.argv[1], sys.argv[2])
except:
    print("Please provide the date or 'today' and either 'central' or the number of the row that should be parsed from the central sheet")

if sys.argv[1] == "today":
    tdate = datetime.datetime.today()
else:
    try:
        tdate = datetime.datetime.strptime(sys.argv[1], "%m-%d-%y")
    except:
        print("Invalid date format provided.\n Please use MM-DD-YY with zero-padding")
        exit()

dateArray = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def parseFromCentralSheetRow(rowdata, sheetHandler, zoomRequester, targetDate):
    cycleName = rowdata[1]
    emails = rowdata[2].split(",")
    for email in emails:
        email.replace(" ", "")
    folderID = rowdata[3]
    spreadsheetID = rowdata[4]
    endDate = rowdata[5]
    splitEndDate = endDate.split("/")
    paddedEndDate = ''
    for section in splitEndDate:
        if len(section) == 1:
            paddedEndDate += "0" + section + "/"
        else:
            paddedEndDate += section + "/"
    paddedEndDate = paddedEndDate[:-1]
    endDate = datetime.datetime.strptime(paddedEndDate, "%m/%d/%Y")
    # datetime.datetime.strptime(rowdata[5],)
    print(f"Looking for meeting for {cycleName} on {targetDate}")
    daysRunning = rowdata[6]
    if targetDate < endDate:
        targetDateWeekday = targetDate.strftime("%A")
        if targetDateWeekday in daysRunning:
            # set desired spreadsheet name to the given week + the cycle name + Attendance
            outputTitle = f"{startOfWeekString(targetDate)} - {endOfWeekString(targetDate)} {cycleName} Attendance"
            aliasData = sheetHandler.getAttendeesAndAliasData(spreadsheetID)
            meetingID = sheetHandler.getCellData(spreadsheetID, "Settings", "A2").replace(" ", "")
            timeZoneOffset = int(sheetHandler.getCellData(spreadsheetID, "Settings", "C9"))
            offsetDelta = datetime.timedelta(hours=timeZoneOffset)

            pastMeetings = zoomRequester.getPastMeetings(meetingID)
            meetingsToParse = []
            for meeting in pastMeetings:
                meeting['date_time'] = datetime.datetime.strptime(meeting['start_time'], timeFormat)
                meeting['date'] = (meeting['date_time'] + offsetDelta).date()
                if meeting['date'] == targetDate.date():
                    meetingsToParse.append(meeting["uuid"])

            if len(meetingsToParse) >= 1:
                aggregateParticipantData = []
                for mID in meetingsToParse:
                    print(f"Meeting uuid:'{mID}' found on {targetDate}")
                    participantData = zoomRequester.get_meeting_participants(mID)
                    for pdata in participantData:
                        aggregateParticipantData.append(pdata)
                aggregateParticipantData.sort(key=lambda i: i['join_time'])
                parser = Parser(timeFormat, timeZoneOffset, aliasData, aggregateParticipantData)
                parser.parseMeetingResponse()

                sebDict = sheetHandler.getStartEndBreakDict(spreadsheetID, parser.logDate)
                parser.loadStartEndBreakDict(sebDict)
                parser.calculateAttendeesTimeInCall()
                startTimeString = parser.startTime.strftime("%H:%M")
                sheetHandler.createAndSetSpreadsheet(folderID, outputTitle)
                outputID = sheetHandler.spreadsheet.id
                worksheetTitle = f"{targetDateWeekday} {targetDate.strftime('%m/%d/%y')}"
                logWorksheetTitle = f"{targetDateWeekday} {targetDate.strftime('%m/%d/%y')} log"
                sheetHandler.createAndSetWorksheet(outputID, worksheetTitle, None)
                sheetHandler.worksheet.clear()
                sheetHandler.writeMatrixToCells(outputID, worksheetTitle, "A1", parser.attendeesDataToMatrix())
                sheetHandler.applyStandardFormatting(outputID, worksheetTitle, startTimeString)
                sheetHandler.createAndSetWorksheet(outputID, logWorksheetTitle, None)
                sheetHandler.worksheet.clear()
                sheetHandler.writeMatrixToCells(outputID, logWorksheetTitle, "A1", parser.meetingResponseToMatrix())
                logWorksheetID = sheetHandler.worksheet.id
                sheetHandler.autoResizeCells(outputID, logWorksheetID)

                currentWorksheetTitles = []
                # remove the default Sheet1 if it exists
                for ws in sheetHandler.spreadsheet.worksheets():
                    currentWorksheetTitles.append(ws.title)
                if "Sheet1" in currentWorksheetTitles:
                    sheetHandler.spreadsheet.del_worksheet(gsh.setWorksheet("Sheet1"))
                print("Sleeping for 100 seconds to avoid API rate limit")
                time.sleep(100)
            else:
                print("No log found for specified date, skipping.")
            # else:
            # gsh.writeMatrixToCells(outputID, worksheetTitle, "A1", [["No meeting found on this date."]])
            # gsh.shareSheetToEmails(outputID, emails)
        else:
            print(f"{cycleName} does not have class on {dateArray[targetDate.weekday()]}")
            print("Waiting 6s to avoid Zoom API rate limit")
            time.sleep(6)
    else:
        print(f"{cycleName} ended before {endDate.strftime('%M/%D/%Y')}, skipping")


try:
    if sys.argv[2] == "all":
        for line in centralData:
            parseFromCentralSheetRow(line, gsh, z, tdate)
        # data from sheet for this particular cycle
    else:
        try:
            targetRow = int(sys.argv[2])
            if 2 <= targetRow < len(centralData) + 2:
                parseFromCentralSheetRow(centralData[targetRow - 2], gsh, z, tdate)
            else:
                print("Please enter a row number that is contained on the central sheet, or 'all'")
        except:
            print("Please enter a row number that is contained on the central sheet or 'all'")



except Exception as e:
    logging.error("Exception occurred", exc_info=True)

# parser.formatDataForCells

end = timer()
print(end - start)
print("Done")
