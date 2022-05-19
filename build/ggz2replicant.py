#!/usr/bin/env python3.8
import json
import sys
from typing import List, Any, Dict,Tuple

if len(sys.argv) < 4:
	print("usage: "+sys.argv[0]+" <file.json> <part number> <output filename>")
	sys.exit(1)

database:dict = {}
with open("../database.json",'r') as f:
	database=json.loads(f.read())

langs = {"ch":2,"ja":3}

#BEHOLD, OVERENGINEERED GARBAGE
#Because we opted to separate each translation into its own file
#and now the message needs its own structure
#all you really need to know is the array is structured like
# ['msg', message, translation note, comment, etc]
# The interpreter will only read the first three elements of the array, so you can put anything you want afterwards.
#class message():

def convertCutscene(chapterFull:Dict[str,List],toConvert:str)->str:
	cutscene=chapterFull[toConvert]
	output = ""
	#outputAdditional:List[str] = [""]*5
	for i in range(len(cutscene)):
		cmnd=cutscene[i]
		if cmnd[0]=="portraits":
			a = []
			b = []
			if cmnd[1][0]!="":
				a.append(str(cmnd[1][0]))
				b.append(str(cmnd[1][1]))
			if cmnd[2][0]!="":
				a.append(str(cmnd[2][0]))
				b.append(str(cmnd[2][1]))
			if len(a) > 0:
				output+="\nportraits\t"+"\t".join(a)
				for i in range(len(b)):
					output+="\nemote\t"+a[i]+"\t"+b[i]
		elif cmnd[0]=="msg":
			tmp_msg = '\nmsg\t'+str(cmnd[1])+'\t'
			if cmnd[5]!=None:
				tmp_txt = str(cmnd[5].replace("//n","\\n"))
				if "(TN:" in tmp_txt:
					start = tmp_txt.find("(TN:")
					end = tmp_txt.find(")",start)
					tmp_msg+=tmp_txt[0:start]+tmp_txt[end+1:] #Append message
					output+="\ntn\t"+tmp_txt[start+5:end] #Append TL note
				else:
					tmp_msg+=str(tmp_txt)
			else:
				tmp_msg+=cmnd[2]
			for col in langs:
				tmp_msg+="\t"+cmnd[langs[col]+1] #+1 because idx 0 is the msg command
			output+=tmp_msg
			# tmp_msg:List[str] = ['msg','','','[GGZID='+str(cmnd[1])+']'] #index 3 is comment tag, this will be filled with ggz text IDs just in case it's needed in the future.
			# if cmnd[5]!=None:
			# 	tmp_txt = str(cmnd[5].replace("//n","\\n"))
			# 	if "(TN:" in tmp_txt:
			# 		start = tmp_txt.find("(TN:")
			# 		end = tmp_txt.find(")",start)
			# 		tmp_msg[1]=tmp_txt[0:start]+tmp_txt[end+1:] #Append message
			# 		tmp_msg[2]=tmp_txt[start+5:end] #Append TL note
			# 	else:
			# 		tmp_msg[1]=str(tmp_txt)
			# else:
			# 	tmp_msg[1]=cmnd[2]
			
			# output+="\n"+"\t".join(tmp_msg)

			# for col in langs:
			# 	outputAdditional[langs[col]]+="\nmsg\t"+cmnd[langs[col]+1] #+1 because idx 0 is the msg command
			
		elif cmnd[0]=="speaker":
			output+="\nspeaker\t"+database['speakers'][str(cmnd[1])][0]
			#Note that we will ALWAYS use the english speaker because the speaker database uses english speakers as the key.
			#for col in langs:
			#	outputAdditional[langs[col]]+="\nspeaker\t"+database['speakers'][str(cmnd[1])][0]
		elif cmnd[0]=="choice":
			output+="\nchoice"
			#for col in langs:
			#	outputAdditional[langs[col]]+="\nchoice"

			for choice in cmnd[1:]:
				if choice[4]!=None:
					output+="\t"+choice[4]
				else:
					output+="\t"+choice[1]
				for col in langs:
					output+=" ## "+choice[langs[col]] #+1 because idx 0 is the msg command
			
			#This is where the fun begins
			if i+1 < len(cutscene):
				output+="\ncondjmp_c\tc2dest\t2"
				dests = cutscene[i+1][2:]
				for j in range(len(dests)):
					output+="\nlabel\tc"+str(j+1)+"dest"
					output+=convertCutscene(chapterFull,str(dests[j]))
					if j==0:
						output+='\njmp\tend_choices'
				output+='\nlabel\tend_choices'
					#for col in langs:
					#	outputAdditional[langs[col]]+=outputAdd_tmp[langs[col]] #+1 because idx 0 is the msg command
				#print(dests)

		elif cmnd[0]=="bg":
			output+="\nbg\t"+cmnd[1]

	return output


with open(sys.argv[1],'r') as f:
	chapterFull = json.loads(f.read())
	#cutscene = chapterFull[sys.argv[2]]
	outputTxt = "#LANGUAGES\tKEY\tEN\tCH\tJP" + convertCutscene(chapterFull,sys.argv[2])
	
	print(outputTxt)
	#for l in langs:
	#	print(outputAddit[langs[l]])