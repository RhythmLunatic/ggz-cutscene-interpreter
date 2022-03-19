#!/usr/bin/env python3.8
import json
import sys

if len(sys.argv) < 3:
	print("usage: "+sys.argv[0]+" <file.json> <part number>")
	sys.exit(1)

database:dict = {}
with open("../database.json",'r') as f:
	database=json.loads(f.read())


output = "#LANGUAGES\tkey\ten\tch\tja"
with open(sys.argv[1],'r') as f:
	chapterFull = json.loads(f.read())
	cutscene = chapterFull[sys.argv[2]]
	for cmnd in cutscene:
		if cmnd[0]=="portraits":
			a = []
			b = []
			if cmnd[1][0]!="":
				a.append(cmnd[1][0])
				b.append(cmnd[1][1])
			if cmnd[2][0]!="":
				a.append(cmnd[2][0])
				b.append(cmnd[2][1])
			if len(a) > 0:
				output+="\nportrait\t"+"\t".join(a)
				for i in range(len(b)):
					output+="\nemote\t"+a[i]
		elif cmnd[0]=="msg":
			output+="\nmsg"
			#cmnd.resize(6)
			for i in range(1,5):
				if i==2 and cmnd[5]!=None: #For retranslated English, no need to keep the original
					output+="\t"+str(cmnd[5])
				else:
					output+="\t"+str(cmnd[i])
		elif cmnd[0]=="speaker":
			output+="\nspeaker\t"+database['speakers'][str(cmnd[1])][0]
		elif cmnd[0]=="choice":
			output+="\nchoice"
			for choice in cmnd[1:]:
				if choice[5]!=None:
					output+="\t"+choice[5]
				else:
					output+="\t"+choice[1]
		elif cmnd[0]=="bg":
			output+="\nbg\t"+cmnd[1]
print(output)