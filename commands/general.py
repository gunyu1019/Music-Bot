import datetime

import discord

from config.config import parser
from module import commands


class Command:
    def __init__(self, bot):
        self.client = bot
        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

    @commands.command(aliases=['핑'], permission=4)
    async def ping(self, ctx):
        now = datetime.datetime.utcnow()
        if now > ctx.created_at:
            response_ping_r = now - ctx.created_at
        else:
            response_ping_r = ctx.created_at - now
        response_ping_read = float(str(response_ping_r.seconds) + "." + str(response_ping_r.microseconds))
        first_latency = round(self.client.latency * 1000, 2)
        embed = discord.Embed(
            title="Pong!",
            description=f"클라이언트 핑상태: {first_latency}ms\n응답속도(읽기): {round(response_ping_read * 1000, 2)}ms",
            color=self.color)
        msg = await ctx.send(embed=embed)
        now = datetime.datetime.utcnow()
        if now > msg.created_at:
            response_ping_w = now - msg.created_at
        else:
            response_ping_w = msg.created_at - now
        response_ping_write = float(str(response_ping_w.seconds) + "." + str(response_ping_w.microseconds))
        embed = discord.Embed(
            title="Pong!",
            description=f"클라이언트 핑상태: {first_latency}ms\n응답속도(읽기/쓰기): {round(response_ping_read * 1000, 2)}ms/{round(response_ping_write * 1000, 2)}ms",
            color=self.color)
        await msg.edit(embed=embed)
        return


def setup(client):
    return Command(client)
