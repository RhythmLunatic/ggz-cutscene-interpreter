#!/usr/bin/env python3.8
import deepl
import os
import sys
import json
from typing import List, Any, Dict,Tuple
import string

if len(sys.argv)<2:
	print("Usage: "+sys.argv[0]+" <file.json> <part number>")
	sys.exit(1)


langs = {"zh":3,"ja":4}
#If a sentence only contains these characters, filter it out
bannedSentences = set('…。!?,.…-—！')
def checkIsBanned(test_str):
    return set(test_str) <= bannedSentences

translations:Dict[str,Dict[int,str]] = {"zh":{},"ja":{}}
if os.path.exists("deepl_translations.json"):
	with open("deepl_translations.json",'r') as f:
		translations = json.load(f)

translator = deepl.Translator(os.environ['DEEPL_API_KEY'])
usage = translator.get_usage()
print("Used "+str(usage.character.count)+" of "+str(usage.character.limit)+".")
with open(sys.argv[1],'r') as f:
	chapterFull:Dict[str,List] = json.load(f)
	if len(sys.argv) > 2:
		partsToConvert = [sys.argv[2]]
	else:
		print("No parts specified, translating the whole chapter.")
		partsToConvert = chapterFull.keys()
	for i in partsToConvert:
		structuredLines = chapterFull[i]
		for cmnd in structuredLines:
			if cmnd[0]=="msg":
				if checkIsBanned(cmnd[3]):
					print("Skipping this message, contains no text: "+cmnd[3])
					continue
				for l in langs:
					txt:str = cmnd[langs[l]].replace("#n","")
					if l=="ja" and cmnd[langs['zh']]==cmnd[langs["ja"]]:
						print("Japanese is identical to Chinese, skipping.")
						continue
					elif txt!=None:
						translation:deepl.TextResult = translator.translate_text(txt, source_lang=l,target_lang="EN-US") #type: ignore
						translations[l][int(cmnd[1])]=translation.text
						print(l+": "+translation.text)
				print("")
				#break
with open("deepl_translations.json",'wb') as f:
	f.write(json.dumps(translations, sort_keys=False, indent='\t', separators=(',', ': '), ensure_ascii=False).encode('utf8'))