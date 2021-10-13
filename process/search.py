import asyncio
from typing import Union, Optional, List, Dict, Any, Tuple

import discord

from config.config import parser
from module.components import ActionRow, Selection, Options
from module.interaction import ApplicationContext, ComponentsContext
from module.message import MessageCommand, Message


class Search:
    def __init__(
            self,
            context: Union[ApplicationContext, MessageCommand],
            client: discord.Client
    ):
        self.context = context
        self.channel = context.channel
        self.client = client

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.selection_id = "Search_Playlists"

    def check_selection(self, author: discord.Member):
        def f(component: ComponentsContext) -> bool:
            return component.custom_id == self.selection_id and component.author.id == author.id
        return f

    async def selection(self, data: List[Dict[str, Any]]) -> Tuple[
        Optional[
            Union[
                Union[
                    int,
                    str
                ],
                List[int]
            ]
        ], Optional[
            Message
        ]
    ]:
        if len(data) == 0:
            embed = discord.Embed(
                title="[재생]",
                description="검색결과가 없습니다.",
                color=self.error_color
            )
            msg = await self.context.send(embed=embed)
            return None, msg
        elif len(data) == 1:
            return 0, None
        elif len(data) <= 5:
            description_data = _data = data[0:]
        else:
            _data = data[0:49]
            description_data = data[0:5]

        embed = discord.Embed(
            title="[재생]",
            description="다음 항목 중 재생할 노래를 선택해주세요.```scss\n{0}\n```".format(
                [
                    "[{0}] {1} ({2})".format(
                        index,
                        video["title"],
                        video.get("uploader", "")
                    ) if "uploader" in video else
                    "[{0}] {1}".format(
                        index,
                        video["title"]
                    ) for index, video in enumerate(description_data)
                ]
            ),
            color=self.color
        )
        options = [
            Options(
                label="{0}".format(
                    value.get("title", "")
                ), value="selection_player_{0}".format(index),
                description="{0}".format(
                    value.get("webpage_url", None)
                ), emoji=discord.PartialEmoji(name="{0}\U0000FE0F\U000020E3".format(
                    str(index)[0]
                ))
            ) for index, value in _data
        ]

        options.append(
            Options(
                label="취소",
                value="cancel",
                description="선택을 취소합니다.",
                emoji=discord.PartialEmoji(name="\U0000274C")
            )
        )
        msg = await self.context.send(
            embed=embed,
            components=[ActionRow(
                components=[
                    Selection(
                        custom_id=self.selection_id,
                        min_values=1,
                        max_values=49,
                        options=options
                    )
                ]
            )]
        )
        try:
            component: ComponentsContext = await self.client.wait_for(
                event="components",
                check=self.check_selection(self.context.author),
                timeout=300
            )
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="[재생]",
                description="시간이 초과되었습니다. 다시 실행해주시기 바랍니다.",
                color=self.error_color
            )
            await msg.edit(embed=embed)
            return None, msg
        _buffer = "selection_player_"
        len_buffer = len(_buffer)
        if len(component.values) == 1:
            return int(component.values[0][len_buffer:]), msg
        return [int(value[len_buffer:]) for value in component.values], msg

    async def comment_queue(self, data, b_message: Optional[Message] = None) -> Optional[Message]:
        if isinstance(data, list):
            embed = discord.Embed(
                title="[재생]",
                description="[{title}]({url}) 외 {count}개가 정상적으로 추가되었습니다.".format(
                    title=data[0]['title'], url=data[0]['webpage_url'], count=(len(data)-1)
                ),
                color=self.color
            )
        else:
            embed = discord.Embed(
                title="[재생]",
                description="[{title}]({url})이/가 정상적으로 추가되었습니다.".format(
                    title=data['title'], url=data['webpage_url']
                ),
                color=self.color
            )
        embed.set_author(
            name="{0}#{1}".format(self.context.author.name, self.context.author.discriminator),
            icon_url=self.context.author.avatar.url
        )

        if b_message is None:
            return await self.context.send(embed=embed)
        else:
            await b_message.edit(embed=embed)
        return

    async def stream_error(self):
        embed = discord.Embed(
            title="[오류]",
            description="음악을 불러오는 도중 에러가 발생하였습니다.",
            color=self.error_color
        )
        await self.context.send(embed)
        return

    async def playing(self, source):
        embed = discord.Embed(
            title="[재생]",
            description="[{title}]({url})".format(
                title=source.title,
                url=source.web_url
            ),
            color=self.color
        )
        embed.set_footer(
            text="신청 - {0}#{1}".format(
                source.requester.name,
                source.requester.discriminator
            ),
            icon_url=source.requester.avatar.url
        )
        embed.set_thumbnail(url=source.thumbnail.url)
        await self.context.send(embed=embed)
        return
