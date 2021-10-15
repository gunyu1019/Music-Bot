import aiohttp
import asyncio
import logging
import time
import json

from datetime import datetime
from typing import List

log = logging.getLogger(__name__)


class Youtube:
    def __init__(
            self,
            token: List[str] = None,
            session: aiohttp.ClientSession = None,
            loop: asyncio.AbstractEventLoop = None,
            refresh_session: int = 300
    ):
        self.BASE = "https://www.googleapis.com"
        self.token = token
        self._token_position = 0
        self._max_token_position = len(token)
        self.loop = loop
        if session is not None:
            self.session = session
        else:
            self.session = aiohttp.ClientSession(loop=self.loop)

        self._session_start = time.time()
        self._refresh_token = datetime.now()
        self.refresh_session_period = refresh_session

    async def close(self):
        await self.session.close()

    async def refresh_session(self):
        await self.session.close()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self._session_start = time.time()

    async def get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            await self.refresh_session()
        elif 0 <= self.refresh_session_period <= time.time() - self._session_start:
            await self.refresh_session()
        return self.session

    def refresh_token(self):
        if self.token == self._max_token_position:
            self._token_position = 0
        else:
            self._token_position += 1
        return

    def get_token(self) -> str:
        timedelta = self._refresh_token - datetime.now()
        if timedelta.days > 1:
            self._token_position = 0
        return self.token[self._token_position]

    async def requests(self, method: str, path: str, **kwargs) -> dict:
        url = "{}{}".format(self.BASE, path)
        for tries in range(self._max_token_position - 1):
            params = {}
            if self.token is not None:
                params['key'] = self.get_token()

            if 'params' in kwargs:
                kwargs['params'].update(params)
            else:
                kwargs['params'] = params
            session = await self.get_session()
            async with session.request(method, url, **kwargs) as response:
                if response.content_type == "application/json":
                    data = await response.json()
                else:
                    fp_data = await response.text()
                    data = json.loads(fp_data)
                log.debug(f'{method} {url} returned {response.status}')

                if response.status == 429:
                    self.refresh_token()
                    continue

                if 200 <= response.status < 300:
                    return data
                raise HTTPException(response, data)
        raise TooManyRequests(response, data)

    async def get(self, path: str, **kwargs):
        return await self.requests("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self.requests("POST", path, **kwargs)

    # --- Client ---
    async def search(self, search: str):
        return Search(
            await self.get(
                path="/youtube/v3/search",
                params={
                    "q": search,
                    "part": "snippet",
                    "maxResults": 49
                }
            )
        )


class HTTPException(Exception):
    def __init__(self, response, message):
        error = message.get("error")
        self.status = response.status
        if error is not None:
            self.status = error.get('code', self.status)
            self.error = error.get('message', 'Exception')
        else:
            self.error = message
        super().__init__(f"{self.status} {self.error}")


class TooManyRequests(HTTPException):
    pass


class Search:
    def __init__(self, data):
        self.kind = data.get("kind")
        self.etag = data.get("etag")
        self.region = data.get("regionCode")

        page_info = data.get("pageInfo", {})
        self.total = page_info.get("totalResults")
        self.item_page = page_info.get("resultsPerPage")

        self.items = data.get("items", [])

    def __len__(self) -> int:
        return len(self.items)
