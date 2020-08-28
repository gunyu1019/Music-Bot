import discord
import asyncio
import aiohttp

import os
import sys
import json
import youtube_dl
import pymysql
import time
import random
import datetime
import importlib

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
token = client_list[0]
key_l = client_list[1:]
key = key_l[0]
key_n = 0
connect.close()

client = discord.Client()
voice_channels = {}
voice_setting = {}
ydl_opts  = {
    'format': 'bestaudio/bestaudio'
}

class API_error(Exception):
    def __init__(self,msg):
        super().__init__(msg)

sys.path.append(directory + "/Module/")
prefix_m = importlib.import_module('prefix')

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

def is_banned(user_id,message):
    connect = pymysql.connect(host=db_ip, user=db_user, password=db_pw,db=db_name, charset='utf8')
    cur = connect .cursor()
    sql = "select * from BLACKLIST"
    cur.execute(sql)
    banned_list = cur.fetchall()
    connect.close()
    for i in range(len(banned_list)):
        if banned_list[i][0] == int(user_id):
            if not message.content[1:].startswith("blacklist info"):
                log_info(message.guild,message.channel,'Blacklist-BOT',str(message.author) + '잘못된 유저가 접근하고 있습니다!(' + message.content + ')')
                embed = discord.Embed(title="권한 거부(403)", color=0x0080ff)
                embed.add_field(name="권한이 거부되었습니다.", value="당신은 블랙리스트로 등록되어 있습니다.", inline=False)
                coro = message.channel.send(embed=embed)
                asyncio.run_coroutine_threadsafe(coro, client.loop)
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

async def check(message,voiceC):
    if voiceC == None or not voiceC in voice_channels:
        embed = discord.Embed(title="MusicBot!",description="음성채널방에 들어가있지 않습니다.", color=0xaa0000)
        await message.channel.send(embed=embed)
        return True
    if message.author.voice == None:
        embed = discord.Embed(title="MusicBot!",description="음성방에 들어가주세요!", color=0xaa0000)
        await message.channel.send(embed=embed)
        return True
    return False

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
        if voice_setting[voiceC]["shuffle"]: #셔플
            if voice_setting[voiceC]["repeat"]:
                max_play = len(voice_channels[voiceC]) - 2
            else:
                max_play = len(voice_channels[voiceC]) - 1
            play_num = random.randrange(0,max_play)
        else:
            play_num = 0
        file = f'{directory}/Music_cache/{voice_channels[voiceC][play_num][0]}.mp3' #재생
        embed = discord.Embed(title="Play!",description=f"{voiceC.channel.name}에서 [{voice_channels[voiceC][play_num][1]}](https://www.youtube.com/watch?v={voice_channels[voiceC][play_num][0]})를 재생합니다.", color=0x0080ff)
        embed.set_thumbnail(url=voice_channels[voiceC][play_num][3])
        embed.set_footer(text=f'{voice_channels[voiceC][play_num][2]}가 신청한 노래입니다.',icon_url=voice_channels[voiceC][play_num][2].avatar_url)
        await message.channel.send(embed=embed)
        music_file = discord.FFmpegOpusAudio(file, bitrate=voiceC.channel.bitrate/1000,options=f'-af "volume={voice_setting[voiceC]["volume"]/100},atempo={voice_setting[voiceC]["tempo"]}"')
        voiceC.play(music_file) #-> 버그, 여기서 플레이가 끝날때까지 기달려야됨.
        while voiceC.is_playing() or voiceC.is_paused(): #-> 사실 이건 임시대처한거일뿐...미친짓일꺼임.
            await asyncio.sleep(0.01)
        if len(voice_channels[voiceC]) != 0:
            if voice_setting[voiceC]["repeat"]: #반복
                voice_channels[voiceC].append(voice_channels[voiceC][play_num])
            del voice_channels[voiceC][play_num]

async def add_queue(message,html,count,voiceC):
    video = html['items'][count]
    video_id = video['id']
    if type(video_id) == dict:
        if 'videoId' in video_id:
            video_id = video_id['videoId']
    title = video['snippet']['title']
    thumbnail = f_thumbnail(video)
    author = message.author
    await download(video_id,f'https://www.youtube.com/watch?v={video_id}')
    voice_channels[voiceC].append((video_id,title,author,thumbnail))
    embed = discord.Embed(description=f"[{title}](https://www.youtube.com/watch?v={video_id})가 정상적으로 추가되었습니다.", color=0x0080ff)
    embed.set_author(name="Play",icon_url=client.user.avatar_url)
    embed.set_footer(text=f'{author}가 등록하였습니다.',icon_url=author.avatar_url)
    await message.channel.send(embed=embed)

