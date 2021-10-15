import asyncio
import discord
import logging

from async_timeout import timeout
from module.source import Youtube
from process.search import Search


class Player:
    def __init__(self, ctx, client):
        self.bot = client
        self._cog = ctx.parents
        self._guild = ctx.guild
        self._channel = ctx.channel

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.volume = 0.5
        self.current = None

        self.client = Search(
            client=self.bot,
            context=ctx
        )

        client.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()
            try:
                async with timeout(300):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return await self.destroy(self._guild)

            if not isinstance(source, Youtube):
                try:
                    source = await Youtube.streaming(source, loop=self.bot.loop)
                except Exception as error:
                    exc_name = str(type(error))
                    exc_list = [str(x) for x in error.args]

                    if not exc_list:
                        exc_log = exc_name.__name__
                    else:
                        exc_log = "{exc_name}: {exc_list}".format(
                            exc_name=exc_name.__name__,
                            exc_list=", ".join(exc_list)
                        )
                    logging.error("스트리밍을 불러오는 도중 오류가 발생했습니다.\n> {0}".format(exc_log))
                    await self.client.stream_error()
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(
                source,
                after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set)
            )
            await self.client.playing(source)
            await self.next.wait()

            source.cleanup()
            self.current = None

    def destroy(self, guild):
        return self.bot.loop.create_task(
            self._cog.cleanup(guild)
        )
