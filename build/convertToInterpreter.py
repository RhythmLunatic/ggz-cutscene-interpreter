#!/usr/bin/env python3.8
from cgitb import text
import json as JSON
import sys
import os
from typing import Dict,List,Any, Union, Literal
from xml.etree.ElementTree import PI
"""
DialogueID	Type	UnLockLevelID	DialogueText	Repeatable	ChoiceID	RoleID	RoleStorySide	faceid	RoleMotion	isMotionFirst	RoleDelay	ItemShowCaseID	CGID	BGID	EffectID	isEffectFirst	EffectDelay	EffectDuration	SoundID	SoundDelay	SoundDuration	BGMID
1	0	0	TEXT30001	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0

DialogueID = Seems to be used for story purposes, first stage is 2, second stage is 3, etc
Type = Unknown.
UnLockLevelID = Unkown.
DialogueText = Key to look up in TextMap.tsv
Repeatable = Unknown boolean
ChoiceID = Unknown
RoleID= ID to look up in StoryFigueSettingData.tsv
RoleStorySide = 0 for left, 1 for right
faceid = unknown
RoleMotion = unknown, probably an ID for an animation to apply to portraits.
isMotionFirst = Unknown, also it can be 2?
CGID = points to a PNG file
BGID = points to a PNG file
"""

def RepresentsInt(s):
	try: 
		int(s)
		return True
	except ValueError:
		return False

print("Plz wait, loading all text!")
textMap:Dict[int,List[Any]] = {}


if os.path.exists("TextMap_aio.tsv"):
	with open("TextMap_aio.tsv",'r') as f:
		f.readline() # skip line 1
		while True:
			line = f.readline()
			if not line:
				break
			line=line.split('\t')
			line[-1]=line[-1].rstrip() #Strip newline char
			textMap[int(line[0])]=line[1:]
else:
	with open(os.path.join("GameData","TextMap_cn.tsv"),'r') as f:
		f.readline() # skip line 1
		while True:
			line = f.readline()
			if not line:
				break
			line=line.split('\t')
			line[-1]=line[-1].rstrip() #Strip newline char
			textMap[int(line[0])]=line[1:]
			
	if True:
		#TEXT_ID	EN	CN	JP	KR	TCN
		files = {1:"TextMap_en.tsv",3:"TextMap_jp.tsv"}
		for column in files: 
			with open(os.path.join("GameData",files[column]),'r') as f:
				f.readline() # skip line 1
				while True:
					line = f.readline()
					if not line:
						break
					line=line.split('\t')
					if len(line)<4 or not line[0].strip():
						print("Skipping invalid line with wrong number of text")
						print(line)
						continue
					textID = int(line[0])
					if textID not in textMap:
						textMap[textID]=['XXX']*5
					#print(textID)
					#print(textMap[textID])
					textMap[textID][column-1]=line[column]
		with open("TextMap_aio.tsv","w") as f:
			f.write("TEXT_ID	EN	CN	JP	KR	TCN\n")
			for textID in textMap:
				f.write(str(textID)+"\t"+"\t".join(textMap[textID])+"\n")


for fn,n in {"TextMap_retranslated_en_re.json":3, "TextMap_retranslated_pt.json":4}.items():
	if os.path.exists(fn):
		with open(fn,'r',encoding='utf8') as f:
			textMap_retranslated = JSON.loads(f.read())
			for fakeID in textMap_retranslated:
				if fakeID=="LANGUAGE":
					continue
				tID = int(fakeID)
				if tID in textMap:
					textMap[tID][n] = textMap_retranslated[fakeID].replace("{","<").replace("}",">")
			print("Added "+fn+" to column "+str(n))
#sys.exit(-1)
#Remove "XXX"
for _id in textMap:
	for i in range(len(textMap[_id])):
		if textMap[_id][i] == "XXX":
			textMap[_id][i]=None
		
print("Now loading portrait information....")


"""
ID	PNGName	DevY	StorySide	FigueName	FacePosition	FlipOnOtherSide	Scale
0	图片路径	立绘y轴的偏移	非九霄中人物的默认站位，1为左，2为右	人物名字	脸的位置（替换）	当立绘放在storyside另一边时，是否翻转	大小
Picture path	The offset of the y-axis of the vertical picture	is not the default position of the characters in Jiuxiao, 1 is left, 2 is the right	Character name	Position of the face (replacement)	When the vertical picture is placed on the other side of the storyside, whether to flip	the size
int	string	float	int	int	List<float>	bool	float
"""
class StoryFigureSettingDataStruct():
	def __init__(self, info):
		self.pic=info[1]
		self.DevX=info[2]
		self.DevY=info[3]
		self.StorySide=int(info[4])    #What the fuck is this even for???
		self.SpeakerName=int(info[5])  #This is a TextID, pulled from textMap_en
		                               #x,y coords of replacement face
		self.FacePosition=[round(float(h)) for h in info[6].split(";")]
		self.FlipOnOtherSide=(info[7]=="1")
		self.Scale=float(info[8])

	def getNormalizedFacePosition(self):
		return (self.FacePosition[0]-128,1024-self.FacePosition[1]-128)
		

storyFigueSettingData:Dict[int,StoryFigureSettingDataStruct] = {}
with open(os.path.join("GameData","StoryFigueSettingData.tsv"),'r') as f:
	f.readline() # skip first four lines, I don't know why they're here
	f.readline()
	f.readline()
	f.readline()
	while True:
		line = f.readline()
		if not line:
			break
		info=line.split('\t')
		
		storyFigueSettingData[int(info[0])]=StoryFigureSettingDataStruct(info)
print("done.")

#commandsList = []

def getLastCommandOf(commandsList:list,opcode:str)->Union[None,List[Any]]:
	"""Given a list of opcodes and the type to search, return the last opcode of the type specified."""
	for i in range(len(commandsList)-1,-1,-1):
		if commandsList[i][0]==opcode:
			return commandsList[i]
		#else:
		#	print(commandsList[i][0]+" != "+t)
	return None
	
#lol
def getOpp(i:Literal[1,2]):
	return 2 if i==1 else 1

emptyPortrait = ['',0,False]
#def shouldDimThis(thisPosition,

