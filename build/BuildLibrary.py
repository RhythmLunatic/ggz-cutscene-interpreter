#!/usr/bin/env python3.8
import sys
import json
import os
from typing import Dict,List,Any
from enum import Enum

textMap:Dict[int,List[Any]] = {}

with open("TextMap_aio.tsv",'r') as f:
	f.readline() # skip line 1
	while True:
		line = f.readline()
		if not line:
			break
		line=line.split('\t')
		line[-1]=line[-1].rstrip() #Strip newline char
		textMap[int(line[0])]=line[1:]

class LDType(Enum):
	CHARACTER = 1
	BOSS = 2
	ENEMY = 3
	UNKNOWN = 4

#ID	Icon	Type	DrawingID	DevX	DevY	AvatarID	Scale	AvatarOffX	AvatarOffY	Charaname	Age	Birth	Des	Skill	Voice	Voicename	EliteID	EliteName	EliteDes	IsUnlock
class LibraryData():
	def __init__(self,info):
		self.icon:int = int(info[1])
		self.type:LDType = LDType(int(info[2]))
		self.drawingID:str = info[3]
		#we don't care about 4,5,6,7,8,9
		self.name:List[str] = textMap[int(info[10])]
		self.age:List[str] = textMap[int(info[11])]
		self.birthday:List[str] = textMap[int(info[12])]
		self.description:List[str] = textMap[int(info[13])]
		self.skill:List[str] = textMap[int(info[14])]
		#voice lines info[15]
		#voice names info[16]
		#Everything else is useless


libraryDatas:List[LibraryData] = []
with open(os.path.join("GameData","LibraryData.tsv")) as f:
	f.readline() # skip first four lines, I don't know why they're here
	f.readline()
	f.readline()
	f.readline()
	while True:
		line = f.readline()
		if not line:
			break
		info=line.split('\t')
		if info[2]=="4": #It's a different struct, dunno why it's here
			continue
		libraryDatas.append(LibraryData(info))

#Fuck it
ENGLISH = 0
CHINESE = 2
JAPANESE = 3
KOREAN = 4
TCHINESE = 5

txt = ""
for d in libraryDatas:
	txt+="<h3>"+d.name[ENGLISH]+"</h3>"
	txt+="<p><b>Age:</b> "+d.age[ENGLISH]
	txt+="</p><p><b>Birthday:</b> "+d.birthday[ENGLISH]
	txt+="</p><p><b>Skill:</b> "+d.skill[ENGLISH].replace("#n","<br>")
	txt+="</p><p><b>Description:</b> "+d.description[ENGLISH]+'</p><br><br>'

with open("LibraryData.html", 'w') as f:
	f.write(txt)