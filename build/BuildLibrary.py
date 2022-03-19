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
		textMap[int(line[0])]=line[1:4] #No KR or TCH

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
CHINESE = 1
JAPANESE = 2
KOREAN = 3
TCHINESE = 4

toStr = ["EN","CN","JA","KR","TCH"]

txt = ""
for d in libraryDatas:
	txt+="<h3>"+d.name[ENGLISH]+"</h3>"
	txt+="<h4>"+" / ".join(d.name)+"</h4>"
	txt+="<p><b>Age:</b> "+" / ".join(d.age)
	txt+="</p><p><b>Birthday:</b> "+" <b>/</b> ".join(d.birthday)
	txt+="</p><p><b>Skill:</b></p>"
	for i in range(len(d.skill)):
		l=d.skill[i]
		txt+="<p><b>"+toStr[i]+" </b>"+l.replace("#n","<br>")+"</p>"
	txt+="</p><p><b>Description:</b></p> "
	for i in range(len(d.description)):
		l=d.description[i]
		txt+="<p><b>"+toStr[i]+" </b>"+l.replace("#n","<br>")+"</p>"
	txt+="<br><br>"

with open("LibraryData.html", 'w') as f:
	f.write(txt)

dictionary:List[dict] = []
with open(os.path.join("GameData","LibraryKeyWordData.tsv")) as f:
	f.readline() # skip first four lines, I don't know why they're here
	f.readline()
	f.readline()
	f.readline()
	while True:
		line = f.readline()
		if not line:
			break
		info=line.split('\t')
		dictionary.append({
			"name":textMap[int(info[1])],
			"desc":textMap[int(info[2])]
		})

txt = ""
for definition in dictionary:
	txt+="<h3>"+definition['name'][ENGLISH]+"</h3>"
	txt+="<h4>"+" / ".join(definition['name'])+"</h4>"
	for l in definition['desc']:
		txt+="<p>"+l+"</p>"
with open("LibraryDictionary.html",'w') as f:
	f.write(txt)