from __future__ import print_function
import os.path
import gspread
from datetime import date
# from googleapiclient import discovery
# from google.oauth2 import service_account
from timeit import default_timer as timer

class GoogleSheetsHandler:

    def __init__(self):
        start = timer()
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
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


    def getAttendeesAndAliasData(self, spreadsheetID):
        worksheetTitle = "Attendees"
        start = timer()
        # used for defining ranges. Not meant to exceed past column Z
        if self.spreadsheet is None or self.spreadsheet.id != spreadsheetID:
            self.spreadsheet = self.gc.open_by_key(spreadsheetID)
        if self.worksheet is None or self.worksheet.title != worksheetTitle:
            self.worksheet = self.spreadsheet.worksheet(worksheetTitle)
        numAttendeesRange = "A2"
        #numAttendeesRange = "Attendees!"
        maxAliasesRange = "B2"
        numAttendees = int(self.worksheet.get(numAttendeesRange)[0][0])
        maxAliases = int(self.worksheet.get(maxAliasesRange)[0][0])
        nameAliasMin = gspread.utils.rowcol_to_a1(3, 1)
        nameAliasMax = gspread.utils.rowcol_to_a1(numAttendees + 2, maxAliases + 2)
        nameAndAliasRange = f"{gspread.utils.rowcol_to_a1(3, 1)}:{gspread.utils.rowcol_to_a1(numAttendees + 2, maxAliases + 2)}"
        # f"A3:{self.alphabet[2 + maxAliases - 1]}{numAttendees + 2}"
        nameAndAliasData = self.worksheet.get(nameAndAliasRange)
        for entry in nameAndAliasData:
            entry.pop(1)  # remove the number of aliases
        end = timer()
        print(end - start)
        return nameAndAliasData

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


    def setSpreadsheet(self, spreadsheetID):
        if self.spreadsheet is None or self.spreadsheet.id != spreadsheetID:
            self.spreadsheet = self.gc.open_by_key(spreadsheetID)


    def setWorksheet(self, worksheetTitle):
        if self.worksheet is None or self.worksheet.title != worksheetTitle:
            self.worksheet = self.spreadsheet.worksheet(worksheetTitle)


    def setSpreadsheetAndWorksheet(self, spreadsheetID, worksheetTitle):
        self.setSpreadsheet(spreadsheetID)
        self.setWorksheet(worksheetTitle)


    def getRangeData(self, spreadsheetID, worksheetTitle, range):

        # Call the Sheets API
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        rangeData = self.worksheet.get(range)
        return rangeData


    def getCellData(self, spreadsheetID, worksheetTitle, cell):

        # Call the Sheets API
        self.setSpreadsheetAndWorksheet(spreadsheetID, worksheetTitle)
        cellData = self.worksheet.get(cell)[0][0]
        return cellData