def getStoryTSV(fileName:str)->Dict[int,List[str]]:
	"""Converts a story TSV into a dict of lists, with the dict being indexed by the part ID. Lines not starting with a number will be ignored.
	
	After conversion it looks something like this:
	{
		1:[
			[TEXT10000,aaa,bbbb],
			[TEXT123131223, ccccc dddddd]
		],
		2:[
			...
		],
		...
	}
	"""
	with open(os.path.join("GameData",fileName),'r') as storyData:
		storyData.readline()
		lastPart = -1
		unconvertedData = {}
		while True:
			l = storyData.readline()
			if not l.strip():
				print("Hit the end at part "+str(lastPart))
				break
			StoryTextV2 = l.split("\t")
			if not RepresentsInt(StoryTextV2[0]):
				print("Ignoring bad line "+str(StoryTextV2))
				continue
			curPart = int(StoryTextV2[0])
			if curPart not in unconvertedData:
				unconvertedData[curPart] = [StoryTextV2]
			else:
				unconvertedData[curPart].append(StoryTextV2)
			lastPart=curPart
	return unconvertedData

#unconvertedLines_Main = getStoryTSV('StoryMainData.tsv')
unconvertedLines_Sub = getStoryTSV('StorySubData.tsv')
unconvertedLines_Ext = getStoryTSV('StoryExtData.tsv')
unconvertedLines_Inside = getStoryTSV('StoryInsideData.tsv')
unconvertedLines_Kyusyo = getStoryTSV('KyusyoStoryData.tsv')
unconvertedLines_DLC2 = getStoryTSV('DLCStoryData.tsv')

#sys.exit(0)
class StoryDataStruct():
	"""Convert a StoryData list into a struct.
		_type: If 0 (default), column 3 is the text.
		If 1, column 1 is the text.
	"""
	def __init__(self, StoryTextV2:List[str], _type=0):
		#self.DialogueID = int(l[0])
		if _type == 1: #PlaybackStoryData
			if RepresentsInt(StoryTextV2[1]):
				self.text = int(StoryTextV2[1])
			else:
				print("Unimplemented opcode! "+StoryTextV2[1]+" is not an integer.")
				print(StoryTextV2)
				self.text = -1
			self.RoleID = int(StoryTextV2[2])
			self.PortraitPosition:Literal[1,2] = 2 if (StoryTextV2[3]=="1") else 1
			self.RoleFace = int(StoryTextV2[4])
			#self.RoleMotion = int(StoryTextV2[5])
			#self.isMotionFirst = StoryTextV2[6] == "1"
			self.CGID = StoryTextV2[9]
			self.BGID = StoryTextV2[10]

			self.ChoiceID=0
		elif _type == 2: #PartnerStoryData

			# self.text=int(StoryTextV2[2][4:])
			# self.RoleID=int(StoryTextV2[1])
			# self.RoleFace=int(StoryTextV2[3])

			# self.CGID=''
			# self.BGID=''
			# #This does nothing, type 2 only ever has two portraits and they're always defined
			# self.PortraitPosition=1
			pass
		else: #Type 0, kyusyo, era zero, extdata, etc uses this one
			#DialogueID	Type	UnLockLevelID	DialogueText	Repeatable	ChoiceID	RoleID	RoleStorySide	face	RoleMotion	isMotionFirst	RoleDelay	ItemShowCaseID	CGID	BGID	EffectID	isEffectFirst	EffectDelay	EffectDuration	SoundID	SoundDelay	SoundDuration	BGMID

			if len(StoryTextV2[3]) > 4:
				if RepresentsInt(StoryTextV2[3]):
					self.text = int(StoryTextV2[3])
				else:
					self.text = int(StoryTextV2[3][4:])
			else:
				print("Unimplemented opcode! Text length is missing TEXT "+StoryTextV2[3])
				print(StoryTextV2)
				self.text=-1
			self.ChoiceID:int = int(StoryTextV2[5])
			self.RoleID = int(StoryTextV2[6])
			self.PortraitPosition:Literal[1,2]=2 if (StoryTextV2[7]=="1") else 1 #Determines which portrait to highlight in this text
			self.RoleFace=int(StoryTextV2[8])
			self.CGID=StoryTextV2[13]
			self.BGID = StoryTextV2[14]
			if _type==3: #Kyusyo only
				self.EffectID = int(StoryTextV2[15])

	
		if self.BGID=="0":
			self.BGID="black"


portraitBlacklist = [0,802,803,804,805] #Portraits without an image

class StoryChoiceData():
	def __init__(self,info) -> None:
		#Only used once, so it doesn't really matter
		#self.ChoiceTitle = textMap[int(info[1])]
		self.Choice1Text = [int(info[2])]+textMap[int(info[2])]
		self.Choice2Text = [int(info[3])]+textMap[int(info[3])]
		self.Choice1Story:int = int(info[4])
		self.Choice2Story:int = int(info[5])
		#This is mostly irrelevant
		self.MergedStory:int = int(info[6])

#Hueristic to skip parts that exist in the playback archive
allUsedLinesSoFar = []

