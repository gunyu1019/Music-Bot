import discord

from config.config import parser
from module import commands


class Command:
    def __init__(self, bot):
        self.client = bot
        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

    @commands.command(name="재생")
    async def play(self, ctx):

        return


def setup(client):
    return Command(client)
