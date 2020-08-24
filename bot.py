import discord
import asyncio

client = discord.Client()
voice_channels = {}

def get_voice(message):
    count = len(client.voice_clients)
    for i in range(count):
        guildID =  client.voice_clients[i].guild.id
        if guildID == message.guild.id:
            return client.voice_clients[i]
    return None

@client.event
async def on_ready(): 
    print("디스코드 봇 로그인이 완료되었습니다.")
    print("디스코드봇 이름:" + client.user.name)
    print("디스코드봇 ID:" + str(client.user.id))
    print("디스코드봇 버전:" + str(discord.__version__))
    print('------')
    
    answer = ""
    total = 0
    for i in range(len(client.guilds)):
        answer = answer + str(i+1) + "번째: " + str(client.guilds[i]) + "(" + str(client.guilds[i].id) + "):"+ str(len(client.guilds[i].members)) +"명\n"
        total += len(client.guilds[i].members)
    print(f"방목록: \n{answer}\n방의 종합 멤버:{total}명")

    await client.change_presence(status=discord.Status.online, activity=discord.Game("노래를 듣고싶다고? $도움를 입력하세요!"))
 
@client.event
async def on_message(message):
    prefix = '$'
    if message.content == f'{prefix}도움' or message.content == f'{prefix}도움말' or message.content == f'{prefix}help' or message.content == f'{prefix}명령어':
        embed = discord.Embed(color=0x0080ff)
        embed.set_author(icon_url=client.user.avatar_url,name='Music Bot')
        embed.add_field(name=f'음악',value='join,leave,play,skip,volume,pause,resume')
        embed.add_field(name=f'관리',value='help,ping')
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}join':
        if message.author.voice == None:
            embed = discord.Embed(title="MusicBot!",description=f"음성방에 들어가주세요!", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        channel = message.author.voice.channel
        voice = await channel.connect()
        voice_channels[voice] = []
        embed = discord.Embed(title="MusicBot!",description=f"{voice.channel}에 성공적으로 연결하였습니다!", color=0x0080ff)
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}debug':
        voiceC = get_voice(message)
        if voiceC == None:
            embed = discord.Embed(title="MusicBot!",description=f"None", color=0x0080ff)
            await message.channel.send(embed=embed)
            return
        elif voiceC in voice_channels:
            embed = discord.Embed(title="MusicBot!",description=f"{voiceC.channel.name}({voiceC.channel.id}):{voice_channels[voiceC]}", color=0x0080ff)
            await message.channel.send(embed=embed)
            return
        embed = discord.Embed(title="MusicBot!",description=f"None", color=0x0080ff)
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}leave':
        voiceC = get_voice(message)
        if voiceC == None or not voiceC in voice_channels:
            embed = discord.Embed(title="MusicBot!",description=f"음성채널방에 들어가있지 않습니다.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        await voiceC.disconnect()
        embed = discord.Embed(title="MusicBot!",description=f"{voiceC.channel}에 성공적으로 떠났습니다!", color=0x0080ff)
        await message.channel.send(embed=embed)
        return

with open('token.txt','r') as f:
    client.run(f.read())
