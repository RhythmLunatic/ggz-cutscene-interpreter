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


if os.path.exists("TextMap_custom.tsv"):
	with open("TextMap_custom.tsv",'r') as f:
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
			if tID in textMap and line[-1] != "":
				textMap[tID][3] = line[-1].replace("{","<").replace("}",">")

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

def getLastCommandOf(commandsList,t):
	for i in range(len(commandsList)-1,-1,-1):
		if commandsList[i][0]==t:
			return commandsList[i]
		#else:
		#	print(commandsList[i][0]+" != "+t)
	return None
	
def getOpp(i):
	return 2 if i==1 else 1

emptyPortrait = ['',0,False]
#def shouldDimThis(thisPosition,

def getStoryTSV(fileName):
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
	def __init__(self, StoryTextV2, _type=0):
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


portraitBlacklist = [0,802,803,804,805] #Portraits without an image

def convertPart(section,partNumber:int,_type=0):
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
			if lastBGcmd and lastBGcmd[1] != StoryTextV2.BGID and StoryTextV2.BGID!="0": #Skip duplicates
				print("Pushed new BG "+StoryTextV2.BGID)
				commandsList.append(['bg',StoryTextV2.BGID])
			elif lastBGcmd==None and StoryTextV2.BGID!="0":
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
			commandsList.append(['msg']+[StoryTextV2.text]+textMap[StoryTextV2.text][:4])
		else:
			print("ID "+str(StoryTextV2.text)+" not present in text db, assuming command with no message")
			#print(StoryTextV2)
	return commandsList

#convertPart(unconvertedLines_Kyusyo,20)
#sys.exit(0)
"""{
			"name":"Playback Type 1 Data (Main Story?)",
			"episodes":[]
		},
		{
			"name":"Playback Type 2 Data (Side Events?)",
			"episodes":[]
		},
		{
			"name":"Playback Type 3 Data",
			"episodes":[]
		},
		{
			"name":"Playback Type 4 Data",
			"episodes":[]
		},
		{
			"name":"Playback Type 6 Data",
			"episodes":[]
		}"""
		
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


unknownExtData = []
for i in range(0,312):
	parts = {}
	for j in range(i*10,i*10+10):
		if j in unconvertedLines_Ext:
			parts[j]=convertPart(unconvertedLines_Ext,j)
		else:
			print("No DialogueID "+str(j))
	print(parts.keys())
	
	if parts: #Do not add empty data
		fName = "StoryExtData-"+str(i)+'.json'
		unknownExtData.append({
			"name":"Parts "+str(i*10)+"-"+str(i*10+9),
			"parts":fName
		})
		
		with open("../avgtxt/"+fName,'wb') as f:
				f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
				print("Generated "+fName)
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
		fName = "StoryKyusyoData-"+str(i)+'.json'
		unknownKyusyoData.append({
			"name":"Parts "+str(i*10)+"-"+str(i*10+9),
			"parts":fName
		})
		
		with open("../avgtxt/"+fName,'wb') as f:
				f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
				print("Generated "+fName)
story['event'].append({
	"name":"Unknown Kyusyo Data",
	"episodes":unknownKyusyoData
})

with open("../avgtxt/"+fName,'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated "+fName)


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


#Prologue
parts = {
	"1":convertPart(unconvertedLines_Ext,1152),
	"2":convertPart(unconvertedLines_Ext,1135),
}
with open("../avgtxt/prologue.json",'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))

#Main story?
unconvertedLines_Playback = getStoryTSV('PlaybackStoryData.tsv')
#print(convertPart(unconvertedLines_Playback,1,True))
#sys.exit(0)

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
		self.ExType = int(d[2]) #Unknown purpose, but seems to be related to ExTitle. Note that these are not unique, Genkai Room and Mysterious Deep use the same type.
		self.StoryTitle = int(d[3]) #Possibly also determines grouping
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
		parts[thisData.DialogueID]=newPart
		if thisData.DialogueID==91:
			parts[thisData.DialogueID].insert(0,['bgm','The Sound of the End'])

	if i==len(playbackData)-1 or thisData.EpisodeNumber != playbackData[i+1].EpisodeNumber:
		if parts:
			fileName = "type-"+str(thisData.StoryType)+"-"+str(thisData.ExType)+"-chapter-"+str(thisData.EpisodeNumber)+'.json'
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
	
