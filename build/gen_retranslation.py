#!/usr/bin/env python3
import os

ans = input("Are you ABSOLUTELY sure you want to run this? This will overwrite TextMap_custom.tsv! Y/N\n")
if ans.lower() == "y":
	print("You asked for it...")
	textMap = {}
	
	if os.path.exists("TextMap_custom.tsv"):
		with open("TextMap_custom.tsv","r") as f:
			f.readline() # skip line 1
			while True:
				line = f.readline()
				if not line:
					break
				line=line.split('\t')
				line[-1]=line[-1].rstrip() #Strip newline char
				textMap[int(line[0])]=['XXX',line[-1]]
	
	with open("TextMap_aio.tsv",'r') as f:
		f.readline() # skip line 1
		while True:
			line = f.readline()
			if not line:
				break
			line=line.split('\t')
			line[-1]=line[-1].rstrip() #Strip newline char
			#if len(line)<4 or not line[0].strip():
			#	print("Skipping invalid line with wrong number of text")
			#	print(line)
			#	continue
			if int(line[0]) in textMap:
				textMap[int(line[0])][0]=line[1]
			else:
				textMap[int(line[0])]=[line[1],'XXX']
			
	with open("TextMap_custom.tsv","w") as f:
		f.write("TEXT_ID	EN	EN_RE\n")
		for textID in textMap:
			#print(textMap[textID])
			f.write(str(textID)+"\t"+"\t".join(textMap[textID])+"\n")
	print("Done!")
