#!/usr/bin/env python3.8
import os
import sys
from typing import Text

from quart import Quart, websocket, request
from quart_cors import cors

import discord
from discord.commands import Option
from discord.ext import commands, tasks
import json
import ini
import math

from thefuzz import fuzz
from thefuzz import process

import traceback

# from twisted.web import server, resource
# from twisted.internet import reactor
# #import threading
# from threading import Thread
# import asyncio
# from syncer import sync

config = ini.parse(open('config.ini','r').read())

discordChannel = int(config['discord_channel_id_en_re'])
discordGuild = int(config['discord_guild_id'])

class TextMapManager:
	def __init__(self) -> None:
		self.full = {}
		self.langs = {"en_re":{},"pt":{}}
		self.origLangs = {"en_re":"en", "pt":"jp"}
		self.columns = ['en','cn','jp','kr']

	def getLangColumn(self,lang:str)->int:
		return self.columns.index(lang)

	def getOrigLang(self,lang:str)->int:
		return self.columns.index(self.origLangs[lang])


	def setNewKey(self,lang:str,key:int,value:str):
		self.langs[lang][key]=value
		#self.full[key][self.columns[lang]]=value
		pass

	#def getKey(self,key:int)->dict:


TEXTMAPMAN = TextMapManager()

#TextMapFull = {}
#TextMap = {}



if os.path.exists("TextMap_aio.tsv"):
	with open("TextMap_aio.tsv",'r',encoding='utf-8') as f:
		f.readline() # skip line 1
		while True:
			line = f.readline()
			if not line:
				break
			#elif line.strip()=="":
			#	continue
			line=line.split('\t')
			line[-1]=line[-1].rstrip() #Strip newline char
			try:
				tID = int(line[0])
				TEXTMAPMAN.full[tID] = line[1:] #Discard 1st column (the ID)
				#if line[-1] != "" and line[-1] != "XXX":
				#	#Replace characters from renpy
				#	TextMap[tID] = line[-1].replace("{","<").replace("}",">").replace("\\n","//n")
			except:
				print("Encountered bad line: "+str(line))
				#print(line)
	#print(len(TextMapFull))
	#print(len(TextMap))
else:
	print("Run convertToInterpreter.py in the build tools to generate TextMap_aio.tsv!!")
	sys.exit(1)

for lang in TEXTMAPMAN.langs.keys():
	fName ="TextMap_retranslated_"+lang+".json"
	if os.path.exists(fName):
		with open(fName,'r') as f:
			TEXTMAPMAN.langs[lang] = json.loads(f.read())
			#TEXTMAPMAN.langs[lang]["LANGUAGE"]=lang
			#print(TEXTMAPMAN.langs[lang])
	else:
		print("The textmap for language "+lang+" does not exist. If this is the first run, ignore this message.")
			


def write_database():
	for lang in TEXTMAPMAN.langs.keys():
		if len(TEXTMAPMAN.langs[lang])==0:
			continue
		fName ="TextMap_retranslated_"+lang+".json"
		with open(fName,'wb') as f:
			#print(TEXTMAPMAN.langs[lang])
			f.write(json.dumps(TEXTMAPMAN.langs[lang], sort_keys=False, separators=(',', ': '), indent='\t', ensure_ascii=False).encode('utf8'))
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
async def defaultGet():
	return b"<html>No language was specificed, please append /en_re or /pt after the URL query to get the translation.</html>",400

@quartServer.route("/<lang>", methods=['GET'])
async def getTranslation(lang):
	if lang not in TEXTMAPMAN.langs:
		return b"<html>Invalid language key. Only /en_re and /pt are available.</html>",400
	return json.dumps(TEXTMAPMAN.langs[lang],ensure_ascii=False).encode()

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
	lang="en_re"
	if "API_KEY" in newTextMap:
		API_KEY = (newTextMap["API_KEY"] == config['override_password'])

	if "LANGUAGE" in newTextMap:
		if newTextMap["LANGUAGE"] not in TEXTMAPMAN.langs:
			return b'Nice try, but your language key is invalid.',400
		lang=newTextMap["LANGUAGE"]
	else:
		return b'Your textmap is missing the LANGUAGE key, redownload it!'
	
	for fakeKey in newTextMap:
		if fakeKey == "API_KEY" or fakeKey=="LANGUAGE":
			continue
		elif newTextMap[fakeKey].strip() == "":
			continue

		k = int(fakeKey)
		newText = newTextMap[fakeKey].strip().replace("\n","//n") #We should be removing junk like trailing '\n's.

		if k not in TEXTMAPMAN.full:
			#print(type(k))
			return bytes('Invalid key '+str(k)+' in client submission.',"utf-8"),400
		elif k not in TEXTMAPMAN.langs[lang]:
			TEXTMAPMAN.setNewKey(lang,k,newText)
			
			origLang = TEXTMAPMAN.getOrigLang(lang)
			botMessage+= "\n["+fakeKey+"] `"+TEXTMAPMAN.full[k][origLang]+"` -> `"+newText+"`"
			keysAdded+=1
		elif k in TEXTMAPMAN.langs[lang] and TEXTMAPMAN.langs[lang] == newText: #Same as old key, ignore it
			pass
		else: #If already exists in the text map
			if API_KEY:
				botMessage += "\n["+fakeKey+"]: `"+TEXTMAPMAN.langs[lang][k]+"` -> `"+newText+"`"
				TEXTMAPMAN.setNewKey(lang,k,newText)
				keysAdded+=1
			else:
				botMessage += "\n["+fakeKey+"] No API key, can't approve change: `"+TEXTMAPMAN.langs[lang][k]+"` -> `"+newText+"`"
	try:
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
	except:
		pass
	
	if keysAdded==0:
		return b'There have been no keys added, your submission was discarded.',200
	return b'Success.', 200

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
async def override_key(ctx, 
	lang: discord.commands.Option(
		str,
		"Language to overwrite",
		choices=["en_re","pt"],
		default="en_re"
	),
	key: int,
	new_text:str
	):
	if key not in TEXTMAPMAN.full:
		await ctx.respond("This key does not exist in the database.")
		return
	TextMap = TEXTMAPMAN.langs[lang]
	if key in TextMap:
		msg = "Updated retranslated text:\n"
		msg +="["+str(key)+"] `"+TextMap[key]+"` -> `"+new_text+"`"
		TEXTMAPMAN.setNewKey(lang,key,new_text)
		await ctx.respond(msg)
	else:
		msg = "Added new translation for language "+lang+":\n"
		TEXTMAPMAN.setNewKey(lang,key,new_text)
		msg +="["+str(key)+"] `"+TEXTMAPMAN.full[key][TEXTMAPMAN.getOrigLang(lang)]+"` -> `"+new_text+"`"
		await ctx.respond(msg)

