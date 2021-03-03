# taken/adapted from https://github.com/billydh/zoom-reporting/blob/master/main.py

# import os
import sys
# from typing import List

# import pandas as pd
# from pandas import DataFrame
# from requests import Response
from zoomAttendanceParser import Parser  # , Attendee

#from googl import Googl
# from zoomRequest import Zoom

#ZOOM_API_KEY = # os.environ.get("ZOOM_API_KEY")
#ZOOM_API_SECRET = # os.environ.get("ZOOM_API_SECRET")
#ZOOM_MEETING_ID = # os.environ.get("ZOOM_MEETING_ID")

try:
    tdatapath = r'{}'.format(sys.argv[1])
except IndexError:
    print("Please drag and drop the attendance ")
    datapath = r"C:\Users\Chris\PycharmProjects\ZoomAttendanceParser\logs\log 2.csv"
print(datapath)
#readCSV(droppedFile)

# SERVICE_ACCOUNT_FILE = f".secrets/{os.listdir('.secrets')[0]}"
# SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"]
taliaspath = r"C:\Users\Chris\PycharmProjects\ZoomAttendanceParser\logs\test aliases.txt"
timeFormat = "%m/%d/%Y %I:%M:%S %p"
parser = Parser("%m/%d/%Y %I:%M:%S %p")
parser.loadAttendeesAndAliasFromPath(r"C:\Users\Chris\PycharmProjects\ZoomAttendanceParser\logs\Learners with aliases.txt")
#try:
parser.loadMeetDataFromPath(datapath)
# except IndexError as e:
#     print(e)
#     print("OH NO")
#     print(droppedFile)
# for attendee in parser.attendees:
#     print(attendee.aliases)
# for entry in parser.aliasDictionary:
#     print(entry)
for attendee in parser.attendees:
    attendee.calculateTimeInCall()
    attendee.createHumanReadableTFs()
    print(f"{attendee.name} in call for {attendee.timeInCall}, entered at {attendee.firstLogin}")
# print(parser.aliasDictionary)
input("")
input("")
# if __name__ == "__main__":
#     zoom = Zoom(ZOOM_API_KEY, ZOOM_API_SECRET)
#
#     jwt_token: bytes = zoom.generate_jwt_token()
#     response: Response = zoom.get_meeting_participants(ZOOM_MEETING_ID, jwt_token)
#     list_of_participants: List[dict] = response.json().get("participants")
#
#     while token := response.json().get("next_page_token"):
#         response = zoom.get_meeting_participants(ZOOM_MEETING_ID, jwt_token, token)
#         list_of_participants += response.json().get("participants")
#
#     df: DataFrame = pd.DataFrame(list_of_participants).drop(columns=["attentiveness_score"])
#     df.join_time = pd.to_datetime(df.join_time).dt.tz_convert("Australia/Sydney")
#     df.leave_time = pd.to_datetime(df.leave_time).dt.tz_convert("Australia/Sydney")
#
#     df.sort_values(["id", "name", "join_time"], inplace=True)
#
#     output_df: DataFrame = df.groupby(["id", "name", "user_email"]) \
#         .agg({"duration": ["sum"], "join_time": ["min"], "leave_time": ["max"]}) \
#         .reset_index() \
#         .rename(columns={"duration": "total_duration"})
#
#     output_df.columns = output_df.columns.get_level_values(0)
#
#     output_df.total_duration = round(output_df.total_duration / 3600, 2)
#
#     output_df.join_time = output_df.join_time.dt.strftime("%Y-%m-%d %H:%M:%S")
#     output_df.leave_time = output_df.leave_time.dt.strftime("%Y-%m-%d %H:%M:%S")
#
#     meeting_date: str = output_df.join_time.tolist()[0].split(" ")[0]

    # output_file: str = f"zoom_report_{meeting_date}"

    # googl = Googl(SERVICE_ACCOUNT_FILE, SCOPES)

    # zoom_folder_id: str = googl.get_folder_id("Zoom")
    # sheet_id = googl.create_new_sheet(output_file, zoom_folder_id)
    # result = googl.insert_df_to_sheet(sheet_id, output_df)
    # sheet_link = googl.get_sheet_link(result.get("spreadsheetId"))

    # print(f"Finished uploading Zoom report.\n"
    #      f"spreadsheetId: {result.get('updates').get('spreadsheetId')}\n"
    #      f"updatedRange: {result.get('updates').get('updatedRange')}\n"
    #      f"updatedRows: {result.get('updates').get('updatedRows')}\n"
    #      f"link: {sheet_link}")