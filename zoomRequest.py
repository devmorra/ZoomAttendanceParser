# taken from https://github.com/billydh/zoom-reporting/blob/master/zoom.py
import time
from typing import Optional, Dict, Union, Any

import requests
from authlib.jose import jwt
from requests import Response
from urllib.parse import quote
import json


class ZoomRequester:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.zoom.us/v2"
        self.reports_url = f"{self.base_url}/report/meetings"
        self.jwt_token_exp = 1800
        self.jwt_token_algo = "HS256"
        self.jwt_token = self.generate_jwt_token()


    def genericAPICall(self, endpoint, query_params, next_page_token: Optional[str] = None):
        url = f"{self.base_url}{endpoint}"


    def getMeetingID(self, meetingID):
        meetingID = quote(quote(meetingID, safe=''),safe='')
        url: str = f"{self.base_url}/meetings/{meetingID}"
        query_params = {"show_previous_occurences": True}
        r: Response = requests.get(url,
                                   headers={"Authorization": f"Bearer {self.jwt_token.decode('utf-8')}"},
                                   params=query_params)
        return r


    def get_meeting_participants_response(self, meetingID: str,
                                 next_page_token: Optional[str] = None) -> Response:
        # colons are variable annotations, sort of like giving an expected typing to the var
        meetingID = quote(quote(meetingID, safe=''),safe='')
        url: str = f"{self.reports_url}/{meetingID}/participants"
        query_params: Dict[str, Union[int, str]] = {"page_size": 300}
        if next_page_token:
            query_params.update({"next_page_token": next_page_token})

        r: Response = requests.get(url,
                                   headers={"Authorization": f"Bearer {self.jwt_token.decode('utf-8')}"},
                                   params=query_params)

        return r
        # rdict = json.loads(r.text)
        # participants = rdict['participants']
        # while rdict['next_page_token'] != '':
        #     participants += self.get_meeting_participants(meetingID, rdict['next_page_token'])
        #
        # return participants


    def getParticipantsList(self, meetingID):
        participants = []
        response = self.get_meeting_participants_response(meetingID)
        rdict = json.loads(response.text)
        participants += rdict['participants']
        while rdict['next_page_token'] != '':
            response = self.get_meeting_participants_response(meetingID, next_page_token=rdict['next_page_token'])
            rdict = json.loads(response.text)
            participants += rdict['participants']
            time.sleep(6.1)
            print("Sleeping for 6 seconds to avoid Zoom API limit")
        return participants

    def getPastMeetings(self, meetingID):
        meetingID = quote(quote(meetingID, safe=''),safe='')
        url: str = f"{self.base_url}/past_meetings/{meetingID}/instances"
        r: Response = requests.get(url,
                                   headers={"Authorization": f"Bearer {self.jwt_token.decode('utf-8')}"})
        pastMeetings = json.loads(r.text)['meetings']
        return pastMeetings

    def generate_jwt_token(self) -> bytes:
        iat = int(time.time())

        jwt_payload: Dict[str, Any] = {
            "aud": None,
            "iss": self.api_key,
            "exp": iat + self.jwt_token_exp,
            "iat": iat
        }

        header: Dict[str, str] = {"alg": self.jwt_token_algo}

        jwt_token: bytes = jwt.encode(header, jwt_payload, self.api_secret)

        return jwt_token