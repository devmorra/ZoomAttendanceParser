from __future__ import print_function
import os.path
import gspread
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
        spreadsheet = self.gc.open_by_key(spreadsheetID)
        worksheet = spreadsheet.worksheet(worksheetTitle)
        numAttendeesRange = "A2"
        #numAttendeesRange = "Attendees!"
        maxAliasesRange = "B2"
        numAttendees = int(worksheet.get(numAttendeesRange)[0][0])
        maxAliases = int(worksheet.get(maxAliasesRange)[0][0])
        nameAliasMin = gspread.utils.rowcol_to_a1(3, 1)
        nameAliasMax = gspread.utils.rowcol_to_a1(numAttendees + 2, maxAliases + 2)
        nameAndAliasRange = f"{gspread.utils.rowcol_to_a1(3, 1)}:{gspread.utils.rowcol_to_a1(numAttendees + 2, maxAliases + 2)}"
        # f"A3:{self.alphabet[2 + maxAliases - 1]}{numAttendees + 2}"
        nameAndAliasData = worksheet.get(nameAndAliasRange)
        for entry in nameAndAliasData:
            entry.pop(1)  # remove the number of aliases
        end = timer()
        print(end - start)
        return nameAndAliasData


    def getCredentials(self, pathToServiceAccountFile):
        # https://developers.google.com/identity/protocols/oauth2/service-account#python
        pass
        #return service_account.Credentials.from_service_account_file(pathToServiceAccountFile, scopes=self.SCOPES)



    def getSheetData(self, spreadsheetID, worksheetTitle, range):

        # Call the Sheets API
        if self.spreadsheet == None or self.spreadsheet.id != spreadsheetID:
            self.spreadsheet = self.gc.open_by_key(spreadsheetID)
        if self.worksheet == None or self.worksheet.title != worksheetTitle:
            worksheet = self.spreadsheet.worksheet(worksheetTitle)
        cellData = worksheet.get(range)
        return cellData
        #result = self.sheet.values().get(spreadsheetId=spreadsheetID,
        #                            range=range).execute()
        #return result.get('values', [])
        #print(values)
        # input("")
        # if not values:
        #     print('No data found.')
        # else:
        #     print('Name, Major:')
        #     for row in values:
        #         # Print columns A and E, which correspond to indices 0 and 4.
        #         print('%s, %s' % (row[0], row[4]))

# gsh = GoogleSheetsHandler()