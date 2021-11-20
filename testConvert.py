#!/usr/bin/env python3
import json as JSON
import sys
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
with open("TextMap_cn.tsv",'r') as f:
	f.readline() # skip line 1
	while True:
		line = f.readline()
		if not line:
			break
		line=line.split('\t')
		textMap[int(line[0])]=line[1:]
		
if True:
	#TEXT_ID	EN	CN	JP	KR	TCN
	files = {1:"TextMap_en.tsv",3:"TextMap_jp.tsv"}
	for column in files: 
		with open(files[column],'r') as f:
			f.readline() # skip line 1
			while True:
				line = f.readline()
				if not line:
					break
				line=line.split('\t')
				if len(line)<4 or not line[0].strip():
					print("Skipping invalid line")
					print(line)
					continue
				textID = int(line[0])
				if textID not in textMap:
					textMap[textID]=['XXX']*5
				textMap[textID][column-1]=line[column]
print("Now loading portrait information....")


"""
ID	PNGName	DevY	StorySide	FigueName	FacePosition	FlipOnOtherSide	Scale
0	图片路径	立绘y轴的偏移	非九霄中人物的默认站位，1为左，2为右	人物名字	脸的位置（替换）	当立绘放在storyside另一边时，是否翻转	大小
Picture path	The offset of the y-axis of the vertical picture	is not the default position of the characters in Jiuxiao, 1 is left, 2 is the right	Character name	Position of the face (replacement)	When the vertical picture is placed on the other side of the storyside, whether to flip	the size
int	string	float	int	int	List<float>	bool	float
"""
storyFigueSettingData = {}
with open("StoryFigueSettingData.tsv",'r') as f:
	f.readline() # skip first four lines, I don't know why they're here
	f.readline()
	f.readline()
	f.readline()
	while True:
		line = f.readline()
		if not line:
			break
		info=line.split('\t')
		
		storyFigueSettingData[int(info[0])]={
			"pic":info[1],
			"DevY":info[2],
			"StorySide":int(info[3]),#What the fuck is this even for???
			"SpeakerName":int(info[4]), #This is a TextID, pulled from textMap_en
			"FacePosition":info[5], #x,y coords of replacement face
			"FlipOnOtherSide":(info[6]=="1"),
			"Scale":float(info[7])
		}
print("done.")

#commandsList = []

def getLastCommandOf(commandsList,t):
	for i in range(len(commandsList)-1,-1,-1):
		if commandsList[i][0]==t:
			return commandsList[i]
	return None
	
def getOpp(i):
	return 2 if i==1 else 1

emptyPortrait = ['',0,False]
#def shouldDimThis(thisPosition,

def getStoryTSV(fileName):
	with open(fileName,'r') as storyData:
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

#sys.exit(0)
class StoryDataStruct():
	def __init__(self, StoryTextV2, isType2):
		#self.DialogueID = int(l[0])
		if isType2:
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
		else:
			#DialogueID	Type	UnLockLevelID	DialogueText	Repeatable	ChoiceID	RoleID	RoleStorySide	face	RoleMotion	isMotionFirst	RoleDelay	ItemShowCaseID	CGID	BGID	EffectID	isEffectFirst	EffectDelay	EffectDuration	SoundID	SoundDelay	SoundDuration	BGMID

			if len(StoryTextV2[3]) > 4:
				self.text = int(StoryTextV2[3][4:])
			else:
				print("Unimplemented opcode!")
				print(StoryTextV2)
				self.text=-1
			self.RoleID = int(StoryTextV2[6])
			self.PortraitPosition=2 if (StoryTextV2[7]=="1") else 1
			self.RoleFace=int(StoryTextV2[8])
			self.CGID=StoryTextV2[13]
			self.BGID = StoryTextV2[14]


