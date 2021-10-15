import discord
import asyncio
import json
import os
import youtube_dl

from functools import partial
from discord.user import _UserTag
from typing import Dict, List, Any
from utils.directory import directory
from process.search import Search

with open(os.path.join(directory, "config", "youtube_option.json")) as file:
    option = json.load(file)
ytdl = youtube_dl.YoutubeDL(option)


class Youtube(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester: discord.Member):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.thumbnails = [YoutubeThumbnail(x) for x in data.get('thumbnails', [])]
        self.duration = data.get('duration')
        self.uploader = data.get('uploader')
        self.uploader_id = data.get('uploader_id')
        self.uploader_url = data.get('uploader_url') or "http://www.youtube.com/channel/{0}".format(self.uploader_id)

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @property
    def thumbnail(self):
        if len(self.thumbnails) == 0:
            return None
        best = sorted(self.thumbnails, key=lambda x: (x.width, x.height))
        return best[0]

    @staticmethod
    def get_ie(search: str):
        for _ie in getattr(ytdl, "_ies"):
            if _ie.suitable(search):
                ie_key = _ie
                break
        else:
            return
        return ie_key

    @staticmethod
    def client(
            ctx,
            client: discord.Client
    ):
        return Search(context=ctx, client=client)

    @staticmethod
    async def create_source(
            url: str,
            loop,
            **kwargs
    ):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=url, download=False, ie_key=kwargs.get("ie_key"))
        data: Dict[Any] = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            data: Dict[Any] = data['entries'][0]

        return {'webpage_url': data['webpage_url'], 'title': data['title']}

    @staticmethod
    async def create_source_without_process(
            url: str,
            loop
    ):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(
            ytdl.extract_info,
            url=url,
            download=False,
            process=False,
            force_generic_extractor=True
        )
        data: Dict[Any] = await loop.run_in_executor(None, to_run)
        return data

    @classmethod
    async def streaming(cls, data, *, loop):
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class YoutubeThumbnail:
    def __init__(self, data: dict):
        self.id: str = data.get('id', 0)
        self.width: int = data['width']
        self.height: int = data['height']
        self.url: str = data['url']
        self.resolution: str = data.get('resolution') or "{width}x{height}".format(
            width=self.width,
            height=self.height
        )

    def to_dict(self):
        return {
            'id': self.id,
            'width': self.width,
            'height': self.height,
            'url': self.url,
            'resolution': self.resolution
        }