def convertPart(section:dict,partNumber:int,_type=0,choiceDatas:Union[Dict[int,StoryChoiceData],None]=None)->List[List[Any]]:
	"""Given a dict containing all the unconverted lines and the part to convert, return a list of structured opcodes."""
	commandsList = []
	if partNumber not in section:
		print("MISSING ID "+str(partNumber)+"!!!!")
		return commandsList
	linesToConvert = section[partNumber]
	for UnConvStoryTextV2 in linesToConvert:
		StoryTextV2 = StoryDataStruct(UnConvStoryTextV2,_type)
		
		#So GGZ didn't support centered portraits until really late
		#[portrait,variant,shouldDim]
		
		lastCmd = getLastCommandOf(commandsList,'portraits')
		if not lastCmd:
			#print("No last cmd")
			newCmd=['portraits',emptyPortrait,emptyPortrait]
		else:
			#print(lastCmd)
			newCmd = ['portraits',lastCmd[1].copy(),lastCmd[2].copy()]
			
		#If opposite side exists, dim it
		if newCmd[getOpp(StoryTextV2.PortraitPosition)][0]!='':
			newCmd[getOpp(StoryTextV2.PortraitPosition)][2]=True
		#
		if StoryTextV2.RoleID in portraitBlacklist: 
			newCmd[StoryTextV2.PortraitPosition]=emptyPortrait
			# Ok but we still have to set the speaker!!
			pInfo = storyFigueSettingData[StoryTextV2.RoleID] 
			lastSpeakerName = getLastCommandOf(commandsList,'speaker')
			if not lastSpeakerName or lastSpeakerName[1] != pInfo.SpeakerName:
				commandsList.append(['speaker', pInfo.SpeakerName ])

		elif StoryTextV2.RoleID < 0:
			#print("Ignoring unknown RoleID: "+str(RoleID))
			pass
		else:
			if StoryTextV2.RoleID in storyFigueSettingData:
				pInfo = storyFigueSettingData[StoryTextV2.RoleID]
				#RoleFace 1 is identical to 0, but the story portrait database generator handles this anyways
				newCmd[StoryTextV2.PortraitPosition]=[StoryTextV2.RoleID,StoryTextV2.RoleFace,False]
				lastSpeakerName = getLastCommandOf(commandsList,'speaker')
				if not lastSpeakerName or lastSpeakerName[1] != pInfo.SpeakerName:
					commandsList.append(['speaker', pInfo.SpeakerName ])
			else:
				print("ID "+str(StoryTextV2.RoleID)+" does not exist in portrait/name DB")
				commandsList.append(['speaker', str(StoryTextV2.RoleID)+" (Update portrait DB!!)" ])
			
		if StoryTextV2.CGID != "0":
			newCmd=['portraits',emptyPortrait,emptyPortrait]
			lastBGcmd = getLastCommandOf(commandsList,'bg')
			if not lastBGcmd or (lastBGcmd and lastBGcmd[1]!= StoryTextV2.CGID): #Skip duplicates
				commandsList.append(['bg',StoryTextV2.CGID])
		else:
			lastBGcmd = getLastCommandOf(commandsList,'bg')
			#print(lastBGcmd)
			#if lastBGcmd:
			#	print(lastBGcmd[1]==StoryTextV2.BGID)
			if lastBGcmd and lastBGcmd[1] != StoryTextV2.BGID: #Skip duplicates
				#if StoryTextV2.BGID=="0":
				#	StoryTextV2.BGID="black"
				print("Pushed new BG "+StoryTextV2.BGID)
				commandsList.append(['bg',StoryTextV2.BGID])
			elif lastBGcmd==None and StoryTextV2.BGID!="black":
				print("No previous BG, adding "+StoryTextV2.BGID)
				commandsList.append(['bg',StoryTextV2.BGID])
				
			#else:
			#	commandsList.append(['bg','black'])
			
		
		#print(newCmd)
		if lastCmd!=newCmd:
			#print(lastCmd,end='')
			#print("!=",end='')
			#print(newCmd)
			commandsList.append(newCmd)
		else:
			#print(lastCmd,end='')
			#print("==",end='')
			#print(newCmd)
			#commandsList.append(newCmd)
			pass
		
		#if StoryTextV2.

		if StoryTextV2.text > 0 and StoryTextV2.text in textMap:
			allUsedLinesSoFar.append(StoryTextV2.text)
			commandsList.append(['msg']+[StoryTextV2.text]+textMap[StoryTextV2.text]) # type: ignore
		else:
			print("ID "+str(StoryTextV2.text)+" not present in text db, assuming command with no message")
		if StoryTextV2.ChoiceID != 0 and choiceDatas!= None:
			#print(StoryTextV2.ChoiceID)
			c = choiceDatas[StoryTextV2.ChoiceID]
			commandsList.append(['choice',c.Choice1Text,c.Choice2Text])
			if c.Choice1Story and c.Choice2Story:
				commandsList.append(['nop','CHOICE_DESTS',c.Choice1Story,c.Choice2Story])
			#print(StoryTextV2)
	return commandsList

def writeAndReturnPart(parts:dict,name:str,fileName:str,partNames:Union[list,None]=None)->dict:
	"""Writes the parts to disk, then returns a dict with the information for the database.
	"""
	with open("../avgtxt/"+fileName,'wb') as f:
		f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
		print("Generated "+fileName)

	d = {
		"name":name,
		"parts":fileName
	}
	if partNames:
		d["part_names"]=partNames # type: ignore
	return d

story = {
	"main":[
		{
			"name":"Prologue",
			"episodes":[
				{
					"name":"Prologue",
					"parts":"prologue.json"
				}
			]
		},
		
	],
	"side":[],
	"event":[],
	"crossover":[]
}


