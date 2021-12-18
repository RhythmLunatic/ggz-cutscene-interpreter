#!/usr/bin/env python3
import os
import json

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
			

if USE_EXTERNAL_DATABASES==False:
	#Just need the image path for this one... Maybe I should 
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
			storyFigueSettingData[int(info[0])]=info[1]
			
#PosterID	FigureID	Type	PersonatedMaxIntimacy	PosterName	TalkList	facelist	cvlist	height	threesize	seriesname	description	brithday	hobby	FirstSightDialogue	SeriesID	Live2D	Group	GroupName	IsOpen	BackGround	DialogueX	DialogueY	isPDAS	IsEntry	PartsNum
class PartnerPosterData():
	def __init__(self, info):
		self.PosterID=int(info[0])
		self.PortraitID=int(info[1])
		self.Type=int(info[2])
		self.PersonatedMaxIntimacy=int(info[3])
		self.Name=int(info[4])
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
		
		if USE_EXTERNAL_DATABASES==False:
			self.Name=textMap[self.Name]
			if self.PortraitID in storyFigueSettingData:
				self.PortraitID=storyFigueSettingData[self.PortraitID]
			else:
				print("Portrait ID "+str(self.PortraitID)+" missing from DB.")
				self.PortraitID=""
		
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

newData={}
with open("PartnerPosterData.tsv",'r') as f:
	f.readline()
	while True:
		line = f.readline()
		if not line:
			break
		info=line.split('\t')
		
		data = PartnerPosterData(info)
		newData[data.PosterID]=data.getTable()
		#print(data.getTable())
		#break
with open('biographies.json','wb') as f:
	f.write(json.dumps(newData, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	#print("Generated database.json")
