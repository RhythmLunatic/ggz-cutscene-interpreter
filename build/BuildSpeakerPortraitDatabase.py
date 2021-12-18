#!/usr/bin/env python3
import json as JSON
import os
import glob

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

class StoryFigureSettingDataStruct():
	def __init__(self, info):
		self.pic=info[1]
		self.DevY=info[2]
		self.StorySide=int(info[3])    #What the fuck is this even for???
		self.SpeakerName=int(info[4])  #This is a TextID, pulled from textMap_en
		                               #x,y coords of replacement face
		self.FacePosition=[round(float(h)) for h in info[5].split(";")]
		self.FlipOnOtherSide=(info[6]=="1")
		self.Scale=float(info[7])
		
	def getNormalizedFacePosition(self):
		return (self.FacePosition[0]-128,1024-self.FacePosition[1]-128)
		
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
		

speakers = {}
portraits = {}

for ID in storyFigueSettingData:
	d = storyFigueSettingData[ID]
	if d.SpeakerName in textMap:
		speakers[d.SpeakerName]=textMap[d.SpeakerName]
	portraits[ID]=[d.pic.lower()+'.png']
	for i in range(25):
		fName = d.pic.lower()+"_"+str(i).zfill(3)+".png"
		if os.path.isfile(os.path.join(os.getcwd(),"../pic/",fName)):
			if len(portraits[ID]) < 2: #001 is identical to 0 so just duplicate it
				portraits[ID].append(portraits[ID][0])
			print("found "+fName)
			portraits[ID].append(fName)
			
	#variants = glob.glob(os.path.join(os.getcwd(),"../pic/",d.pic.lower())+"_*")
	#if len(variants) > 0:
		
	#print(variants)
	

with open(os.path.join("GameData","PartnerPosterData.tsv"),'r') as f:
	f.readline()
	while True:
		line = f.readline()
		if not line:
			break
		info=line.split('\t')
		textID = int(info[4])
		if textID in textMap and textID not in speakers:
			speakers[textID]=textMap[textID]
			

		
with open('database.json','wb') as f:
	f.write(JSON.dumps({'speakers':speakers,'portraits':portraits}, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated database.json")
