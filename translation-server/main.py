#!/usr/bin/env python3.8
import os
from typing import Text

from quart import Quart, websocket, request
from quart_cors import cors

import discord
from discord.ext import commands, tasks
import json
import ini

# from twisted.web import server, resource
# from twisted.internet import reactor
# #import threading
# from threading import Thread
# import asyncio
# from syncer import sync

config = ini.parse(open('config.ini','r').read())

discordChannel = int(config['discord_channel_id'])
discordGuild = int(config['discord_guild_id'])

TextMapFull = {}
TextMap = {}

if os.path.exists("../TextMap_custom.tsv"):
	with open("../TextMap_custom.tsv",'r',encoding='utf-8') as f:
		f.readline() # skip line 1
		while True:
			line = f.readline()
			if not line:
				break
			#elif line.strip()=="":
			#	continue
			line=line.split('\t')
			line[-1]=line[-1].rstrip() #Strip newline char
			tID = int(line[0])
			TextMapFull[tID] = line[1:]
			if line[-1] != "" and line[-1] != "XXX":
				TextMap[tID] = line[-1].replace("{","<").replace("}",">").replace("\\n","//n")
	print(len(TextMapFull))
	print(len(TextMap))

def write_database():
	with open("../TextMap_custom.tsv","w") as f:
		f.write("TEXT_ID	EN	EN_RE\n")
		for textID in TextMapFull:
			f.write(str(textID)+"\t"+"\t".join(TextMapFull[textID])+"\n")
	print("Wrote database.")

#app.run(port=8080)

# class Simple(resource.Resource):
# 	def __init__(self, discordBot,event_loop):
# 		#return
# 		self.bot = discordBot
# 		asyncio.set_event_loop(event_loop)

		

# 	isLeaf = True
# 	def render_GET(self, request):
# 		print("HTTP GET!")
# 		self.post_discord_message()
# 		if self.data != None:
# 			return self.data
# 		else:
# 			return b"<html>There is no TextMap_custom.tsv. Please run gen_retranslation.py first to generate a custom TextMap.</html>"
# 		#return b"<html>Hello, world!</html>"

# 	@sync
# 	async def post_discord_message(self):
# 		message_channel = self.bot.get_channel(discordChannel)
# 		await message_channel.send("Recieved HTTP GET!")
		

#What the fuck does any of this mean?
# class ReactorThread(Thread):
# 	def __init__(self, reactor, discordBot,event_loop):
# 		Thread.__init__(self)
# 		self.reactor = reactor
# 		self.site = server.Site(Simple(discordBot,event_loop))

# 	def listen(self):
# 		self.reactor.callFromThread(self._listen)

# 	def _listen(self):
# 		#self.site = server.Site(PageFactory())
# 		#print("aaa")
# 		self.port = reactor.listenTCP(8080, self.site)

# 	def run(self):
# 		print("HTTP server running!")
# 		self.reactor.run(installSignalHandlers=False)


intents = discord.Intents.default()
intents.members = False

bot = commands.Bot(command_prefix="?", description="none", intents=intents)

quartServer = Quart(__name__)
quartServer = cors(quartServer, allow_origin="*")

@quartServer.route("/", methods=['GET'])
async def hello():
	if len(TextMap) > 0:

		message_channel = bot.get_channel(discordChannel)
		#await message_channel.send("Recieved HTTP GET!")

		return json.dumps(TextMap,ensure_ascii=False).encode()
	else:
		return b"<html>There is no TextMap_custom.tsv. Please run gen_retranslation.py first to generate a custom TextMap.</html>",404

