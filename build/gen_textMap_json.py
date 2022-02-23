#!/usr/bin/env python3
import json

newJSON = {}
with open("GameData/TextMap_en.tsv",'r') as f:
    f.readline()
    while True:
        line = f.readline()
        if not line:
            break
        line=line.split('\t')
        if line[1].strip()!="XXX":
            newJSON[int(line[0])]=line[1]

with open("TextMap_retranslated.json",'r') as f:
    retranslated = json.loads(f.read())
    for k in retranslated:
        newJSON[int(k)]=retranslated[k].replace("//n","\n")

with open('TextMap_en_re.json','wb') as f:
	f.write(json.dumps(newJSON, sort_keys=False, separators=(',', ': '), indent='\t', ensure_ascii=False).encode('utf8'))
	print("Generated.")
