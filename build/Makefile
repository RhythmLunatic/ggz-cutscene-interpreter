#objects := $(wildcard *.py)

build: 
	./convertToInterpreter.py
	./BuildSpeakerPortraitDatabase.py
	mv database.json ../
	mv biographies.json ../
	rsync -arv txtFixes/ ../avgtxt/
	
clean:
	git fetch origin
	git reset --hard origin/master

all:
	build

.PHONY: all
