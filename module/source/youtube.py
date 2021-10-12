import discord
import asyncio
import json
import os
import youtube_dl

from functools import partial
from typing import Dict, List, Any
from utils.directory import directory
from process.search import Search

with open(os.path.join(directory, "config", "youtube_option.json")) as file:
    option = json.load(file)
ytdl = youtube_dl.YoutubeDL(option)


class Youtube(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')
        self.uploader = data.get('uploader')
        self.uploader_id = data.get('uploader_id')
        self.uploader_url = data.get('uploader_url') or "http://www.youtube.com/channel/{0}".format(self.uploader_id)

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(
            cls,
            ctx,
            client: discord.Client,
            search: str,
            *,
            loop,
            download=False
    ):
        loop = loop or client.loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data: Dict[Any] = await loop.run_in_executor(None, to_run)

        client = Search(context=ctx, client=client)
        b_message = None
        if 'entries' in data:
            if data.get("extractor", None) == "youtube:search":
                position, b_message = await client.selection(data['entries'])
                if position is None or "cancel" in position:
                    return
                elif isinstance(position, list):
                    data: List[Dict[Any]] = [
                        x for index, x in enumerate(data['entries']) if index in position
                    ]
                else:
                    data: Dict[Any] = data['entries'][position]
            else:
                data: Dict[Any] = data['entries'][0]

        _ = await client.comment_queue(
            data=data,
            b_message=b_message
        )

        if download:
            if isinstance(data, list):
                source = [ytdl.prepare_filename(x) for x in data]
            else:
                source = ytdl.prepare_filename(data)
        else:
            if isinstance(data, list):
                return [{
                    'webpage_url': x['webpage_url'],
                    'requester': ctx.author,
                    'title': x['title']
                } for x in data]
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        if isinstance(source, list):
            return [
                cls(discord.FFmpegPCMAudio(x), data=data, requester=ctx.author)
                for x in source
            ]
        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)
