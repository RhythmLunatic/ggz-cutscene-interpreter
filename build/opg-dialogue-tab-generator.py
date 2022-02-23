#!/usr/bin/env python3.8
#The final form of the cutscene interpreter is converting from tab separated values, to json, back to tab separated values.
#Just kidding.
import json

exportLines:list=[]

with open("../chapterDatabase.json",'r') as f:
    db = json.load(f)
    for ep in db['story']['main'][1]['episodes']:
        with open('../avgtxt/'+ep['parts'],'r') as iop_f:
            iop = json.load(iop_f)
            for k in iop:
                for opcode in iop[k]:
                    print(opcode)
                    if opcode[0]=="msg":
                        newTSV=str(opcode[1])+"\t"
                        if opcode[5]:
                            newTSV+=opcode[5]
                        elif opcode[2]:
                            newTSV+="(O) "+opcode[2] #O for original
                        else:
                            newTSV+="(JP)"+opcode[4]
                        exportLines.append(newTSV.strip()+'\n')

with open("dialogue_2.tab",'w') as f:
    f.writelines(exportLines)