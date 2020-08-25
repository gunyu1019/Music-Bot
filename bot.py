import discord
import asyncio
import aiohttp

import os
import json
import youtube_dl
import pymysql
import time

from bs4 import BeautifulSoup
from urllib import parse 

directory = os.path.dirname(os.path.abspath(__file__)).replace("\\","/")
db_f = open(directory + "/Data/bot_info.json",mode='r')
db = db_f.read()
db_f.close()
db_json = json.loads(db)

db_ip = db_json["mysql"]["ip"]
db_user = db_json["mysql"]["user"]
db_pw = db_json["mysql"]["password"]
db_name = db_json["mysql"]["database"]

connect = pymysql.connect(host=db_ip, user=db_user, password=db_pw,db=db_name, charset='utf8') #클라이언트 API키 불러오기.
cur = connect.cursor()
cur.execute("SELECT * from Music_Bot")
client_list = cur.fetchone()
key = client_list[0]
token = client_list[1]
connect.close()

client = discord.Client()
voice_channels = {}
voice_setting = {}
ydl_opts  = {
    'format': 'bestaudio/bestaudio'
}
#voice_setting = {
#   repeat
#   shuffle
#}

def is_manager(user_id):
    file = open(directory + "/Setting/Manager.txt",mode='r')
    cache1 = file.readlines()
    file.close()
    for i in range(len(cache1)):
        if user_id == cache1[i]:
            return True
    return False

def is_admin(message):
    for i in range(len(message.author.roles)):
        if message.author.roles[i].permissions.administrator:
            return True
    return False   

def log_info(guild, channel, user, message):
    r_time = time.strftime('%Y-%m-%d %p %I:%M:%S', time.localtime(time.time()))
    print(f"[{r_time} | {guild} | {channel} | {user}]: {message}")
    log = open(f"{directory}/Log/message.txt","a",encoding = 'utf-8')
    log.write(f"[{r_time} | {guild} | {channel} | {user}]: {message}\n")
    log.close()
    #log_info(message.guild,message.channel,message.author,message.content)

def log_system(message):
    r_time = time.strftime('%Y-%m-%d %p %I:%M:%S', time.localtime(time.time()))
    print(f"[{r_time}]: {message}")
    log = open(f"{directory}/Log/system.txt","a",encoding = 'utf-8')
    log.write(f"[{r_time}]: {message}\n")
    log.close()

def log_error(message):
    r_time = time.strftime('%Y-%m-%d %p %I:%M:%S', time.localtime(time.time()))
    print(f"[{r_time}]: {message}")
    log = open(f"{directory}/Log/error.txt","a",encoding = 'utf-8')
    log.write(f"[{r_time}]: {message}\n")
    log.close()

def get_voice(message):
    count = len(client.voice_clients)
    for i in range(count):
        guildID =  client.voice_clients[i].guild.id
        if guildID == message.guild.id:
            return client.voice_clients[i]
    return None

def f_thumbnail(video):
    try:
        thumbnail = video['snippet']['thumbnails']['default']['url']
    except KeyError:
        try:
            thumbnail = video['snippet']['thumbnails']['high']['url']
        except KeyError:
            thumbnail = video['snippet']['thumbnails']['medium']['url']
    finally:
        return thumbnail

async def download(video_id,link):
    if not os.path.isfile(f'{directory}/Music_cache/{video_id}.mp3'):
        ydl_opts_cache = ydl_opts
        ydl_opts_cache['outtmpl'] = f'{directory}/Music_cache/{video_id}.mp3'
        with youtube_dl.YoutubeDL(ydl_opts_cache) as ydl:
            ydl.download([link])

async def m_play(message,voiceC):
    while not len(voice_channels[voiceC]) == 0:
        #만약에 셔플을 넣는다면 여기서 0이 아닌 len 내로 랜덤으로 지칭해 재생.
        file = f'{directory}/Music_cache/{voice_channels[voiceC][0][0]}.mp3'
        embed = discord.Embed(title="Play!",description=f"[{voice_channels[voiceC][0][1]}](https://www.youtube.com/watch?v={voice_channels[voiceC][0][0]})를 재생합니다.", color=0x0080ff)
        embed.set_thumbnail(url=voice_channels[voiceC][0][3])
        embed.set_footer(text=f'{voice_channels[voiceC][0][2]}가 신청한 노래입니다.',icon_url=voice_channels[voiceC][0][2].avatar_url)
        await message.channel.send(embed=embed)
        music_file = discord.FFmpegOpusAudio(file, bitrate=320)
        voiceC.play(music_file)
        #만약에 반복을 넣는 다면 del을 작동하되, 맨 끝에 똑같은 값을 재 대입시킴.
        del voice_channels[voiceC][0]