#Prologue... Not in the playback archive for some reason.
#Additionally, 1152 runs before 1135 as seen on YouTube but this might be a glitch.
parts = {
	"1":convertPart(unconvertedLines_Ext,1152),
	"2":convertPart(unconvertedLines_Ext,1135),
}
with open("../avgtxt/prologue.json",'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))



#LevelMetaV2 is not understood, but it contains information about levels...
#To get descriptions we'll just reverse search the title
class LevelMetaV2Struct():
	def __init__(self,info) -> None:
		d=info.split("\t")
		if "TEXT" in d[8]:
			tmp=int(d[8][4:])
			if tmp in textMap:
				self.ChapterTitle=[tmp]+textMap[tmp]
			else:
				self.ChapterTitle=[str(tmp)]
		else:
			self.ChapterTitle=[0,d[8]]
		if "TEXT" in d[9]:
			tmp=int(d[9][4:])
			self.ChapterDescription=[tmp]+textMap[tmp]
		else:
			self.ChapterDescription=[0,d[9]]

		tmp=d[11]
		if "TEXT" in tmp:
			tmp=int(tmp[4:])
			if tmp in textMap:
				self.StageName:str=textMap[tmp][0]
			else:
				self.StageName:str=""
		else:
			self.StageName:str=tmp
		pass
LevelMetaV2s:List[LevelMetaV2Struct]=[]
with open("GameData/LevelMetaV2.tsv",'r') as f:
	f.readline()
	while True:
		l=f.readline()
		if not l:
			break
		#I don't think there's any repeated IDs, but regardless we don't care about IDs right now
		LevelMetaV2s.append(LevelMetaV2Struct(l))
#print(LevelMetaV2s[0])

def getLevelMetaFromChapterTitleID(chID:int):
	#print("Searching for "+str(chID))
	for lm in LevelMetaV2s:
		if chID==lm.ChapterTitle[0]:
			#print("Return "+str(lm.ChapterDescription[0]))
			return lm
	#raise KeyError("Chapter ID "+str(chID)+" not present in LevelMetaV2.")
	return None


#All stories in the playback archive.
unconvertedLines_Playback = getStoryTSV('PlayBackStoryData.tsv')

# Search for matching chapter name
def getIndexFromKey(k:str):
	for i in range(len(story['main'])):
		if story['main'][i]['episodes'][0]['parts'].startswith("type-"+k):
			return i
	return -1


#ID	Type	ExType	ExTitle	ExTitleText	SeasonID	SeasonTitle	SeasonText	BannerID	BannerTitle	BannerText	Title	TitleText	DialogueID	IsSub	UnlockLevel
class PlayBackStoryTitleDataStruct():
	def __init__(self,info) -> None:
		d = info.split("\t")
		#Story types:
		#1 = Main?
		#2 = Side stories? Halloween event is here?
		self.StoryType = int(d[1])
		self.ExType = int(d[2]) #Seems to control grouping. Genkai Room and Mysterious Deep are supposed to be in the same group and are both Group 6.
		tmp = int(d[3]) #The chapter title, but I'm not sure how it's determined when there are two different titles in the same group.
		self.StoryTitle:list =[tmp]+textMap[tmp]
		#Column 4 seems to be unused
		self.EpisodeNumber = int(d[5])
		self.EpisodePrefix = int(d[6]) #Episode 1, Episode 2, etc. Or Chapter 1, Chapter 2, etc
		#Column 7 is unused
		#Column 8 is irrelevant (Just the graphic to display in-game)
		self.EpisodeTitle = int(d[9])
		#Column 10 is unused
		self.PartName = int(d[11]) #Segment 1, Segment 2, etc. Sometimes there's names though
		#Column 12 is unused
		self.DialogueID = int(d[13]) #part to pull from in PlaybackStoryData
		self.IsSub = d[14]=="1" #Marks extra chapters
	
	def getChapterName(self)->str:
		if self.EpisodePrefix==self.EpisodeTitle:
			return textMap[self.EpisodePrefix][0]
		else:
			return textMap[self.EpisodePrefix][0]+": "+textMap[self.EpisodeTitle][0]

playbackData = []
with open(os.path.join("GameData",'PlayBackStoryTitleData.tsv'),'r') as storyDatabase:
	storyDatabase.readline()
	storyDatabase.readline()
	storyDatabase.readline()
	storyDatabase.readline()
	while True:
		l = storyDatabase.readline()
		if not l.strip():
			break
		playbackData.append(PlayBackStoryTitleDataStruct(l))

def writePlaybackData():
	parts = {}

	for i in range(len(playbackData)):
		#lastData = playbackData[i]
		thisData:PlayBackStoryTitleDataStruct = playbackData[i]
		
		newPart = convertPart(unconvertedLines_Playback,thisData.DialogueID,1)
		if newPart:

			#Add to parts dict, contains the data for this part.
			parts[thisData.DialogueID]=newPart
			if thisData.DialogueID==91:
				parts[thisData.DialogueID].insert(0,['bgm','The Sound of the End'])
			elif thisData.DialogueID==54 or thisData.DialogueID==57:
				parts[thisData.DialogueID].insert(0,['bgm','Amusement Park'])
			elif thisData.DialogueID==89:
				parts[thisData.DialogueID].insert(0,['bgm','The Sound of the End Quiet'])


		if i==len(playbackData)-1 or thisData.EpisodeNumber != playbackData[i+1].EpisodeNumber:
			if parts:
				fileName = "type-"+str(thisData.StoryType)+"-"+str(thisData.ExType)+"-chapter-"+str(thisData.EpisodeNumber)+'-'+str(thisData.DialogueID)+'.json'
				print(parts.keys())
				with open("../avgtxt/"+fileName,'wb') as f:
					f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
					print("Generated "+fileName+" containing "+str(len(parts)))

				idx = getIndexFromKey(str(thisData.StoryType)+"-"+str(thisData.ExType))
				if idx==-1:
					story['main'].append({
						"name":thisData.StoryTitle[1],
						"nameMultilang":thisData.StoryTitle,
						#"shortName":"HG2 x GFL",
						"episodes":[]
					})
					idx=len(story['main'])-1
				story['main'][idx]['episodes'].append({
					"name":thisData.getChapterName(),
					"parts":fileName
				})
				lm = getLevelMetaFromChapterTitleID(thisData.EpisodeTitle)
				if lm:
					#TODO: Description doesn't support multilanguage yet
					if lm.ChapterDescription[4]:
						story['main'][idx]['episodes'][-1]['description']=lm.ChapterDescription[4]
					else:
						story['main'][idx]['episodes'][-1]['description']=lm.ChapterDescription[1]
				elif thisData.DialogueID == 284:
					story['main'][idx]['episodes'][-1]['description']="It is highly recommended for you to read Sin's manga chapters first for context in part 6: https://mangadex.org/chapter/b75c6a9f-324e-4356-99db-8c19ae54c2fa/1"
			parts={}

writePlaybackData()
#sys.exit(0)

#Now we do the Fire Moth DLC!
class KyusyoMissionDataStruct():
	def __init__(self,info) -> None:
		d = info.split("\t")
		self.MissionID = int(d[0])
		self.ParentID = [int(a) for a in d[1][:-1].split(';')]
		#d[2] is useless
		#self.ParentStoryID = int(d[3])
		#MarkForMemoryID = d[4]
		#ShowType: Main line = 1, branch line = 2
		#self.ShowType = int(d[5])
		
		# 1 general; 2 limited time; 3 daily; 4 weekly reset;
		#self.DependType = int(d[6])
		#LevelRequiredMin = d[7]
		#LevelRequiredMax is never used (d[8])
		self.MissionName = textMap[int(d[9])][0]
		if d[10] != "0":
			txtArr = textMap[int(d[10])]
			#if textArr[5]:
			self.MissionDesc = txtArr[3] if txtArr[3] else txtArr[0]
		else:
			self.MissionDesc=""

		#If ParentID is 999 this isn't a range, but it seems like
		#the next ID is used in a different part
		#If StoryIDEnd is 0, I have no idea what happens.
		#Since the end tag makes no sense, I'm just going to guess by finding the next closest start.
		self.StoryIDStart = int(d[11])
		self.StoryIDEnd = int(d[12])
		# "Story id triggered after being set as a recall item"... Whatever that means.
		self.StoryIDMemory = int(d[13])
		self.ChapterNum = int(d[16])

kyusyoMissionDatas = []
with open("GameData/KyusyoMissionData.tsv",'r') as f:
	f.readline()
	f.readline()
	f.readline()
	f.readline()
	while True:
		l = f.readline()
		if not l.strip():
			break
		kyusyoMissionDatas.append(KyusyoMissionDataStruct(l))

KyusyoChoicePartsList:Dict[int,StoryChoiceData] = {}
with open("GameData/KyusyoStoryChoiceData.tsv",'r') as f:
	f.readline()
	f.readline()
	f.readline()
	f.readline()
	while True:
		l = f.readline()
		if not l.strip():
			break
		t=l.split("\t")
		KyusyoChoicePartsList[int(t[0])]=StoryChoiceData(t)

KyusyoStoryPartsList = []
for mission in kyusyoMissionDatas:
	KyusyoStoryPartsList.append(mission.StoryIDStart)
KyusyoStoryPartsList.sort()
#print(KyusyoStoryPartsList)
#sys.exit(0)

def getNextClosestEndPart(start:int)->int:
	if start==0:
		return 17 #Because it will skip the first index... Yeah it's dumb
	for n in KyusyoStoryPartsList:
		if start > n or start==n:
			#print(str(start)+" < "+str(n))
			continue
		else:
			#print("Closest to "+str(start)+" is "+str(n))
			return n
	return KyusyoStoryPartsList[-1]

def writeFireMothData():
	#ConvertedKyusyoData = []
	for i in range(8):
		story['side'].append({
			"name":"Chapter "+str(i), #Yes it starts on chapter 0 lol
			"episodes":[]
		})
	story['side'].append({
		"name":"Unused data?",
		"episodes":[]
	})
	for i in range(len(kyusyoMissionDatas)):
		thisMission:KyusyoMissionDataStruct = kyusyoMissionDatas[i]
		parts = {}
		#print("START: "+str(thisMission.StoryIDStart)+" | END: "+str(getNextClosestEndPart(thisMission.StoryIDStart)))
		#Mission has no story?
		if thisMission.StoryIDStart==0:
			continue
		elif thisMission.MissionID==2: #First mission
			thisMission.StoryIDStart=0
		for j in range(thisMission.StoryIDStart,getNextClosestEndPart(thisMission.StoryIDStart)):
			if j in unconvertedLines_Kyusyo:
				parts[j] = convertPart(unconvertedLines_Kyusyo,j,0,KyusyoChoicePartsList)
				if j==223:
					parts[j].insert(0,['bgm',"Significance"]) #Faltering Prayer - Dawn Breeze might also work?
				elif j==226:
					parts[j].insert(0,['bgm','Blissful Death'])
				elif j==227:
					parts[j].insert(0,['bgm',"Faltering Prayer - Starry Sky"])
				elif j==228:
					parts[j].insert(0,['bgm',"Faltering Prayer - No Vocals"])
				elif j==242:
					parts[j].insert(0,['bgm',"Weight of the World - No Vocals"])
			#else:
			#	print("No DialogueID "+str(j))
		print(parts.keys())
		if parts:
			fName = "StoryKyusyoData-chapter-"+str(thisMission.ChapterNum)+"-"+str(thisMission.MissionID)+'.json'
			
			toAdd = thisMission.ChapterNum
			if thisMission.StoryIDEnd > 900 and thisMission.StoryIDEnd < 1000:
				#Not sure how this works, but these parts exist
				parts[thisMission.StoryIDEnd] = convertPart(unconvertedLines_Kyusyo,thisMission.StoryIDEnd)
				toAdd=8

			part_names = list(parts.keys())
			#print(part_names)
			for pn in range(len(part_names)):
				for c in KyusyoChoicePartsList.values():
					#print(c.Choice1Story)
					if c.Choice1Story==part_names[pn]:
						#print(str(part_names[pn])+" == "+str(c.Choice1Story))
						part_names[pn]="If choice 1 was picked:"
						#sys.exit(0)
					elif c.Choice2Story==part_names[pn]:
						part_names[pn]="If choice 2 was picked:"

			story['side'][toAdd]['episodes'].append({
				"name":thisMission.MissionName,
				"parts":fName,
				"part_names":part_names
			})
			if thisMission.MissionDesc != "":
				story['side'][thisMission.ChapterNum]['episodes'][-1]["description"]=thisMission.MissionDesc
			with open("../avgtxt/"+fName,'wb') as f:
				f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
				print("Generated "+fName)

	#I think we have every single part, so this isn't necessary
	"""unknownKyusyoData = []
	for i in range(0,14):
		parts = {}
		for j in range(i*10,i*10+10):
			if j in unconvertedLines_Kyusyo:
				parts[j]=convertPart(unconvertedLines_Kyusyo,j)
			else:
				print("No DialogueID "+str(j))
		print(parts.keys())
		
		if parts: #Do not add empty data
			unknownKyusyoData.append(writeAndReturnPart(
				parts,
				"Parts "+str(i*10)+"-"+str(i*10+9),
				"StoryKyusyoData-unk-"+str(i)+'.json',
				list(parts.keys())
			))
			
	story['side'].append({
		"name":"Unknown Kyusyo Data",
		"episodes":unknownKyusyoData
	})"""
#writeFireMothData()
#sys.exit(0)


#Era ZERO... Which was cancelled, by the way. There's nothing after the first two chapters.
class DLC2MissionData():
	def __init__(self,info) -> None:
		d = info.split("\t")
		self.MissionName=textMap[int(d[0])][0]
		self.MissionDesc=textMap[int(d[1])][0]
		self.StoryIDEnd=int(d[2])

def writeDLC2Data():
	#The real database is stupid so here's a modified one with the correct information.
	#The third column is the end, and it goes until the end of the previous column.
	#I might have gotten it wrong since there's no guarentee these missions even have cutscenes but whatever I don't care
	"""
	NameText	DespText	StoryIDStart	StoryIDEnd
	描述	描述	开启时剧情	交付时剧情
	Client	Client	Client	Client
	int	int	int	int
	"""

	dlc2Information_tsv = ["""356002	356101	2
356003	356102	6
356004	356103	9
356005	356104	10
356006	356105	11
356007	356106	13
356008	356107	14
356009	356108	15
356010	356109	16""","""356011	356110	17
356012	356111	18
356013	356112	19
356014	356113	22
356015	356114	23
356016	356115	24
356017	356116	27
356018	356117	28
356019	356118	29
356020	356119	30
356021	356120	33
356022	356121	34
356023	356122	35"""]

	for i in range(len(dlc2Information_tsv)):

		dlc2Information=[DLC2MissionData(info) for info in dlc2Information_tsv[i].splitlines()]
		dlc2Datas=[]
		for j in range(0,len(dlc2Information)):
			thisInfo:DLC2MissionData=dlc2Information[j]
			startAt=0
			if i==1:
				startAt=16
			if j>0:
				startAt=dlc2Information[j-1].StoryIDEnd+1

			
			
			if j==0:
				#MIHOYO IS IS SO HARD TO PUT YOUR PARTS IN A NORMAL ORDER INSTEAD OF PUTTING 998 AND 999 BEFORE 1
				parts = {
					"-1":convertPart(unconvertedLines_DLC2,998),
					"0":convertPart(unconvertedLines_DLC2,999),
					"1":convertPart(unconvertedLines_DLC2,1),
					"2":convertPart(unconvertedLines_DLC2,2),
				}
			else:
				parts={k:convertPart(unconvertedLines_DLC2,k) for k in range(startAt,thisInfo.StoryIDEnd+1)}

			dlc2Datas.append(writeAndReturnPart(
				parts,
				thisInfo.MissionName,
				"DLC2-"+str(startAt)+"-"+str(thisInfo.StoryIDEnd)
			))
			dlc2Datas[-1]['description']=thisInfo.MissionDesc
			

		story['event'].append({
			"name":"Era ZERO Chapter "+str(i+1),
			"episodes":dlc2Datas
		})
#writeDLC2Data()


#ABANDON ALL HOPE, YE WHO ENTER HERE
#"Who needs file structures anyways" - The complete lunatics at mihoyo that think this is even remotely okay
from biographiesToJSON import PartnerPosterData

class PartnerStoryHeadData():
	def __init__(self,tsv:List[str],textMap:Dict[int,List[str]]) -> None:
		self.StoryID=int(tsv[0])
		#BackgroundID is never used
		self.Title=textMap[int(tsv[2])]
		self.Description=textMap[int(tsv[3])] #Unknown, appears to be for grouping
		self.Poster=int(tsv[4]) #Unknown
		self.StoryOrder=int(tsv[5]) #IntimacyRequire, but stories are sorted by intimacy
		pass

	def __str__(self)->str:
		return str(vars(self))

class PartnerStoryStruct():
	def __init__(self,tsv:List[str]) -> None:
		self.text=int(tsv[2][4:])
		if tsv[1][0]=="2": #WTF WHY WOULD YOU DO THIS
			tsv[1]='1'+tsv[1][1:]
			self.PortraitPosition:Literal[1,2]=2 #This isn't really needed since there's usually always just two
		else:
			self.PortraitPosition:Literal[1,2]=1
		self.FigureID=int(tsv[1])
		#if self.FigureID
		self.RoleFace=int(tsv[3])

#import BuildLibrary
#libraryDatas:List[BuildLibrary.LibraryData]=BuildLibrary.getLibraryDatas(textMap)

def convertPartnerStory(linesToConvert:List[Any])->List[List[Any]]:
	commandsList:List[List[Any]]=[]

	structs:List[PartnerStoryStruct]=[]
	for unConvStoryText in linesToConvert:
		structs.append(PartnerStoryStruct(unConvStoryText))
	if len(structs)<2:
		print("There are not enough structs!!")
		return commandsList
	
	#commandsList.append([ #It's not really accurate, I think it uses RoleSide in the figure db
	#	'portraits',
	#	[structs[0].FigureID,structs[0].RoleFace,False],
	#	[structs[1].FigureID,structs[1].RoleFace,True]
	#])
	for i in range(len(structs)):
		partnerStoryLine = structs[i]

		lastCmd = getLastCommandOf(commandsList,'portraits')
		if not lastCmd:
			#print("No last cmd")
			newCmd=['portraits',emptyPortrait,emptyPortrait]
		else:
			#print(lastCmd)
			newCmd = ['portraits',lastCmd[1].copy(),lastCmd[2].copy()]
			
		#If opposite side exists, dim it
		if newCmd[getOpp(partnerStoryLine.PortraitPosition)][0]!='':
			newCmd[getOpp(partnerStoryLine.PortraitPosition)][2]=True
		#

		if partnerStoryLine.FigureID < 0:
			#print("Ignoring unknown RoleID: "+str(RoleID))
			pass
		else:
			if partnerStoryLine.FigureID in storyFigueSettingData:
				pInfo = storyFigueSettingData[partnerStoryLine.FigureID]
				#RoleFace 1 is identical to 0, but the story portrait database generator handles this anyways
				newCmd[partnerStoryLine.PortraitPosition]=[partnerStoryLine.FigureID,partnerStoryLine.RoleFace,False]
				lastSpeakerName = getLastCommandOf(commandsList,'speaker')
				if not lastSpeakerName or lastSpeakerName[1] != pInfo.SpeakerName:
					commandsList.append(['speaker', pInfo.SpeakerName ])
			else:
				#print("ID "+str(StoryTextV2.RoleID)+" does not exist in portrait/name DB")
				commandsList.append(['speaker',"Missing ID " +str(partnerStoryLine.FigureID)+" (Removed from DB?)"])
		
		if lastCmd!=newCmd:
			commandsList.append(newCmd)

		if partnerStoryLine.text > 0 and partnerStoryLine.text in textMap:
			commandsList.append(['msg']+[partnerStoryLine.text]+textMap[partnerStoryLine.text]) # type: ignore
		#else:
		#	print("ID "+str(partnerStoryLine.text)+" not present in text db, assuming command with no message")
	return commandsList

def writePartnerStories():
	partnerStoryData = getStoryTSV("PartnerStoryData.tsv")
	partnerPosterData:Dict[int,PartnerPosterData] = {}
	with open("GameData/PartnerPosterData.tsv",'r') as f:
		f.readline()
		while True:
			line = f.readline()
			if not line:
				break
			info=line.split('\t')
			
			data = PartnerPosterData(info,textMap,storyFigueSettingData)
			partnerPosterData[data.PosterID]=data
	"""
		Structure example:
		"6":[
			cutscene1,
			cutscene2,
			etc
		],
		"7":[
			...
		]
	"""
	partnerStoryHeadData:Dict[int,List[PartnerStoryHeadData]]={}
	with open("GameData/PartnerStoryHeadData.tsv",'r') as f:
		f.readline()
		lastPoster=-1
		while True:
			line = f.readline()
			if not line:
				break
			d = PartnerStoryHeadData(line.split('\t'),textMap)
			
			if d.Poster not in partnerStoryHeadData:
				partnerStoryHeadData[d.Poster]=[]
			partnerStoryHeadData[d.Poster].append(d)

			if lastPoster==-1:
				lastPoster=d.Poster
			elif lastPoster!=d.Poster:
				partnerStoryHeadData[lastPoster].sort(key=lambda x: x.StoryOrder)
			lastPoster=d.Poster
	#print(partnerStoryHeadData[6])
	#for p in partnerStoryHeadData[6]:
	#	print(p)
	partnerEpisodes=[]
	for poster in partnerStoryHeadData:
		partnerStoriesInfo=partnerStoryHeadData[poster]

		#It turns out there are no stories with unknown posters in the first place, so you can just continue

		# if poster in partnerPosterData:
		# 	fileName = "PartnerStory-"+str(partnerPosterData[poster].PortraitID)+".json"
		# 	episodeName = partnerPosterData[poster].Name[0]
		# else:
		# 	print("This story has no poster associated with it!")
		# 	fileName = "PartnerStory-unk-"+str(poster)+".json"
		# 	episodeName = "Unknown Partner ID"+str(poster)
		# 	#continue
		if poster not in partnerPosterData:
			continue
		fileName = "PartnerStory-"+str(partnerPosterData[poster].PortraitID)+".json"
		episodeName = partnerPosterData[poster].Name[0]

		parts = {}
		part_names = []
		for st in partnerStoriesInfo:
			if st.StoryID in partnerStoryData:
				parts[st.StoryID] = convertPartnerStory(partnerStoryData[st.StoryID])
				part_names.append(st.Title[2])
			else:
				print("There is no partner story with ID "+str(st.StoryID))
		if len(parts) > 0:
			with open("../avgtxt/"+fileName,'wb') as f:
				f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
				print("Generated "+fileName+" containing "+str(len(parts)))
			
			partnerEpisodes.append({
				'name':episodeName,
				'parts':fileName,
				'part_names':part_names
			})


	story['event'].append({
		"name":"Partner Stories (Removed)",
		"episodes":partnerEpisodes
	})

	def foundStory(storyNum:int)->bool:
		for k in partnerStoryHeadData:
			for pshd in partnerStoryHeadData[k]:
				if pshd.StoryID==p:
					return True
		return False


	#unusedPartnerEpisodes = []
	#parts = {}
	#Actually there aren't any that aren't used...
	for p in partnerStoryData:
		if not foundStory(p):
			print("Partner story "+str(p)+" is not used.")
			# parts[p] = convertPartnerStory(partnerStoryData[p])
			# if len(p)>9:
			# 	with open("../avgtxt/"+fileName,'wb') as f:
			# 		f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
			# 		print("Generated "+fileName+" containing "+str(len(parts)))

writePartnerStories()
#sys.exit(0)



"""with open("../avgtxt/"+fName,'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated "+fName)"""

#Grouped extdata goes here

#Why did I name this writeAndReturnPart3 when there's no 2
def writeAndReturnPart3(begin:int,end:int,name:str,customFileName:Union[str,None]=None)->dict:
	fName="ExtData-"+str(begin)+"-"+str(end+1)+".json"
	if customFileName:
		fName=customFileName
	return writeAndReturnPart(
		{j:convertPart(unconvertedLines_Ext,j) for j in range(begin,end+1)},
		name,
		fName,
		[j for j in range(begin,end+1)]
	)

#writeAndReturnPart3(2070,2081,"Bronya's Magic show, also sexy Sin Mal")
#sys.exit(0)

#writeAndReturnPart3(3930,3939,"Test")
#sys.exit(-1)

groupedExtData = [
	writeAndReturnPart(
		{j:convertPart(unconvertedLines_Ext,j) for j in range(3055,3062)},
		"Seele's Dream",
		"ExtData-3055-3061.json"
	),
	writeAndReturnPart3(1657,1665,"Honkai RPG"),
	writeAndReturnPart3(1722,1725,"Theresa's birthday?"),
	writeAndReturnPart3(1755,1763,"CN only event"),
	writeAndReturnPart3(1764,1769,"Nina afterstory"),
	writeAndReturnPart3(1804,1812,"Seele's stigmata space and Seele 2"),
	writeAndReturnPart3(1813,1821,"asdasdadadasd"),
	writeAndReturnPart3(1830,1857,"asasddadsdadsd 2"),
	writeAndReturnPart3(1858,1861,"Another CN exclusive"),
	writeAndReturnPart3(1862,1864,"asdjiaodijojwo 3"),
	writeAndReturnPart3(1865,1870,"Delta, no not the pink one"),
	writeAndReturnPart3(1885,1893,"Mei becomes a child"),
	writeAndReturnPart3(1930,1939,"Unused Fire Moth garbage"),
	writeAndReturnPart3(2424,2431,"school au"),
	writeAndReturnPart3(2464,2469,"Unused junk"),
	writeAndReturnPart3(2470,2478,"Wonderland"),
	writeAndReturnPart3(2524,2534,"Wonderland again"),
	writeAndReturnPart3(2077,2081,"Seele's Magic show, also sexy Sin Mal"),
	writeAndReturnPart3(3805,3096,"Schoolgirl AU stuff"),
	writeAndReturnPart3(3100,3108,"Sirin goes to school"),
	writeAndReturnPart3(1260,1267,"Lost Child S3, I guess"),
	
	writeAndReturnPart(
		{j:convertPart(unconvertedLines_Ext,j) for j in range(390,408)},
		"JP Only event?",
		"ExtData-390-408.json"
	)
]

story['event'].append({
	"name":"Stuff...",
	"episodes":groupedExtData
})

#And now for whatever's left... I guess...
unknownExtData = []
lastPart = 0
for i in unconvertedLines_Ext.keys():
	lastPart=max(lastPart,i)
for i in range(0,int(lastPart/10)+1):
	parts = {}
	for j in range(i*10,i*10+10):
		if j in unconvertedLines_Ext:
			linesToConvert = unconvertedLines_Ext[j]
			partAlreadyExists=False
			"""for line in linesToConvert:
				#print(line[3])
				if line[3] != "0" and int(line[3][4:]) in allUsedLinesSoFar:
					partAlreadyExists=True
					print("skipped "+str(j))
					break"""
			if partAlreadyExists==False:
				parts[j]=convertPart(unconvertedLines_Ext,j)
		else:
			print("No DialogueID "+str(j))
	print(parts.keys())
	
	if parts: #Do not add empty data
		fName = "StoryExtData-"+str(i)+'.json'
		unknownExtData.append(writeAndReturnPart(
			parts,
			"Parts "+str(i*10)+"-"+str(i*10+9),
			fName,
			list(parts.keys())
		))

story['event'].append({
	"name":"Unknown ExtData",
	"episodes":unknownExtData
})

unknownSubData = []
for i in range(0,14):
	parts = {}
	for j in range(i*10,i*10+10):
		if j in unconvertedLines_Sub:
			parts[j]=convertPart(unconvertedLines_Sub,j)
		else:
			print("No DialogueID "+str(j))
	print(parts.keys())
	
	if parts: #Do not add empty data
		fName = "StorySubData-"+str(i)+'.json'
		unknownSubData.append(writeAndReturnPart(
			parts,
			"Parts "+str(i*10)+"-"+str(i*10+9),
			fName,
			list(parts.keys())
		))
story['event'].append({
	"name":"Unknown SubData",
	"episodes":unknownSubData
})

story['event'].append({
	"name":"World Bosses",
	"episodes":[
		writeAndReturnPart3(1680,1685,"Sakura World Boss?"),
		writeAndReturnPart3(1686,1691,"Kaguya World Boss?"),
		writeAndReturnPart3(1692,1695,"Chloe World Boss?"),
		writeAndReturnPart3(1696,1700,"Kira World Boss?"),
		writeAndReturnPart3(1749,1754,"Kaguya (Unknown Data)"),
		writeAndReturnPart3(1770,1775,"Kira (Unknown Data)"),
		writeAndReturnPart3(1776,1781,"Chloe (Unknown Data)"),
	]
})
story['event'].append({
	"name":"Haunted Mansion",
	"episodes":[
		writeAndReturnPart3(89,89,"Introduction"),
		writeAndReturnPart3(90,90,"Ghost Girl"),
		writeAndReturnPart3(99,101,"Haunted Mansion S1"),
		writeAndReturnPart3(102,103,"Haunted Mansion S2"),
		writeAndReturnPart3(144,149,"Haunted Mansion S2 cont."),
		writeAndReturnPart3(150,153,"Haunted Mansion S3"),
		#writeAndReturnPart3(1776,1781,"Chloe (Unknown Data)"),
	]
})



				

#Convert StoryInsideData
parts = {}
for j in range(0,11):
	if j in unconvertedLines_Inside:
		parts[j]=convertPart(unconvertedLines_Inside,j)
	else:
		print("No DialogueID "+str(j))

fName = "StoryInsideData.json"
story['event'].append({
	"name":"Unknown InsideData",
	"episodes":[
		writeAndReturnPart(
			parts,
			"Parts 0-10",
			"storyinsidedata.json"
		)
	]
})



#sys.exit(0)

#HG2 x GFL
parts = {j:convertPart(unconvertedLines_Ext,j) for j in range(772,782+1)}

with open("../avgtxt/hg2-gfl-old.json",'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))

story['crossover'].append({
	"name":"Houkai Gakuen 2nd x Girls' Frontline",
	"shortName":"HG2 x GFL",
	"episodes":[
		{
			"name":"Full Episode",
			"parts":"hg2-gfl-old.json"
		}
	]
})
story['crossover'].append({
	"name":"GGZ x HI3: Herrscher of Sentience",
	"shortName":"GGZ x HI3: HoS",
	"episodes":[
		writeAndReturnPart3(3760,3769,"Part 1","ggz-hi3-hos-1.json"),
		writeAndReturnPart3(3770,3773,"Part 2","ggz-hi3-hos-2.json"),
	]
})
story['crossover'].append({
	"name":"GGZ x HI3: Herrscher of Reason",
	"shortName":"GGZ x HI3: HoR",
	"episodes":[
		writeAndReturnPart3(2927,2936,"Full Episode","ggz-hi3-hor.json")
	]
})

story['crossover'].append({
	"name":"GGZ x HI3: Ai Chan",
	#"shortName":"GGZ x HI3: Ai Chan",
	"episodes":[
		writeAndReturnPart3(1356,1361,"Full Episode","ggz-hi3-aic-1.json"),
	]
})
story['crossover'].append({
	"name":"Hyperdimension Neptunia",
	"episodes":[
		writeAndReturnPart(
			{j:convertPart(unconvertedLines_Ext,j) for j in range(2057,2070)},
			"Hyperdimension Neptunia Crossover",
			"ExtData-2057-2069.json"
		),
		writeAndReturnPart(
			{j:convertPart(unconvertedLines_Ext,j) for j in range(2497,2524)},
			"Hyperdimension Neptunia Crossover 2",
			"ExtData-2497-2523.json"
		),
	]
})
story['crossover'].append({
	"name":"Date A Live crossover (Incomplete?)",
	"episodes":[
		writeAndReturnPart3(1909,1920,"Date A Live crossover"),
	]
})



#This runs at the end!
routing = {}
for section in story:
	numChapters = len(story[section])
	for i in range(numChapters):
		numEpisodes = len(story[section][i]['episodes'])
		for j in range(numEpisodes):
			thisEpisode=story[section][i]['episodes'][j]
			#if j < numEpisodes:
			routing[thisEpisode['parts']]=section+"-"+str(i)+"-"+str(j)

with open('../chapterDatabase.json','wb') as f:
	f.write(JSON.dumps({'story':story,'routing':routing}, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated chapterDatabase.json")
	
