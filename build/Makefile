#objects := $(wildcard *.py)

build: 
	wget http://ggz.amaryllisworks.pw:8880 -O TextMap_retranslated.json
	./convertToInterpreter.py
	./BuildSpeakerPortraitDatabase.py
	mv database.json ../
	#mv biographies.json ../
	rsync -arv txtFixes/ ../avgtxt/
	
clean:
	git fetch origin
	git reset --hard origin/master

all:
	build

.PHONY: all
