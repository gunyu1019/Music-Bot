import discord
import asyncio

import pymysql

def is_manager(user_id,directory):
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

class prefix: #class (기능명)으로 작성하는것을 권장하고 있음.
    def __init__(self,message,prefix,db_json):
        self.message = message
        self.prefix = prefix
        self.db_json = db_json

    async def get(self,directory,client):
        message = self.message
        prefix = self.prefix

        db_json = self.db_json

        db_ip = db_json["mysql"]["ip"]
        db_user = db_json["mysql"]["user"]
        db_pw = db_json["mysql"]["password"]
        db_name = db_json["mysql"]["database"]
        list_message = message.content.split(' ')
        author_id = message.author.mention.replace("<@","",).replace(">","").replace("!","")
        
        if len(list_message) < 2:
            if prefix == '%':
                embed = discord.Embed(title="에러",description="%prefix [info/set/init] [접두어(if you change prefix)]\n위와 같이 작성해주시기 바랍니다.", color=0x0080ff)
            else:
                embed = discord.Embed(title="에러",description=f"%prefix [info/set/init] [접두어(if you change prefix)] 혹은 {prefix}prefix [info/set/init] [접두어(if you change prefix)]\n위와 같이 작성해주시기 바랍니다.", color=0x0080ff)
            await message.channel.send(embed=embed)
            return
        mode = list_message[1]    
        connect = pymysql.connect(host=db_ip, user=db_user, password=db_pw,db=db_name, charset='utf8')
        cur = connect .cursor()
        if mode == "info":
            try:
                sql_prefix = "select * from SERVER_INFO where ID=" + str(message.guild.id)
                cur.execute(sql_prefix)
                c_prefix = cur.fetchall()
                embed = discord.Embed(title="접두어",description=message.guild.name + "서버의 접두어는 " + str(c_prefix[0][1]) + "입니다.", color=0x0080ff)
            except:
                embed = discord.Embed(title="접두어",description=message.guild.name + "서버의 접두어는 %입니다.", color=0x0080ff)
            await message.channel.send(embed=embed)
            connect.close()
            return
        elif mode == "init":
            if not(is_admin(message) or is_manager(author_id,directory)):
                embed = discord.Embed(title="접두어",description=message.guild.name + "봇 주인 혹은 서버 관리자외에는 접두어를 변경할 권한이 없습니다.", color=0x0080ff)
                await message.channel.send(embed=embed)
                connect.close()
                return
            sql_T = "select EXISTS (select * from SERVER_INFO where ID=" + str(message.guild.id) + ") as success"
            cur.execute(sql_T)
            c_TF = cur.fetchall()[0][0]
            if c_TF == 0:
                embed = discord.Embed(title="접두어",description="접두어가 이미 기본설정(%)으로 되어 있습니다...", color=0x0080ff)
            else:
                sql = "update SERVER_INFO set prefix='%' where ID=" + str(message.guild.id)
                cur.execute(sql)
                embed = discord.Embed(title="접두어",description=message.guild.name + "서버의 접두어는 %으로 성공적으로 초기화가 완료되었습니다.", color=0x0080ff)
                connect.commit()
            connect.close()
            await message.channel.send(embed=embed)
        elif mode == "set": 
            if not(is_admin(message) or is_manager(author_id,directory)):
                embed = discord.Embed(title="접두어",description=message.guild.name + "봇 주인 혹은 서버 관리자외에는 접두어를 변경할 권한이 없습니다.", color=0x00aaaa)
                await message.channel.send(embed=embed)
                connect.close()
                return
            if len(list_message) < 3:
                if prefix == '%':
                    embed = discord.Embed(title="에러",description="%prefix [info/set/init] [접두어(if you change prefix)]\n위와 같이 작성해주시기 바랍니다.", color=0x0080ff)
                else:
                    embed = discord.Embed(title="에러",description=f"%prefix [info/set/init] [접두어(if you change prefix)] 혹은 {prefix}prefix [info/set/init] [접두어(if you change prefix)]\n위와 같이 작성해주시기 바랍니다.", color=0x0080ff)
                await message.channel.send(embed=embed)
                return
            n_prefix = list_message[2:]
            if len(n_prefix) > 4 or len(list_message) > 3 or n_prefix.find('\t') != -1 or n_prefix.find('\n') != -1 :
                if prefix == '%':
                    embed = discord.Embed(title="에러",description="%prefix [info/set/init] [접두어(if you change prefix)]\n사용금지 단어가 포함되어 있습니다.\n 접두어를 설정시 \\n,\\t,(공백) 를 사용하시면 안됩니다. 또한 5자 미만으로 하셔야 합니다. 이점 참조하시기 바랍니다.", color=0x0080ff)
                else:
                    embed = discord.Embed(title="에러",description=f"%prefix [info/set/init] [접두어(if you change prefix)] 혹은 {prefix}prefix [info/set/init] [접두어(if you change prefix)]\n사용금지 단어가 포함되어 있습니다.\n 접두어를 설정시 \\n,\\t,(공백) 를 사용하시면 안됩니다. 또한 5자 미만으로 하셔야 합니다. 이점 참조하시기 바랍니다.", color=0x0080ff)
                await message.channel.send(embed=embed)
                return
            sql_T = "select EXISTS (select * from SERVER_INFO where ID=" + str(message.guild.id) + ") as success"
            cur.execute(sql_T)
            c_TF = cur.fetchall()[0][0]
            if c_TF == 0:
                sql = "insert into SERVER_INFO(ID,prefix) values (%s, %s)"
                cur.execute(sql,(message.guild.id,n_prefix))
            else:
                sql = "update SERVER_INFO set prefix=\"" + n_prefix + "\" where ID=" + str(message.guild.id)
                cur.execute(sql)
            embed = discord.Embed(title="접두어",description=message.guild.name + "서버의 접두어는 " + n_prefix + "(명령어)으로 성공적으로 설정되었습니다.", color=0x0080ff)
            await message.channel.send(embed=embed)
            connect.commit()
            connect.close()
            return
        else:
            if prefix == '%':
                embed = discord.Embed(title="에러",description="%prefix [info/set/init] [접두어(if you change prefix)]\n위와 같이 작성해주시기 바랍니다.", color=0x0080ff)
            else:
                embed = discord.Embed(title="에러",description=f"%prefix [info/set/init] [접두어(if you change prefix)] 혹은 {prefix}prefix [info/set/init] [접두어(if you change prefix)]\n위와 같이 작성해주시기 바랍니다.", color=0x0080ff)
            await message.channel.send(embed=embed)
            return