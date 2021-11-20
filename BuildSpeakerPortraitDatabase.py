#!/usr/bin/env python3
import json as JSON


print("Plz wait, loading all text!")
textMap = {}
with open("TextMap_en.tsv",'r') as f:
	f.readline() # skip line 1
	while True:
		line = f.readline()
		if not line:
			break
		line=line.split('\t')
		textMap[int(line[0])]=line[1:]
		
if True:
	#TEXT_ID	EN	CN	JP	KR	TCN
	files = {2:"TextMap_cn.tsv",3:"TextMap_jp.tsv"}
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
		

speakers = {}
portraits = {}

for ID in storyFigueSettingData:
	d = storyFigueSettingData[ID]
	if d['SpeakerName'] in textMap:
		speakers[d['SpeakerName']]=textMap[d['SpeakerName']]
	portraits[ID]=[d['pic'].lower()+'.png']

story = {
	"main":[{
		"name":"testing...",
		"episodes":[]
	}],
	"side":[],
	"event":[],
	"crossover":[]
}
for i in range(0,22):
	story['main'][0]['episodes'].append({
		"name":"IDs "+str(i*10)+"-"+str(i*10+9),
		"parts":"output-"+str(i)+".json"
	})

		
with open('database.json','wb') as f:
	f.write(JSON.dumps({'speakers':speakers,'portraits':portraits}, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))
	print("Generated database.json")
