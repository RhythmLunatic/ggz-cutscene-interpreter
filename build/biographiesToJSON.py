#!/usr/bin/env python3.8
import os
import json
from typing import List,Union,Dict,Any
from BuildSpeakerPortraitDatabase import StoryFigureSettingDataStruct
import sys
			
#PosterID	FigureID	Type	PersonatedMaxIntimacy	PosterName	TalkList	facelist	cvlist	height	threesize	seriesname	description	brithday	hobby	FirstSightDialogue	SeriesID	Live2D	Group	GroupName	IsOpen	BackGround	DialogueX	DialogueY	isPDAS	IsEntry	PartsNum
class PartnerPosterData():
	def __init__(self, info:List[str],textMap:Dict[int,List[str]],storyFigueSettingData:Union[Dict[int,StoryFigureSettingDataStruct],None]=None):
		self.PosterID=int(info[0])
		self.PortraitID=int(info[1])
		if storyFigueSettingData:
			if self.PortraitID in storyFigueSettingData:
				self.PortraitFile:str=storyFigueSettingData[self.PortraitID].pic
			else:
				print("Portrait ID "+str(self.PortraitID)+" missing from DB.")
				#self.PortraitFile=""
		self.Type=int(info[2])
		self.PersonatedMaxIntimacy=int(info[3])
		self.NameID=int(info[4])
		self.Name=textMap[self.NameID]
		self.TalkList= [textMap[int(a)] for a in info[5].split(';')[:-1]]
		self.FaceList = [int(a) for a in info[6].split(';')[:-1]]
		self.cvList = [int(a) for a in info[7].split(';')[:-1]]
		self.Height = info[8]
		self.ThreeSizes = info[9]
		self.Weight = textMap[int(info[10])]
		self.Description = textMap[int(info[11])]
		self.Birthday=info[12]
		self.Hobby=textMap[int(info[13])]
		self.FirstSightDialogue=textMap[int(info[14])]
		

	
	def __str__(self):
		#print("Poster
		print(vars(self))
		
	def getTable(self):
		d = vars(self).copy()
		del d['PosterID']
		return d
		#return vars(self)
	"""def getTSV(self):
		s = ""
		d = vars(self)
		for v in d:
			if isinstance(d[v],list):
				s+="
			#s+=str("""

class PartnerStoryHeadData():
	def __init__(self,tsv:List[str],textMap:Dict[int,List[str]]) -> None:
		self.StoryID=int(tsv[0])
		#BackgroundID is never used
		self.Title:List[str]=textMap[int(tsv[2])] #For short stories (usually 1 paragraph, NOT the full cutscenes)
		self.ShortStory:List[str]=textMap[int(tsv[3])] #The short story
		self.Poster=int(tsv[4]) #ID of the 'poster', refers to ID in PartnerPosterData
		self.StoryOrder=int(tsv[5]) #IntimacyRequire, but stories are sorted by intimacy
		pass

	def __str__(self)->str:
		return str(vars(self))

if __name__=='__main__':
	USE_EXTERNAL_DATABASES=False

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
				
	storyFigueSettingData:Dict[int,StoryFigureSettingDataStruct] = None #type: ignore
	if USE_EXTERNAL_DATABASES==False:
		storyFigueSettingData = {}
		with open("GameData/StoryFigueSettingData.tsv",'r') as f:
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

	#Indexed by poster ID, a list of stories.
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

	print(partnerStoryHeadData[120])
	#sys.exit(-1)
	newData={}
	with open("GameData/PartnerPosterData.tsv",'r') as f:
		f.readline()
		while True:
			line = f.readline()
			if not line:
				break
			info=line.split('\t')
			
			data = PartnerPosterData(info,textMap,storyFigueSettingData)
			newData[data.PosterID]=data.getTable()
			if data.PosterID in partnerStoryHeadData:
				#newData[data.PosterID].
				stories = []
				for st in partnerStoryHeadData[data.PosterID]:
					stories.append({
						'sortOrder':st.StoryOrder,
						'title':st.Title,
						'story':st.ShortStory
					})
				newData[data.PosterID]["stories"]=stories

			#print(data.getTable())
			#break
	with open('biographies.json','wb') as f:
		f.write(json.dumps(newData, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
		#print("Generated database.json")