def get_new():
    global key_n
    key_n += 1
    if key_n != len(key_l) - 1:
        return key_l[key_n]
    else:
        return key_l[0]

async def google_api(t,params,count=0):
    if count == 12:
        raise API_error('All API quotas were used.')
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.googleapis.com/youtube/v3/{t}",params=params) as resp:
            if resp.status == 200:
                html = await resp.json()
            elif resp.status == 403:
                e_code = await resp.json()
                e_bool = False
                for i in e_code['error']['errors']:
                    if i['reason'] == "quotaExceeded":
                        global key
                        key = get_new()
                        e_bool = True
                        params['key'] = key
                        await google_api(t,params,count+1)
                if not e_bool:
                    raise API_error('An unknown error has occurred.')
            else:
                html = None
    return html

async def get_playlist(voiceC,playlistId,author):
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
    html = await google_api('playlistItems',params)
    await append_channel(html,author)
    while "nextPageToken" in html:
        params['pageToken'] = html['nextPageToken']
        html = await google_api('playlistItems',params)
        await append_channel(html,author)

async def get_vid(voiceC,vid,message):
    params = {
        "part":"snippet",
        "maxResults":1,
        "key":key,
        "id":vid
    }
    html = await google_api('videos',params)
    if len(html['items']) == 0:
        embed = discord.Embed(title="MusicBot!",description="검색결과가 없습니다..", color=0xaa0000)
        await message.channel.send(embed=embed)
        return
    await add_queue(message,html,0,voiceC)
    return

async def get_search(voiceC,music,message):
    params = {
        "part":"snippet",
        "type":"vidoe",
        "maxResults":1,
        "key":key,
        "q":music
    }
    html = await google_api('search',params)
    if len(html['items']) == 0:
        embed = discord.Embed(title="MusicBot!",description="검색결과가 없습니다..", color=0xaa0000)
        await message.channel.send(embed=embed)
        return
    await add_queue(message,html,0,voiceC)
    return

@client.event
async def on_voice_state_update(member,before,after):
    if member.id == 746895766684958820:
        if after == None:
            del voice_channels[before]
    return

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

    await client.change_presence(status=discord.Status.online, activity=discord.Game("노래를 듣고싶다고? %도움를 입력하세요!"))
 