@quartServer.route("/",methods=["POST"])
async def handleFilePost():
	newData = await request.get_data()
	#print(newData)
	if len(newData) == 0:
		return b'Invalid client submission.',400
	try:
		newTextMap = json.loads(newData)
	except:
		return b'Invalid client submission.',400

	botMessage = ""
	keysAdded = 0
	API_KEY = False
	if "API_KEY" in newTextMap:
		API_KEY = (newTextMap["API_KEY"] == config['override_password'])
	
	for fakeKey in newTextMap:
		if fakeKey == "API_KEY":
			continue
		elif newTextMap[fakeKey].strip() == "":
			continue

		k = int(fakeKey)
		if k not in TextMapFull:
			#print(type(k))
			return bytes('Invalid key '+str(k)+' in client submission.',"utf-8"),400
		elif k not in TextMap:
			TextMap[k]=newTextMap[fakeKey]
			TextMapFull[k][1]=TextMap[k]
			botMessage +="\n["+fakeKey+"] `"+TextMapFull[k][0]+"` -> `"+TextMapFull[k][1]+"`"
			keysAdded+=1
		elif k in TextMap and TextMap[k] == newTextMap[fakeKey]: #Same as old key, ignore it
			pass
		else: #If already exists in the text map
			if API_KEY:
				botMessage += "\n["+fakeKey+"]: `"+TextMap[k]+"` -> `"+newTextMap[fakeKey]+"`"
				TextMap[k]=newTextMap[fakeKey]
				TextMapFull[k][1]=TextMap[k]
				keysAdded+=1
			else:
				botMessage += "\n["+fakeKey+"] No API key, can't approve change: `"+TextMap[k]+"` -> `"+newTextMap[fakeKey]+"`"
	if botMessage != "":
		print(botMessage)
		message_channel = bot.get_channel(discordChannel)
		if len(botMessage) > 2000:
			messagesToUpload = botMessage.split("\n")
			halfWay = int(len(messagesToUpload)/2)
			await message_channel.send("\n".join(messagesToUpload[:halfWay]))
			await message_channel.send("\n".join(messagesToUpload[halfWay:]))
		else:
			await message_channel.send(botMessage)
	
	if keysAdded==0:
		return b'There have been no keys added, your submission was discarded.',200
	return bytes("Success. "+str(keysAdded)+" lines have been updated/added."), 200

@quartServer.after_request
def after_request(response):
	response.headers['Access-Control-Allow-Origin'] = "*"
	response.headers['Content-Type']="application/json;charset=UTF-8"
	return response


@bot.slash_command(guild_ids=[discordGuild])
async def hello(ctx, name: str = None):
	name = name or ctx.author.name
	await ctx.respond(f"Hello {name}!")

@bot.slash_command(guild_ids=[discordGuild])
async def override_key(ctx, key: int,new_text:str):
	if key not in TextMapFull:
		await ctx.respond("This key does not exist in the database.")
		return
	if key in TextMap:
		msg = "Updated retranslated text:\n"
		msg +="["+str(key)+"] `"+TextMap[key]+"` -> `"+new_text+"`"
		TextMap[key]=new_text
		TextMapFull[key][1]=TextMap[key]
		await ctx.respond(msg)
	else:
		msg = "Added new translation:\n"
		TextMap[key]=new_text
		TextMapFull[key][1]=TextMap[key]
		msg +="["+str(key)+"] `"+TextMapFull[key][0]+"` -> `"+TextMapFull[key][1]+"`"
		await ctx.respond(msg)

@bot.slash_command(guild_ids=[discordGuild])
async def delete_key(ctx, key:int):
	if key in TextMap:
		TextMap.pop(key)
		TextMapFull[key][1]="XXX"
		await ctx.respond("Deleted "+str(key)+" from database.")
	else:
		await ctx.respond("This key wasn't found in the database.")

#@bot.user_command(name="Say Hello")
#async def hi(ctx, user):
#	await ctx.respond(f"{ctx.author.mention} says hello to {user.name}!")

firstRun = True

@tasks.loop(minutes=int(config['autosave_timer']))  # every 30 minutes
async def job():
	global firstRun
	if firstRun==True:
		firstRun=False
		print("Ignoring first run.")
		return
	try:
		write_database()
	except Exception as e:
		print("Failed to write database....")
		print(e)
	
@bot.event
async def on_ready():
	print("The bot is ready!")
	#print(str(client.user.id))
	#https://discordapp.com/oauth2/authorize?client_id=351447700064960522&scope=bot&permissions=0
	#Send Messages, Manage Messages, Embed Links, and Add Reactions is required for optimal use.
	print("Add me with https://discord.com/oauth2/authorize?client_id="+str(bot.user.id)+ "&scope=bot&permissions=52224")
	#await client.change_presence(status=discord.Status.online, activity=discord.Game(serverCount()))

bot.loop.create_task(quartServer.run_task('0.0.0.0',port=8880))
job.start()
bot.run(config['discord_token'])
