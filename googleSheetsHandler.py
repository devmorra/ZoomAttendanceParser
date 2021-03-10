from __future__ import print_function
import os.path
import gspread
import gspread_formatting as gsf
from gspread_formatting import *
import numpy as np
from datetime import date
# from googleapiclient import discovery
# from google.oauth2 import service_account
import time
from timeit import default_timer as timer

class GoogleSheetsHandler:

    def __init__(self):
        start = timer()
        self.token = None
        # self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        # self.spreadSheetID = spreadsheetID
        # self.pathToServiceAccountFile =
        # self.credentials = self.getCredentials(self.pathToServiceAccountFile)
        # self.service = discovery.build('sheets', 'v4', credentials=self.credentials)
        self.gc = gspread.service_account(filename=os.path.abspath('client_secrets.json'))
        # self.getAttendeesAndAliasData(self.spreadSheetID)
        self.spreadsheet = None
        self.worksheet = None

        # end = timer()
        # totaltime = end - start
        # print(totaltime)

    def openSheet(self, spreadsheetID):
        self.spreadsheet = self.gc.open_by_key(spreadsheetID)


    def applyStandardFormatting(self, spreadsheetID, worksheetTitle, startTimeString):
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        breakConditionRule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('C:Z', self.worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition("TEXT_STARTS_WITH", ["Break"]),
                format=gsf.cellFormat(backgroundColor=gsf.color(0.70, 0.70, 0.70))  # should color break cells grey
            )
        )
        absentConditionRule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('B5:B', self.worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition("TEXT_EQ", ["0:00"]),  # "0:00" cells are absent
                format=gsf.cellFormat(backgroundColor=gsf.color(1, 0, 0))  # make them an angry red
            )
        )
        emptyFirstTimeframeRule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('C5:C', self.worksheet)],
            booleanRule=BooleanRule(
                # if there's no timeframe for the first one then keep it white instead of yellow
                condition=BooleanCondition("BLANK"),
                format=gsf.cellFormat(backgroundColor=gsf.color(1, 1, 1))  # white
            )
        )
        lateConditionRule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('C5:C', self.worksheet)],
            booleanRule=BooleanRule(
                # If the first timeframe doesn't have the start time in it, mark it yellow
                condition=BooleanCondition("TEXT_NOT_CONTAINS", [startTimeString]),
                format=gsf.cellFormat(backgroundColor=gsf.color(1, 1, 0))  # yellow
            )
        )
        onTimeConditionRule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('C5:C', self.worksheet)],
            booleanRule=BooleanRule(
                # if it does have the start time, mark it green
                condition=BooleanCondition("TEXT_STARTS_WITH", [startTimeString]),
                format=gsf.cellFormat(backgroundColor=gsf.color(0, 1, 0))  # green
            )
        )

        rules = get_conditional_format_rules(self.worksheet)
        rules.clear()
        # order is important, rule that is appended first takes priority
        rules.append(breakConditionRule)
        rules.append(absentConditionRule)
        rules.append(emptyFirstTimeframeRule)
        rules.append(lateConditionRule)
        rules.append(onTimeConditionRule)
        rules.save()
        self.autoResizeCells(self.spreadsheet.id, self.worksheet.id)


    def autoResizeCells(self, spreadsheetID, worksheetID):
        payload = {
            "requests": [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": worksheetID,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 30
                        }
                    }
                }
            ]
        }
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetID}:batchUpdate"
        self.gc.request("post", url, json=payload)


    def createAndSetSpreadsheet(self, folderID, spreadsheetTitle):
        try:
            self.spreadsheet = self.gc.open(spreadsheetTitle)
        except:
            self.spreadsheet = self.gc.create(spreadsheetTitle, folderID)
            print(f"Creating {spreadsheetTitle} in {folderID}")
            print(f"{self.spreadsheet.id} created")
            # print("Waiting 10s for spreadsheet to become active...")
            # time.sleep(10)
            # self.setSpreadsheet()


    def createAndSetWorksheet(self, spreadsheetID, worksheetTitle, index):
        try:
            self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        except:
            self.spreadsheet.add_worksheet(worksheetTitle, 100, 100, index)
            print(f"Adding {worksheetTitle} to {self.spreadsheet.id}")
            self.setWorksheet(worksheetTitle)


    def deleteSpreadSheet(self, spreadsheetID):
        self.gc.del_spreadsheet(spreadsheetID)


    def getAttendeesAndAliasData(self, spreadsheetID):
        worksheetTitle = "Attendees"
        start = timer()
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        # read formula values from spreadsheet to intelligently know which cells to read from
        # may not be necessary if the whole worksheet is read and parsed but this seems fine
        # does result in 2 extra API calls though
        numAttendeesRange = "A2"
        maxAliasesRange = "B2"
        numAttendees = int(self.worksheet.get(numAttendeesRange)[0][0])
        maxAliases = int(self.worksheet.get(maxAliasesRange)[0][0])
        nameAliasMin = gspread.utils.rowcol_to_a1(3, 1)
        nameAliasMax = gspread.utils.rowcol_to_a1(numAttendees + 2, maxAliases + 2)
        nameAndAliasRange = f"{nameAliasMin}:{nameAliasMax}"
        nameAndAliasData = self.worksheet.get(nameAndAliasRange)
        for entry in nameAndAliasData:
            entry.pop(1)  # remove the number of aliases
        end = timer()
        print(end - start)
        return nameAndAliasData


    def getMeetingsFromCentralSheet(self, centralSheetID):
        self.setSpreadsheetAndWorksheet(centralSheetID, "Form Responses 1")
        masterData = self.worksheet.get_all_values()[1:]
        return masterData


    def getStartEndBreakDict(self, spreadsheetID, logDate):
        dayOfWeek = logDate.weekday()
        monCol = "B"    # 0 = Monday: col B
        tuesCol = "C"   # 1 = Tuesday: col C
        wedCol = "D"    # 2 = Wednesday: col D
        thursCol = "E"  # 3 = Thursday: col E
        friCol = "F"    # 4 = Friday: col F
        satCol = "G"    # 5 = Saturday: col G
        sunCol = "H"    # 6 = Sunday: col H
        dayColumnList = [monCol, tuesCol, wedCol, thursCol, friCol, satCol, sunCol]
        startRow = 11
        endRow = 18
        targetRange = f"{dayColumnList[dayOfWeek]}{startRow}:{dayColumnList[dayOfWeek]}{endRow}"
        startEndBreakData = self.getRangeData(spreadsheetID, "Settings", targetRange)
        startEndBreakDict = {}
        startEndBreakDict['callStart'] = startEndBreakData[0][0]
        startEndBreakDict['callEnd'] = startEndBreakData[1][0]
        startEndBreakDict['b1start'] = startEndBreakData[2][0]
        startEndBreakDict['b1end'] = startEndBreakData[3][0]
        startEndBreakDict['b2start'] = startEndBreakData[4][0]
        startEndBreakDict['b2end'] = startEndBreakData[5][0]
        startEndBreakDict['b3start'] = startEndBreakData[6][0]
        startEndBreakDict['b3end'] = startEndBreakData[7][0]
        for key in startEndBreakDict:
            # zero-pad times that start with single digit hours
            if len(startEndBreakDict[key]) < 5:
                startEndBreakDict[key] = "0" + startEndBreakDict[key]
        return startEndBreakDict


    def getCredentials(self, pathToServiceAccountFile):
        # https://developers.google.com/identity/protocols/oauth2/service-account#python
        pass
        #return service_account.Credentials.from_service_account_file(pathToServiceAccountFile, scopes=self.SCOPES)


    def getRangeData(self, spreadsheetID, worksheetTitle, range):

        # Call the Sheets API
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        rangeData = self.worksheet.get(range)
        print(f"Grabbing data from {spreadsheetID}, {worksheetTitle}, {range}")
        return rangeData


    def getAllFromSheet(self, spreadsheetID, worksheetTitle):
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        return self.worksheet.get_all_values()


    def getCellData(self, spreadsheetID, worksheetTitle, cell):

        # Call the Sheets API
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        cellData = self.worksheet.get(cell)[0][0]
        return cellData


    def setSpreadsheet(self, spreadsheetID):
        if self.spreadsheet is None or self.spreadsheet.id != spreadsheetID:
            self.spreadsheet = self.gc.open_by_key(spreadsheetID)
            return self.spreadsheet
        # print(f"Spreadsheet set to {self.spreadsheet.id}")


    def setWorksheet(self, worksheetTitle):
        if self.worksheet is None or self.worksheet.title != worksheetTitle:
            self.worksheet = self.spreadsheet.worksheet(worksheetTitle)
            return self.worksheet
        # print(f"Worksheet set to {self.worksheet.title}")


    def setSpreadsheetAndWorksheet(self, spreadsheetID, worksheetTitle):
        self.setSpreadsheet(spreadsheetID)
        self.setWorksheet(worksheetTitle)


    def shareSheetToEmails(self, spreadsheetID, emails):
        self.setSpreadsheet(spreadsheetID)
        for email in emails:
            self.spreadsheet.share(email, "user", "writer", "True")
            print(f"{spreadsheetID} shared with {email}")


    def writeMatrixToCells(self, spreadsheetID, worksheetTitle, startCell, matrix):
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        self.worksheet.update(startCell, matrix)
        print(f"Data written to spreadsheet: {spreadsheetID}\nworksheet: {worksheetTitle}")