@client.event
async def on_message(message):
    author_id = message.author.mention.replace("<@","",).replace(">","").replace("!","")
    list_message = message.content.split(' ')
    if message.author == client.user or message.author.bot:
        return
    connect = pymysql.connect(host=db_ip, user=db_user, password=db_pw,db=db_name, charset='utf8')
    try:
        cur = connect.cursor()
        sql_prefix = f"select prefix from SERVER_INFO where ID={message.guild.id}"
        cur.execute(sql_prefix)
        cache = cur.fetchone()
        if not cache == None:
            prefix = cache[0]
        else:
            prefix = "%"
    except:
        prefix = "%"
    connect.close()
    if message.content == f'{prefix}도움' or message.content == f'{prefix}도움말' or message.content == f'{prefix}help' or message.content == f'{prefix}명령어':
        log_info(message.guild,message.channel,message.author,message.content)
        embed = discord.Embed(color=0x0080ff)
        embed.set_author(icon_url=client.user.avatar_url,name='Music Bot')
        embed.add_field(name='음악',value='join,leave,play,select,skip,volume,pause,resume,queue,shuffle,repeat,tempo,volume',inline=False)
        embed.add_field(name='관리',value='help,ping,information,blacklist,prefix',inline=False)
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}ping':
        now = datetime.datetime.utcnow()
        embed = discord.Embed(title="Pong!", color=0x0080ff)
        msg = await message.channel.send(embed=embed)
        message_ping_c = msg.created_at - now
        message_ping = float(f'{message_ping_c.seconds}.{message_ping_c.microseconds}')
        embed = discord.Embed(title="Pong!",description=f"클라이언트 핑: {round(client.latency * 1000,2)}ms\n응답속도: {round(message_ping * 1000,2)}ms", color=0x0080ff)
        await msg.edit(embed=embed)
        return
    if message.content == f'{prefix}information':
        log_info(message.guild,message.channel,message.author,message.content)
        total = 0
        for i in client.guilds:
            total += len(i.members)
        embed = discord.Embed(title='Music Bot', color=0x0080ff)
        embed.add_field(name='제작자',value='건유1019#0001',inline=True)
        embed.add_field(name='깃허브',value='[링크](https://github.com/gunyu1019/Music-Bot)',inline=True)
        embed.add_field(name='<:user:735138021850087476>서버수/유저수',value=f'{len(client.guilds)}서버/{total}명',inline=True)
        embed.add_field(name='<:discord:735135879990870086>discord.py',value=f'v{discord.__version__}',inline=True)
        embed.add_field(name='<:aiohttp:735135879634616351>aiohttp',value=f'v{aiohttp.__version__}',inline=True)
        embed.set_thumbnail(url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}join':
        log_info(message.guild,message.channel,message.author,message.content)
        if message.author.voice == None:
            embed = discord.Embed(title="MusicBot!",description="음성방에 들어가주세요!", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        channel = message.author.voice.channel
        voice = await channel.connect()
        voice_channels[voice] = []
        voice_setting[voice] = {
            "shuffle": False,
            "repeat": False,
            "volume": 100,
            "tempo": 1.0
        }
        embed = discord.Embed(description=f"{voice.channel}에 성공적으로 연결하였습니다!", color=0x0080ff)
        embed.set_author(name="Join",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        return
    if message.content.startswith(f'{prefix}prefix') or message.content.startswith('%prefix'):
        log_info(message.guild,message.channel,message.author,message.content)
        if is_banned(author_id,message):
            return
        if message.guild == None:
            embed = discord.Embed(title="접두어",description=message.guild.name + "DM에서는 접두어 기능을 사용하실수 없습니다.", color=0x0080ff)
            await message.channel.send(embed=embed)
            return
        pf = prefix_m.prefix(message,prefix,db_json)
        await pf.get(directory,client)
        return

    if message.content == f'{prefix}debug' and is_manager(author_id):
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if voiceC == None:
            embed = discord.Embed(title="MusicBot!",description="None", color=0x0080ff)
            await message.channel.send(embed=embed)
            return
        elif voiceC in voice_channels:
            embed = discord.Embed(title=f"{voiceC.channel.name}({voiceC.channel.id})", color=0x0080ff)
            embed.add_field(name='재생목록: ',value=f'{voice_channels[voiceC]}')
            embed.add_field(name='설정: ',value=f'{voice_setting[voiceC]}')
            await message.channel.send(embed=embed)
            return
        embed = discord.Embed(title="MusicBot!",description=f"None", color=0x0080ff)
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}leave':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        del voice_channels[voiceC]
        del voice_setting[voiceC]
        await voiceC.disconnect()
        embed = discord.Embed(description=f"{voiceC.channel}에 성공적으로 떠났습니다!", color=0x0080ff)
        embed.set_author(name="Leave",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        return
    if message.content.startswith(f'{prefix}play'):
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        if len(list_message) < 2:
            embed = discord.Embed(title="MusicBot!",description="URL 혹은 영상 링크를 넣어주세요.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        music = " ".join(list_message[1:])
        url_T = parse.urlparse(music)
        playlist_bool = False
        video_id_bool = False
        if url_T.netloc.endswith('youtube.com'):
            for i in url_T.query.split('&'):
                if i.startswith('list='):
                    embed = discord.Embed(title="MusicBot!",description="재생목록을 다운로드받고 있습니다.\n상황에 따라 시간이 길게 소요될 수 있으니, 양해부탁드립니다.", color=0x0080ff)
                    await message.channel.send(embed=embed)
                    music = music.replace(i,'')
                    await get_playlist(voiceC,i.split('list=')[1],message.author)
                    playlist_bool = True
            if not playlist_bool:
                for i in url_T.query.split('&'):
                    if i.startswith('v='):
                        await get_vid(voiceC, i.split('v=')[1],message)
                        video_id_bool = True
        if url_T.netloc.endswith('youtu.be') and url_T.path.startswith('/'):
            await get_vid(voiceC, i.split('/')[1],message)
            video_id_bool = True
        if not (playlist_bool or video_id_bool):
            await get_search(voiceC,music,message)
        if not voiceC.is_playing():
            await m_play(message,voiceC)
        return
    if message.content.startswith(f'{prefix}select'):
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        if len(list_message) < 2:
            embed = discord.Embed(title="MusicBot!",description="URL 혹은 영상 링크를 넣어주세요.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        embed = discord.Embed(title="유튜브 검색",description="검색목록을 불러오는 중입니다!", color=0x0080ff) #기존 검색코드(우려먹음)
        msg1 = await message.channel.send(embed=embed)
        music = " ".join(list_message[1:])
        params = {
        "part":"snippet",
        "type":"vidoe",
        "maxResults":5,
        "key":key,
        "q":music
        }
        html = await google_api('search',params)
        if len(html['items']) == 0:
            embed = discord.Embed(title="MusicBot!",description="검색결과가 없습니다..", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        elif len(html['items']) == 1:
            count_search = 0
            return
        else:
            count = len(html['items'])
            answer = "```css\n"
            if count > 5:
                m_list = html['items'][0:5]
                count = 5
            else:
                m_list = html['items']
            for i in m_list:
                answer += f"[{m_list.index(i)+1}]: {i['snippet']['title']}\n"
            answer += "```"
            embed = discord.Embed(title="유튜브 검색",description=answer +"아래의 반응을 클릭하여 검색해주세요.\n본인만 선택이 가능하며, 30초내로 입력해주세요.\n로딩시에는 선택이 불가능합니다.", color=0x0080ff)
            msg2 = await message.channel.send(embed=embed)
            await msg1.delete()
            for i in range(count):
                await msg2.add_reaction(f"{i+1}\U0000FE0F\U000020E3")
            author = message.author
            def check_wait_for(reaction, user):
                for i in range(count):
                    if str(i+1) + "\U0000FE0F\U000020E3" == reaction.emoji:
                        return user == author and msg2.id == reaction.message.id
            reaction,_ = await client.wait_for('reaction_add', check=check_wait_for)
            for i in range(count):
                if f"{i+1}\U0000FE0F\U000020E3" == reaction.emoji:
                    count_search = i
                    break
            try:
                await msg2.clear_reactions()
            except discord.Forbidden:
                embed_waring = discord.Embed(title="\U000026A0경고!",description="권한설정이 잘못되었습니다! 메세지 관리를 활성해 주세요.\n메세지 관리 권한이 활성화 되지 않을 경우 디스코드봇이 정상적으로 작동하지 않습니다.", color=0xffd619)
                await message.channel.send(embed=embed_waring)
            await msg2.delete()
        await add_queue(message,html,count_search,voiceC)
        if not voiceC.is_playing():
            await m_play(message,voiceC)
        return
    if message.content == f'{prefix}skip':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        embed = discord.Embed(description="음악을 스킵합니다.", color=0x0080ff)
        embed.set_author(name="Skip",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        voiceC.stop()
        return
    if message.content == f'{prefix}stop':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        embed = discord.Embed(description="재생을 멈춥니다!", color=0x0080ff)
        embed.set_author(name="Stop",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        voice_channels[voiceC] = []
        voiceC.stop()
        return
    if message.content == f'{prefix}shuffle':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        if voice_setting[voiceC]["shuffle"]:
            embed = discord.Embed(description="다시 정리...셔플모드를 끕니다.", color=0x0080ff)
            embed.set_author(name="Shuffle",icon_url=client.user.avatar_url)
            await message.channel.send(embed=embed)
            voice_setting[voiceC]["shuffle"] = False
        else:
            embed = discord.Embed(description="재생목록을 흔들어! 흔들어! 셔플모드를 켭니다.", color=0x0080ff)
            embed.set_author(name="Shuffle",icon_url=client.user.avatar_url)
            await message.channel.send(embed=embed)
            voice_setting[voiceC]["shuffle"] = True
        return
    if message.content == f'{prefix}repeat':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        if voice_setting[voiceC]["repeat"]:
            embed = discord.Embed(description="무한반복!~~ 반복재생을 끕니다.", color=0x0080ff)
            embed.set_author(name="Repeat",icon_url=client.user.avatar_url)
            await message.channel.send(embed=embed)
            voice_setting[voiceC]["repeat"] = False
        else:
            embed = discord.Embed(description="반복재생을 켭니다.", color=0x0080ff)
            embed.set_author(name="Repeat",icon_url=client.user.avatar_url)
            await message.channel.send(embed=embed)
            voice_setting[voiceC]["repeat"] = True
        return
    if message.content == f'{prefix}pause':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        voiceC.pause()
        embed = discord.Embed(description="잠시중지! 음악을 일시 정지합니다.", color=0x0080ff)
        embed.set_author(name="Pause",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}resume':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        voiceC.resume()
        embed = discord.Embed(description="다시 재생! 일시 정지를 해제합니다..", color=0x0080ff)
        embed.set_author(name="Resume",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        return
    if message.content.startswith(f'{prefix}tempo'):
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        if len(list_message) < 2:
            embed = discord.Embed(description=f"템포값은 {voice_setting[voiceC]['tempo']}배입니다.", color=0x0080ff)
            embed.set_author(name="Tempo",icon_url=client.user.avatar_url)
            await message.channel.send(embed=embed)
            return
        try:
            tempo_num = float(" ".join(list_message[1:]))
            if tempo_num < 0.5 or tempo_num > 100.0:
                embed = discord.Embed(title="MusicBot!",description="템포값은 0.5배~100배로 설정이 가능합니다..", color=0xaa0000)
                await message.channel.send(embed=embed)
                return
        except ValueError:
            embed = discord.Embed(title="MusicBot!",description="옳바른 숫자값을 입력해주세요.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        voice_setting[voiceC]["tempo"] = tempo_num
        if voiceC.is_playing():
            embed = discord.Embed(description=f"탬포 값을 {tempo_num}배으로 설정하였습니다.\n**[주의]:** 탬포 값은 다음 곡부터 적용됩니다.", color=0x0080ff)
        else:
            embed = discord.Embed(description=f"템포 값을 {tempo_num}배으로 설정하였습니다.", color=0x0080ff)
        embed.set_author(name="Tempo",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        return
    if message.content.startswith(f'{prefix}volume'):
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        if len(list_message) < 2:
            embed = discord.Embed(description=f"볼륨값은 {voice_setting[voiceC]['volume']}%입니다.", color=0x0080ff)
            embed.set_author(name="Volume",icon_url=client.user.avatar_url)
            await message.channel.send(embed=embed)
            return
        try:
            vol_num = int(" ".join(list_message[1:]))
        except ValueError:
            embed = discord.Embed(title="MusicBot!",description="옳바른 숫자값을 입력해주세요.", color=0xaa0000)
            await message.channel.send(embed=embed)
            return
        voice_setting[voiceC]["volume"] = vol_num
        if voiceC.is_playing():
            embed = discord.Embed(description=f"볼륨값을 {vol_num}%으로 설정하였습니다.\n**[주의]:** 볼륨값은 다음 곡부터 적용됩니다.", color=0x0080ff)
        else:
            embed = discord.Embed(description=f"볼륨값을 {vol_num}%으로 설정하였습니다.", color=0x0080ff)
        embed.set_author(name="Volume",icon_url=client.user.avatar_url)
        await message.channel.send(embed=embed)
        return
    if message.content == f'{prefix}queue':
        log_info(message.guild,message.channel,message.author,message.content)
        voiceC = get_voice(message)
        if await check(message,voiceC) or is_banned(author_id,message):
            return
        async def pg_queue(message,client,voiceC,queue_page):
            answer = '```css\n'
            if len(voice_channels[voiceC])%5 == 0:
                m_page = len(voice_channels[voiceC])/5
            else:
                m_page = len(voice_channels[voiceC])/5 + 1
            if len(voice_channels[voiceC]) - queue_page*5 > 5:
                c = voice_channels[voiceC][queue_page*5:queue_page*5+5]
            else:
                load = len(voice_channels[voiceC]) - queue_page*5
                c = voice_channels[voiceC][queue_page*5:queue_page*5+load]
            for i in c:
                answer += f'[{voice_channels[voiceC].index(i) + 1}]: {i[1]}\n'
            answer += '```'
            if voice_setting[voiceC]["repeat"]:
                o1 = "켜짐"
            else:
                o1 = "꺼짐"
            if voice_setting[voiceC]["shuffle"]:
                o2 = "켜짐"
            else:
                o2 = "꺼짐"
            embed = discord.Embed(description=f"{answer}\n반복:{o1}, 셔플: {o2}", color=0x0080ff)
            embed.set_author(name="Queue",icon_url=client.user.avatar_url)
            embed.set_footer(text=f"{queue_page+1}/{int(m_page)}페이지")
            msg = await message.channel.send(embed=embed)
            if not queue_page == 0:
                await msg.add_reaction("\U00002B05")
            if not queue_page + 1 == int(m_page):
                await msg.add_reaction("\U000027A1")
            message_id = msg.id
            def check(reaction, user):
                if "\U000027A1" == reaction.emoji or "\U00002B05" == reaction.emoji:
                    return user.id == message.author.id and message_id == reaction.message.id
            reaction,_ = await client.wait_for('reaction_add', check=check)
            if reaction.emoji == "\U000027A1":
                await msg.delete()
                await pg_queue(message,client,voiceC,queue_page+1)
            elif reaction.emoji == "\U00002B05":
                await msg.delete()
                await pg_queue(message,client,voiceC,queue_page-1)
            return
        if len(voice_channels[voiceC] == 0):
            embed = discord.Embed(description=f"재생 중인 노래가 없습니다.", color=0x0080ff)
            embed.set_author(name="Queue",icon_url=client.user.avatar_url)
            embed.set_footer(text="0/0페이지")
            await message.channel.send(embed=embed)
            return
        await pg_queue(message,client,voiceC,0)
        return
    return

client.run(token)