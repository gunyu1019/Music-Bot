import discord
import asyncio

from typing import Union
from youtube_dl import extractor
from config.config import parser
from module import commands
from module.source import Youtube as source_Youtube
from module.message import MessageCommand
from module.interaction import ApplicationContext
from module.youtube import Youtube
from utils.token import google_token
from process.player import Player


class Command:
    def __init__(self, bot: discord.Client):
        self.bot = bot

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.players = {}
        self.youtube = Youtube(
            token=google_token,
            loop=bot.loop
        )

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx):
        if ctx.guild.id in self.players:
            player = self.players[ctx.guild.id]
        else:
            player = Player(ctx, self.bot)
            self.players[ctx.guild.id] = player
        return player

    @commands.command(name='연결', aliases=['join', 'j'])
    async def connect(self, ctx: Union[MessageCommand, ApplicationContext]):
        channel = None
        if isinstance(ctx, ApplicationContext):
            channel = ctx.options[0]
        else:
            if len(ctx.options) == 1:
                channel_id = ctx.options[0]
                channel = ctx.guild.get_channel(channel_id)
                if not isinstance(channel, discord.VoiceChannel):
                    embed = discord.Embed(
                        title="Music Bot",
                        description="{channel}는 음성 채널이 아닙니다.".format(
                            channel=channel
                        ),
                        color=self.warning_color
                    )
                    await ctx.send(embed=embed)
                    return
            elif len(ctx.options) > 1:
                return

        if channel is None:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(
                    title="Music Bot",
                    description="음성채널에 먼저 들어가신 후, 명령어를 사용해주세요.",
                    color=self.warning_color
                )
                await ctx.send(embed=embed)
                return

        vc = ctx.voice_client

        if vc is not None:
            if vc.channel.id == channel.id:
                embed = discord.Embed(
                    title="Music Bot",
                    description="이미 음성 채널({channel})에 들어가 있습니다.".format(
                        channel=channel.mention
                    ),
                    color=self.warning_color
                )
                await ctx.send(embed=embed)
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                return
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                return
        embed = discord.Embed(
            title="Music Bot",
            description="음성 채널({channel})에 연결을 하였습니다.".format(
                channel=channel.mention
            ),
            color=self.color
        )
        await ctx.send(embed=embed)

    @commands.command(name='재생', aliases=['play', 'p'])
    async def play(self, ctx: Union[ApplicationContext, MessageCommand]):
        if isinstance(ctx, ApplicationContext):
            search = " ".join([x for x in ctx.options.values()])
        else:
            if len(ctx.options) == 0:
                embed = discord.Embed(
                    title="Music Bot",
                    description="재생하실 노래를 작성해주세요.",
                    color=self.warning_color
                )
                await ctx.send(embed=embed)
                return
            search = " ".join(ctx.options[0:])
        original_search = search
        await ctx.defer()

        vc = ctx.voice_client
        if not vc:
            await self.connect.callback(self, ctx)

        ie_key = source_Youtube.get_ie(search)
        if ie_key == extractor.GenericIE:
            _data = await source_Youtube.create_source_without_process(search, self.bot.loop)
            search = _data.get("url")
            ie_key = source_Youtube.get_ie(search)

        client = source_Youtube.client(ctx, self.bot)
        b_message = None
        if ie_key == extractor.YoutubeSearchIE:
            _data = await self.youtube.search(original_search)
            position, b_message = await client.selection(_data.items)
            if isinstance(position, str):
                # Only cancel is string
                embed = discord.Embed(
                    title="Music Bot",
                    description="사용자 요청에 따라 취소 되었습니다.",
                    color=self.color
                )
                await b_message.edit(embed=embed)
                return
            elif isinstance(position, int):
                result = _data.items[position]
                _id = result.get("id", {})
                _snippet = result.get("snippet", {})
                data = {
                    'webpage_url': "https://www.youtube.com/watch?v={0}".format(
                        _id.get("videoId", "")
                    ),
                    'requester': ctx.author,
                    'title': _snippet.get("title")
                }
            elif isinstance(position, list):
                if "cancel"in position:
                    return
                result = [
                    _data.items[x] for x in position
                ]
                data = [
                    {
                        'webpage_url': "https://www.youtube.com/watch?v={0}".format(
                            x.get("id", {}).get("videoId", "")
                        ),
                        'requester': ctx.author,
                        'title': x.get(
                            "snippet", {}
                        ).get(
                            "title", ""
                        )
                    } for x in result
                ]
            else:
                return
        else:
            data = await source_Youtube.create_source(
                url=search,
                loop=self.bot.loop,
                ie_key=ie_key.ie_key()
            )
            data['requester'] = ctx.author

        if isinstance(data, dict):
            _ = await client.comment_queue(
                title=data['title'],
                url=data['webpage_url'],
                b_message=b_message
            )
        elif isinstance(data, list):
            _ = await client.muiti_comment_queue(
                data=data,
                b_message=b_message
            )
        player = self.get_player(ctx)
        if isinstance(data, list):
            for x in data:
                await player.queue.put(x)
        else:
            await player.queue.put(data)

    @commands.command(name='pause')
    async def pause_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(
                title="Music Bot",
                description="재생 중인 노래가 없습니다.",
                color=self.warning_color
            )
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        embed = discord.Embed(
            title="Music Bot",
            description="일시 정지",
            color=self.color
        )
        await ctx.send(embed=embed)

    @commands.command(name='resume')
    async def resume_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send("Resuming ⏯️")

    @commands.command(name='skip')
    async def skip_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()

    @commands.command(name='remove', aliases=['rm', 'rem'])
    async def remove_(self, ctx, pos: int = None):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if pos is None:
            player.queue._queue.pop()
        else:
            try:
                s = player.queue._queue[pos - 1]
                del player.queue._queue[pos - 1]
                embed = discord.Embed(title="",
                                      description=f"Removed [{s['title']}]({s['webpage_url']}) [{s['requester'].mention}]",
                                      color=discord.Color.green())
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(title="", description=f'Could not find a track for "{pos}"',
                                      color=discord.Color.green())
                await ctx.send(embed=embed)

    @commands.command(name='clear', aliases=['clr', 'cl', 'cr'])
    async def clear_(self, ctx):

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('**Cleared**')

    @commands.command(name='queue', aliases=['q', 'playlist', 'que'])
    async def queue_info(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(title="", description="queue is empty", color=discord.Color.green())
            return await ctx.send(embed=embed)

        seconds = vc.source.duration % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
        fmt = '\n'.join(
            f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['webpage_url']}) | ` {duration} Requested by: {_['requester']}`\n"
            for _ in upcoming)
        fmt = f"\n__Now Playing__:\n[{vc.source.title}]({vc.source.web_url}) | ` {duration} Requested by: {vc.source.requester}`\n\n__Up Next:__\n" + fmt + f"\n**{len(upcoming)} songs in queue**"
        embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=discord.Color.green())
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name='np', aliases=['song', 'current', 'currentsong', 'playing'])
    async def now_playing_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(title="", description="I am currently not playing anything",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        seconds = vc.source.duration % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        embed = discord.Embed(title="",
                              description=f"[{vc.source.title}]({vc.source.web_url}) [{vc.source.requester.mention}] | `{duration}`",
                              color=discord.Color.green())
        embed.set_author(icon_url=self.bot.user.avatar_url, name=f"Now Playing 🎶")
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol', 'v'])
    async def change_volume(self, ctx, *, vol: float = None):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I am not currently connected to voice",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        if not vol:
            embed = discord.Embed(title="", description=f"🔊 **{(vc.source.volume) * 100}%**",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        # if not 0 < vol < 101:
        #     embed = discord.Embed(title="", description="Please enter a value between 1 and 100",
        #                           color=discord.Color.green())
        #     return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(title="", description=f'**`{ctx.author}`** set the volume to **{vol}%**',
                              color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name='leave', aliases=["stop", "dc", "disconnect", "bye"])
    async def leave_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel",
                                  color=discord.Color.green())
            return await ctx.send(embed=embed)

        await ctx.send('**Successfully disconnected**')

        await self.cleanup(ctx.guild)


def setup(client):
    return Command(client)