@bot.slash_command(guild_ids=[discordGuild])
async def delete_key(ctx, 
	lang: discord.commands.Option(
		str,
		"Language to overwrite",
		choices=["en_re","pt"],
		default="en_re"
	),
	key:int
	):
	TextMap = TEXTMAPMAN.langs[lang]
	if key in TextMap:
		TextMap.pop(key)
		#TEXTMAPMAN.full[key][TEXTMAPMAN.columns[]]="XXX"
		await ctx.respond("Deleted "+str(key)+" from database.")
	else:
		await ctx.respond("This key wasn't found in the database.")

@bot.slash_command(guild_ids=[discordGuild])
async def search_orig_text(ctx,  
	lang: discord.commands.Option(
		str,
		"Language to overwrite",
		choices=['en','cn','jp','kr'],
		default="en"
	),
	search:str
	):
	await ctx.respond("Please wait... (Discord is garbage and slash commands must respond within 3 seconds)")
	print("Searching for "+search)
	col = TEXTMAPMAN.getLangColumn(lang)
	tmp_en = {k:TEXTMAPMAN.full[k][col] for k in TEXTMAPMAN.full}
	res = process.extract(search, tmp_en, limit=3)
	print("Got result!")
	print(res)
	msg = "Results:"
	numLength = 0
	for r in res:
		numLength=max(int(math.log10(r[2]))+1,numLength)
	#print(numLength)
	for r in res:
		#msg+="\n"+str(r[2])+" "+r[0]
		#msg += "\n"+"%"+str(numLength)+'s'
		msg += ("\n`{:<"+str(numLength)+"}` ").format(r[2])+r[0]
	message_channel = bot.get_channel(discordChannel)
	await message_channel.send(msg)

@bot.slash_command(guild_ids=[discordGuild])
async def get_key(ctx, 
	#lang: discord.commands.Option(
	#	str,
	#	"Language to get key from, or \'all\' for all translations of a key.",
	#	choices=["all","en_re","pt",'en','cn','jp','kr'],
	#	default="en_re"
	#),
	key:int):
	ALL_LANGUAGES = ["all","en_re","pt",'en','cn','jp','kr']
	if key not in TEXTMAPMAN.full:
		await ctx.respond("This key does not exist in the database.")
		#return
	else:
		v = {}
		for i in range(len(TEXTMAPMAN.columns)):
			v[TEXTMAPMAN.columns[i]]=TEXTMAPMAN.full[key][i]
		for l in TEXTMAPMAN.langs.keys():
			if key in TEXTMAPMAN.langs[l]:
				v[l]=TEXTMAPMAN.langs[l][key]
		msg = "All text for key "+str(key)+":\n```ini"
		for k in v:
			msg+="\n["+k+"] "+v[k]
		msg+="```"
		await ctx.respond(msg)
		#return
	# elif lang not in ALL_LANGUAGES:
	# 	await ctx.respond("Invalid language specified, somehow. Only "+str(ALL_LANGUAGES)+" are valid languages.")
	# 	#return
	# else:
	# 	TextMap = TEXTMAPMAN.langs[lang]
	# 	origCol = TEXTMAPMAN.getLangColumn(lang)
	# 	#newCol = TEXTMAPMAN.getOrigLang(lang)
	# 	if key in TextMap and key in TEXTMAPMAN.full:
	# 		await ctx.respond(str(key)+"\nOriginal: "+TEXTMAPMAN.full[key][origCol]+"\nRetranslated: "+TEXTMAPMAN.langs[lang][key])
	# 	else:
	# 		await ctx.respond(str(key)+"\nOriginal: "+TEXTMAPMAN.full[key][origCol])


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
		traceback.print_exc()
		#print(e)
	
@bot.event
async def on_ready():
	print("The bot is ready!")
	#print(str(client.user.id))
	#https://discordapp.com/oauth2/authorize?client_id=351447700064960522&scope=bot&permissions=0
	#Send Messages, Manage Messages, Embed Links, and Add Reactions is required for optimal use.
	#https://discord.com/api/oauth2/authorize?client_id=675916321594015746&permissions=18432&scope=bot%20applications.commands
	print("Add me with https://discord.com/oauth2/authorize?client_id="+str(bot.user.id)+ "&permissions=18432&scope=bot%20applications.commands")
	#await client.change_presence(status=discord.Status.online, activity=discord.Game(serverCount()))

bot.loop.create_task(quartServer.run_task('0.0.0.0',port=8880))
job.start()
bot.run(config['discord_token'])
