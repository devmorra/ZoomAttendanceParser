from __future__ import print_function
import os.path
from googleapiclient import discovery
from google.oauth2 import service_account
from timeit import default_timer as timer

class GoogleSheetsHandler:

    def __init__(self):
        start = timer()
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.token = None
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        # self.spreadSheetID = spreadsheetID
        self.pathToServiceAccountFile = os.path.abspath('client_secrets.json')
        self.credentials = self.getCredentials(self.pathToServiceAccountFile)
        self.service = discovery.build('sheets', 'v4', credentials=self.credentials)
        self.sheet = self.service.spreadsheets()
        # self.getAttendeesAndAliasData(self.spreadSheetID)
        end = timer()
        totaltime = end - start
        print(totaltime)


    def getAttendeesAndAliasData(self, spreadsheetID):
          # used for defining ranges. Not meant to exceed past column Z
        numAttendeesRange = "Attendees!A2"
        maxAliasesRange = "Attendees!B2"
        preReq1 = timer()
        numAttendees = int(self.getSheetData(spreadsheetID, numAttendeesRange)[0][0])
        postAtt = timer()
        maxAliases = int(self.getSheetData(spreadsheetID, maxAliasesRange)[0][0])
        postAlias = timer()
        nameAndAliasRange = f"Attendees!A3:{self.alphabet[2 + maxAliases - 1]}{numAttendees + 2}"
        nameAndAliasData = self.getSheetData(spreadsheetID, nameAndAliasRange)
        for entry in nameAndAliasData:
            entry.pop(1)  # remove the number of aliases
        return nameAndAliasData
        print(nameAndAliasData)
        # aliasData = self.getSheetData(self.credentials)
        # print(self.pathToServiceAccountFile)
        # print(self.credentials)
        print(postAtt - preReq1)
        print(postAlias - postAtt)


    def getCredentials(self, pathToServiceAccountFile):
        # https://developers.google.com/identity/protocols/oauth2/service-account#python
        return service_account.Credentials.from_service_account_file(pathToServiceAccountFile, scopes=self.SCOPES)

    def getSheetData(self, spreadsheetID, range):

        # Call the Sheets API
        result = self.sheet.values().get(spreadsheetId=spreadsheetID,
                                    range=range).execute()
        return result.get('values', [])
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