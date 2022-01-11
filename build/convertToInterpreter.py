#!/usr/bin/env python3
import json as JSON
import sys
import os
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
textMap = {}


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


if os.path.exists("TextMap_retranslated.json"):
	with open("TextMap_retranslated.json",'r',encoding='utf8') as f:
		textMap_retranslated = JSON.loads(f.read())
		for fakeID in textMap_retranslated:
			tID = int(fakeID)
			if tID in textMap:
				textMap[tID][3] = textMap_retranslated[fakeID].replace("{","<").replace("}",">")

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
		self.DevY=info[2]
		self.StorySide=int(info[3])    #What the fuck is this even for???
		self.SpeakerName=int(info[4])  #This is a TextID, pulled from textMap_en
		self.FacePosition=info[5]      #x,y coords of replacement face
		self.FlipOnOtherSide=(info[6]=="1")
		self.Scale=float(info[7])
		

storyFigueSettingData = {}
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

def getLastCommandOf(commandsList:list,opcode:str):
	"""Given a list of opcodes and the type to search, return the last opcode of the type specified."""
	for i in range(len(commandsList)-1,-1,-1):
		if commandsList[i][0]==opcode:
			return commandsList[i]
		#else:
		#	print(commandsList[i][0]+" != "+t)
	return None
	
def getOpp(i):
	return 2 if i==1 else 1

emptyPortrait = ['',0,False]
#def shouldDimThis(thisPosition,