async def playlist(voiceC,playlistId,author):
    params = {
        "part":"snippet",
        "key":key,
        "playlistId":playlistId
    }
    async def append_channel(html,author):
        for i in html['items']:
            video_id = i['snippet']['resourceId']['videoId']
            title = i['snippet']['title']
            thumbnail = f_thumbnail(i)
            await download(video_id,f'https://www.youtube.com/watch?v={video_id}')
            voice_channels[voiceC].append((video_id,title,author,thumbnail))
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.googleapis.com/youtube/v3/playlistItems",params=params) as resp:
            html = await resp.json()
    await append_channel(html,author)
    while "nextPageToken" in html:
        params['pageToken'] = html['nextPageToken']
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.googleapis.com/youtube/v3/playlistItems",params=params) as resp:
                html = await resp.json()
        await append_channel(html,author)

@client.event
async def on_ready(): 
    log_system("디스코드 봇 로그인이 완료되었습니다.")
    log_system("디스코드봇 이름:" + client.user.name)
    log_system("디스코드봇 ID:" + str(client.user.id))
    log_system("디스코드봇 버전:" + str(discord.__version__))
    print('------')
    
    answer = ""
    total = 0
    for i in range(len(client.guilds)):
        answer = answer + str(i+1) + "번째: " + str(client.guilds[i]) + "(" + str(client.guilds[i].id) + "):"+ str(len(client.guilds[i].members)) +"명\n"
        total += len(client.guilds[i].members)
    log_system(f"방목록: \n{answer}\n방의 종합 멤버:{total}명")

    await client.change_presence(status=discord.Status.online, activity=discord.Game("노래를 듣고싶다고? $도움를 입력하세요!"))
 
@client.event
async def on_message(message):
    author_id = message.author.mention.replace("<@","",).replace(">","").replace("!","")
    list_message = message.content.split(' ')
    prefix = '$'
    if message.content == f'{prefix}도움' or message.content == f'{prefix}도움말' or message.content == f'{prefix}help' or message.content == f'{prefix}명령어':
        log_info(message.guild,message.channel,message.author,message.content)
        embed = discord.Embed(color=0x0080ff)
        embed.set_author(icon_url=client.user.avatar_url,name='Music Bot')
        embed.add_field(name=f'음악',value='join,leave,play,skip,volume,pause,resume')
        embed.add_field(name=f'관리',value='help,ping')
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}join':
        log_info(message.guild,message.channel,message.author,message.content)
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
        log_info(message.guild,message.channel,message.author,message.content)
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
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if voiceC == None or not voiceC in voice_channels:
            embed = discord.Embed(title="MusicBot!",description=f"음성채널방에 들어가있지 않습니다.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        del voice_channels[voiceC]
        await voiceC.disconnect()
        embed = discord.Embed(title="MusicBot!",description=f"{voiceC.channel}에 성공적으로 떠났습니다!", color=0x0080ff)
        await message.channel.send(embed=embed)
        return
    if message.content.startswith(f'{prefix}play'):
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if voiceC == None or not voiceC in voice_channels:
            embed = discord.Embed(title="MusicBot!",description=f"음성채널방에 들어가있지 않습니다.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        if len(list_message) < 2:
            embed = discord.Embed(title="MusicBot!",description=f"URL 혹은 영상 링크를 넣어주세요.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        music = " ".join(list_message[1:])
        url_T = parse.urlparse(music)
        playlist_bool = False
        if url_T.netloc.endswith('youtube.com'):
            for i in url_T.query.split('&'):
                if i.startswith('list='):
                    embed = discord.Embed(title="MusicBot!",description=f"재생목록을 다운로드받고 있습니다.\n상황에 따라 시간이 길게 소요될 수 있으니, 양해부탁드립니다.", color=0x0080ff)
                    await message.channel.send(embed=embed)
                    music = music.replace(i,'')
                    await playlist(voiceC,i.split('list=')[1],message.author)
                    playlist_bool = True
        if not playlist_bool:
            params = {
                "part":"snippet",
                "type":"vidoe",
                "maxResults":1,
                "key":key,
                "q":music
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://www.googleapis.com/youtube/v3/search",params=params) as resp:
                    html = await resp.json()
            if len(html['items']) == 0:
                embed = discord.Embed(title="MusicBot!",description=f"검색결과가 없습니다..", color=0xaa0000)
                await message.channel.send(embed=embed)
                return
            video = html['items'][0]
            video_id = video['id']['videoId']
            title = video['snippet']['title']
            thumbnail = f_thumbnail(video)
            author = message.author
            await download(video_id,f'https://www.youtube.com/watch?v={video_id}')
            voice_channels[voiceC].append((video_id,title,author,thumbnail))
        if not voiceC.is_playing():
            await m_play(message,voiceC)

client.run(token)
