#Zoom Attendance Parser
Tool for taking Zoom meeting attendance. Configured via google sheets + some local files and outputs data to google sheets.

#Requires:
* Python 3+ (tested on 3.8)
* [Zoom JWT Credentials](https://marketplace.zoom.us/docs/guides/build/jwt-app)
* Zoom Api permissions
    * meeting:read:admin
    * meeting:read
    * report:read:admin
* [Google Service Account Credentials](https://developers.google.com/identity/protocols/oauth2/service-account#python)
    * [see this page for walkthrough of what this particular account will need](https://medium.com/swlh/how-i-automate-my-church-organisations-zoom-meeting-attendance-reporting-with-python-419dfe7da58c)
    
#Setup
* Install Python
* Install the necessary pip packages from requirements.txt
* Create a file named "zoomSecrets.txt" in the folder with main.py and place the Zoom JWT API key and API secret inside it on a single line, separated by a comma with no spaces

[Zoom Credentials](readme%20images/ZoomCredentials.png)
* Place the google service account .json key information you downloaded [(see instructions)](https://medium.com/swlh/how-i-automate-my-church-organisations-zoom-meeting-attendance-reporting-with-python-419dfe7da58c) in the same folder as main.py
and rename it client_secrets.json
* Make a copy of [this central spreadsheet](https://docs.google.com/spreadsheets/d/1nAJzI-ns52FCqaCM_WD5v9XTjSIrH0lc2JkpSf_GWUk/edit#gid=0)
and take the spreadsheet ID, and save it inside a file named "centralSheetID.txt" in the same folder as main.py and give the service account email edit permissions. The section of the URL with the spreadsheet ID is shown below.
![spreadsheetID](readme%20images/spreadsheetID.png)
* Create a folder in Google Drive and give the service account email edit permissions
* Make a copy of [this settings spreadsheet](https://docs.google.com/spreadsheets/d/1Bn3qVhmg_ZlamDh3C9Gss9t3Mz7g-KkHXZ7eulEdW7Y/edit#gid=25161300) and place it within the shared folder
* Add the names of the attendees you would like to track in the first column, and any aliases you would like to associate 
with them in the 2nd columns and beyond. Ensure that you have no gaps between each subsequent attendee. Ensure that 
there are no horizontal gaps between aliases for a single attendee. 
    * Ensure that any given alias can only match a single attendee. For example if there is a Jose and a Joseph you are tracking, 
    an alias of Jose would match both of them, and would associate a given login/logout period with whomever is listed first under the Attendees
    
![](readme%20images/SettingsSheet1.png)
* On the second sheet of the settings document, fill out information of when the meeting starts and ends, and 3 break periods
 where attendees are not tracked, as well as the timezone you are in, adjusted for daylight savings, and the meeting ID in the red box below where it says "Meeting ID".

![](readme%20images/SettingsSheet2.png)

* Return to the central spreadsheet, and fill in the name of the meeting, the ID of the shared folder, 
the ID of the filled out settings spreadsheet, the date to stop tracking the meeting at,
 and the days of the week to track the meeting on.
 
 
 #Usage
 main.py takes 2 command arguments
 1. The date in MM-DD-YY format
 2. The row of the central sheet to grab data for, or "all"
 
 All other settings are configured through local files like centralSheetID.txt, the secrets files, or google sheets.
 
 I have mine set up on a Raspberry Pi that runs a cron job every day at 8PM and saves the output to a log file
 ![](readme%20images/Cronjob.png)
 
 #Sample output
 Every new week gets its own google sheet created automatically. They will automatically be shared with whoever has access to the shared folder they are in
 ![](readme%20images/folderOutput.png)
 
 Sample of a day's output. Late arrival = yellow, absent = red, greyed out breaks are untracked and do not add to the "Time in call"
 ![](readme%20images/sheetOutput.png)
 
 Every login/logout event is also tracked in the "(Day) log" sheet. Useful for troubleshooting any alias issues that may arise or anything else.
 
 If an attendee leaves the call for 2 minutes or less before rejoining (e.g. connection issues) the timeframes 
 are automatically stitched together in the main output and it does not count against their time in the call
 ![](readme%20images/logOutput.png)
 
 Ensure that you have followed all instructions carefully as this program has not been built to handle unexpected input.