def getStoryTSV(fileName):
	"""Converts a story TSV into a dict of lists, with the dict being indexed by the part ID.
	
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
				#print("added part "+str(lastPart))
				#print(unconvertedLines_Main)
				#sys.exit(0)
			else:
				unconvertedData[curPart].append(StoryTextV2)
			lastPart=curPart
	return unconvertedData

unconvertedLines_Main = getStoryTSV('StoryMainData.tsv')
unconvertedLines_Sub = getStoryTSV('StorySubData.tsv')
unconvertedLines_Ext = getStoryTSV('StoryExtData.tsv')
unconvertedLines_Inside = getStoryTSV('StoryInsideData.tsv')
unconvertedLines_Kyusyo = getStoryTSV('KyusyoStoryData.tsv')

#sys.exit(0)
class StoryDataStruct():
	"""Convert a StoryData list into a struct.
		_type: If 0 (default), column 3 is the text.
		If 1, column 1 is the text.
	"""
	def __init__(self, StoryTextV2:list, _type=0):
		#self.DialogueID = int(l[0])
		if _type == 1:
			if RepresentsInt(StoryTextV2[1]):
				self.text = int(StoryTextV2[1])
			else:
				print("Unimplemented opcode! "+StoryTextV2[1]+" is not an integer.")
				print(StoryTextV2)
				self.text = -1
			self.RoleID = int(StoryTextV2[2])
			self.PortraitPosition = 2 if (StoryTextV2[3]=="1") else 1
			self.RoleFace = int(StoryTextV2[4])
			#self.RoleMotion = int(StoryTextV2[5])
			#self.isMotionFirst = StoryTextV2[6] == "1"
			self.CGID = StoryTextV2[9]
			self.BGID = StoryTextV2[10]
		elif _type == 2:
			pass
		else:
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
			self.RoleID = int(StoryTextV2[6])
			self.PortraitPosition=2 if (StoryTextV2[7]=="1") else 1
			self.RoleFace=int(StoryTextV2[8])
			self.CGID=StoryTextV2[13]
			self.BGID = StoryTextV2[14]

	
		if self.BGID=="0":
			self.BGID="black"


portraitBlacklist = [0,802,803,804,805] #Portraits without an image



#Hueristic to skip parts that exist in the playback archive
allUsedLinesSoFar = []

def convertPart(section:dict,partNumber:int,_type=0):
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
		
		if StoryTextV2.text > 0 and StoryTextV2.text in textMap:
			allUsedLinesSoFar.append(StoryTextV2.text)
			commandsList.append(['msg']+[StoryTextV2.text]+textMap[StoryTextV2.text][:4])
		else:
			print("ID "+str(StoryTextV2.text)+" not present in text db, assuming command with no message")
			#print(StoryTextV2)
	return commandsList

def writeAndReturnPart(parts:dict,name:str,fileName:str,partNames:list=None)->dict:
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
		d["part_names"]=partNames
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


#All stories in the playback archive.
unconvertedLines_Playback = getStoryTSV('PlaybackStoryData.tsv')

# Search for matching chapter name
def getIndexFromKey(k:str):
	for i in range(len(story['main'])):
		ep = story['main'][i]
		#print(ep)
		if ep['name']==k:
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
		self.StoryTitle = int(d[3]) #The chapter title, but I'm not sure how it's determined when there are two different titles in the same group.
		self.StoryTitle=[self.StoryTitle]+textMap[self.StoryTitle]
		#Column 4 seems to be unused
		self.EpisodeNumber = int(d[5])
		self.EpisodePrefix = int(d[6]) #Episode 1, Episode 2, etc
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

	if i==len(playbackData)-1 or thisData.EpisodeNumber != playbackData[i+1].EpisodeNumber:
		if parts:
			fileName = "type-"+str(thisData.StoryType)+"-"+str(thisData.ExType)+"-chapter-"+str(thisData.EpisodeNumber)+'-'+str(thisData.DialogueID)+'.json'
			print(parts.keys())
			with open("../avgtxt/"+fileName,'wb') as f:
				f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
				print("Generated "+fileName+" containing "+str(len(parts)))


			#if storyType == 6:
			#	storyType = 5
			idx = getIndexFromKey(thisData.StoryTitle[1])
			if idx==-1:
				story['main'].append({
					"name":thisData.StoryTitle[1],
					"nameMultilang":thisData.StoryTitle,
					#"shortName":"HG2 x GFL",
					"episodes":[
						{
							"name":thisData.getChapterName(),
							"parts":fileName
						}
					]
				})
			else:
				story['main'][idx]['episodes'].append({
					"name":thisData.getChapterName(),
					"parts":fileName
				})
		parts={}


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
			self.MissionDesc = textMap[int(d[10])][0]
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


KyusyoStoryPartsList = []
for mission in kyusyoMissionDatas:
	KyusyoStoryPartsList.append(mission.StoryIDStart)
KyusyoStoryPartsList.sort()
print(KyusyoStoryPartsList)
#sys.exit(0)

def getNextClosestEndPart(start:int)->int:
	for n in KyusyoStoryPartsList:
		if start > n or start==n:
			#print(str(start)+" < "+str(n))
			continue
		else:
			#print("Closest to "+str(start)+" is "+str(n))
			return n
	return KyusyoStoryPartsList[-1]

#ConvertedKyusyoData = []
for i in range(8):
	story['side'].append({
		"name":"Chapter "+str(i+1),
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
	for j in range(thisMission.StoryIDStart,getNextClosestEndPart(thisMission.StoryIDStart)):
		if j in unconvertedLines_Kyusyo:
			parts[j] = convertPart(unconvertedLines_Kyusyo,j)
		#else:
		#	print("No DialogueID "+str(j))
	print(parts.keys())
	if parts:
		fName = "StoryKyusyoData-chapter-"+str(thisMission.ChapterNum)+"-"+str(thisMission.MissionID)+'.json'
		
		toAdd = thisMission.ChapterNum
		if thisMission.StoryIDEnd > 900 and thisMission.StoryIDEnd < 1000:
			#Not sure how this works, but these parts exist
			parts[j] = convertPart(unconvertedLines_Kyusyo,thisMission.StoryIDEnd)
			toAdd=8
		story['side'][toAdd]['episodes'].append({
			"name":thisMission.MissionName,
			"parts":fName,
			"part_names":list(parts.keys())
		})
		if thisMission.MissionDesc != "":
			story['side'][thisMission.ChapterNum]['episodes'][-1]["description"]=thisMission.MissionDesc
		with open("../avgtxt/"+fName,'wb') as f:
			f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
			print("Generated "+fName)

unknownKyusyoData = []
for i in range(0,14):
	parts = {}
	for j in range(i*10,i*10+10):
		if j in unconvertedLines_Kyusyo:
			parts[j]=convertPart(unconvertedLines_Kyusyo,j)
		else:
			print("No DialogueID "+str(j))
	print(parts.keys())
	
	if parts: #Do not add empty data
		fName = "StoryKyusyoData-unk-"+str(i)+'.json'
		unknownKyusyoData.append({
			"name":"Parts "+str(i*10)+"-"+str(i*10+9),
			"parts":fName,
			"part_names":list(parts.keys())
		})
		
		with open("../avgtxt/"+fName,'wb') as f:
				f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
				print("Generated "+fName)
story['side'].append({
	"name":"Unknown Kyusyo Data",
	"episodes":unknownKyusyoData
})

with open("../avgtxt/"+fName,'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated "+fName)

#Grouped extdata goes here
groupedExtData = []
groupedExtData.append(writeAndReturnPart(
	{j:convertPart(unconvertedLines_Ext,j) for j in range(3055,3062)},
	"Seele's Dream",
	"ExtData-3055-3061.json"
))
groupedExtData.append(writeAndReturnPart(
	{j:convertPart(unconvertedLines_Ext,j) for j in range(2060,2077)},
	"Hyperdimension Neptunia Crossover",
	"ExtData-2060-2076.json"
))
groupedExtData.append(writeAndReturnPart(
	{j:convertPart(unconvertedLines_Ext,j) for j in range(2497,2524)},
	"Hyperdimension Neptunia Crossover 2",
	"ExtData-2497-2523.json"
))
groupedExtData.append(writeAndReturnPart(
	{j:convertPart(unconvertedLines_Ext,j) for j in range(390,408)},
	"JP Only event?",
	"ExtData-390-408.json"
))

story['event'].append({
	"name":"Stuff...",
	"episodes":groupedExtData
})

#And now for whatever's left... I guess...
unknownExtData = []
for i in range(0,312):
	parts = {}
	for j in range(i*10,i*10+10):
		if j in unconvertedLines_Ext:
			linesToConvert = unconvertedLines_Ext[j]
			partAlreadyExists=False
			for line in linesToConvert:
				#print(line[3])
				if line[3] != "0" and int(line[3][4:]) in allUsedLinesSoFar:
					partAlreadyExists=True
					print("skipped "+str(j))
					break
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
		unknownSubData.append({
			"name":"Parts "+str(i*10)+"-"+str(i*10+9),
			"parts":fName
		})
		
		with open("../avgtxt/"+fName,'wb') as f:
				f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
				print("Generated "+fName)
story['event'].append({
	"name":"Unknown SubData",
	"episodes":unknownSubData
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
		{
			"name":"Parts 0-10",
			"parts":fName
		}
	]
})



#sys.exit(0)

#HG2 x GFL
"""parts = {}
for p in range(772,782):
	parts[p]=convertPart(unconvertedLines_Ext,p)

with open("../avgtxt/hg2-gfl.json",'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))"""

story['crossover'].append({
	"name":"Houkai Gakuen 2nd x Girls' Frontline",
	"shortName":"HG2 x GFL",
	"episodes":[
		{
			"name":"Full Episode",
			"parts":"hg2-gfl.json"
		}
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
	
