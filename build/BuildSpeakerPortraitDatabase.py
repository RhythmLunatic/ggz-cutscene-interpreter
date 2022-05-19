#!/usr/bin/env python3
import json as JSON
import os
import glob
import xml.etree.ElementTree as ET

class ResizingList(list):
	def extendListIfTooShort(self,idx):
		diff_len=idx-len(self)
		if diff_len > 0:
			self+=[None]*diff_len
	
	def __setitem__(self,i,val):
		self.extendListIfTooShort(i+1)
		super(ResizingList,self).__setitem__(i,val)

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
		self.StorySide=float(info[4])    #What the fuck is this even for???
		self.SpeakerName=int(info[5])  #This is a TextID, pulled from textMap_en
		                               #x,y coords of replacement face
		self.FacePosition=[round(float(h)) for h in info[6].split(";")]
		self.FlipOnOtherSide=(info[7]=="1")
		self.Scale=float(info[8])
		
	def getNormalizedFacePosition(self): #It's centered, so subtract half
		return (self.FacePosition[0]-128,1024-self.FacePosition[1]-128)

	def __str__(self) -> str:
		return ', '.join("%s: %s" % item for item in vars(self).items())

if __name__=='__main__':
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
			

	speakers = { "0":["","","","",""] }
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
				speakers[textID]=textMap[textID] #type: ignore
				

	musicDB = ResizingList([])
	for f in os.listdir("../audio"):
		if os.path.isfile("../audio/"+f) and "_" in f:
			n = int(f.split("_")[1])
			musicDB[n]=f[:-4]
			
	with open('database.json','wb') as f:
		f.write(JSON.dumps({'speakers':speakers,'portraits':portraits,'music':musicDB}, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
		print("Generated database.json")