def convertPart(section,partNumber,isType2=False):
	commandsList = []
	if partNumber not in section:
		print("MISSING ID "+str(partNumber)+"!!!!")
		return commandsList
	linesToConvert = section[partNumber]
	for UnConvStoryTextV2 in linesToConvert:
		StoryTextV2 = StoryDataStruct(UnConvStoryTextV2,isType2)
		
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
		if StoryTextV2.RoleID==0 or StoryTextV2.RoleID==804:
			newCmd[StoryTextV2.PortraitPosition]=emptyPortrait
		elif StoryTextV2.RoleID < 0:
			#print("Ignoring unknown RoleID: "+str(RoleID))
			pass
		else:
			if StoryTextV2.RoleID in storyFigueSettingData:
				pInfo = storyFigueSettingData[StoryTextV2.RoleID]
				newCmd[StoryTextV2.PortraitPosition]=[StoryTextV2.RoleID,StoryTextV2.RoleFace,False]
				commandsList.append(['speaker', pInfo['SpeakerName'] ])
			else:
				print("ID "+str(StoryTextV2.RoleID)+" does not exist in portrait/name DB")
			
		if StoryTextV2.CGID != "0":
			newCmd=['portraits',emptyPortrait,emptyPortrait]
			lastBGcmd = getLastCommandOf(commandsList,'bg')
			if not lastBGcmd or (lastBGcmd and lastCmd[1]!= StoryTextV2.CGID): #Skip duplicates
				commandsList.append(['bg',StoryTextV2.CGID])
		else:
			lastBGcmd = getLastCommandOf(commandsList,'bg')
			if not lastBGcmd or (lastBGcmd and lastCmd[1]!= 'black'): #Skip duplicates
				commandsList.append(['bg','black'])
			
		
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
		
		if StoryTextV2.BGID != "0":
			lastCmd = getLastCommandOf(commandsList,'bg')
			if not lastCmd or (lastCmd and lastCmd[1]!= StoryTextV2.BGID): #Skip duplicates
				commandsList.append(['bg',StoryTextV2.BGID])
		
		if StoryTextV2.text > 0 and StoryTextV2.text in textMap:
			commandsList.append(['msg']+textMap[StoryTextV2.text])
		else:
			print("ID "+str(StoryTextV2.text)+" not present in text db, assuming command with no message")
			#print(StoryTextV2)
	return commandsList

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
		{
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
		}
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
story['main'].append({
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
story['main'].append({
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
story['main'].append({
	"name":"Unknown InsideData",
	"episodes":[
		{
			"name":"Parts 0-10",
			"parts":fName
		}
	]
})

with open("../avgtxt/"+fName,'wb') as f:
	f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated "+fName)


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

with open('PlayBackStoryTitleData.tsv','r') as storyDatabase:
	storyDatabase.readline()
	storyDatabase.readline()
	storyDatabase.readline()
	storyDatabase.readline()
	
	#lastSeasonID = 0
	
	
	lastChapter = -1
	lastChapterName = ""
	lastStoryType = 1
	lastExType = "-1"
	
	parts = {}
	while True:
		l = storyDatabase.readline()
		if not l.strip():
			break
		d = l.split("\t")
		
		ChapterID = int(d[5])
		#Story types:
		#1 = Main?
		#2 = Side stories? Halloween event is here?
		storyType = int(d[1])

		if lastChapter != ChapterID:
			if parts:
				fileName = "type-"+str(lastStoryType)+"-"+lastExType+"-chapter-"+str(lastChapter)+'.json'
				print(parts.keys())
				with open("../avgtxt/"+fileName,'wb') as f:
					f.write(JSON.dumps(parts, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
					print("Generated "+fileName+" containing "+str(len(parts)))


				if storyType == 6:
					storyType = 5

				story['main'][storyType]['episodes'].append({
						"name":lastChapterName,
						"parts":fileName
					})
			parts={}
		
		newPart = convertPart(unconvertedLines_Playback,int(d[13]),True)
		if newPart:
			parts[d[13]]=newPart
		lastChapter=ChapterID
		lastChapterName=textMap[int(d[9])][0]
		lastStoryType = storyType
		lastExType = d[2]

with open('../chapterDatabase.json','wb') as f:
	f.write(JSON.dumps({'story':story}, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated chapterDatabase.json")
	
