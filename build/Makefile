#objects := $(wildcard *.py)

build: 
	wget https://ggz.amaryllisworks.pw:8880/en_re -O TextMap_retranslated_en_re.json
	wget https://ggz.amaryllisworks.pw:8880/pt -O TextMap_retranslated_pt.json
	./convertToInterpreter.py
	./BuildSpeakerPortraitDatabase.py
	mv database.json ../
	#mv biographies.json ../
	rsync -arv txtFixes/ ../avgtxt/
	
clean:
	git fetch origin
	git reset --hard origin/master

dist:
	cd ../
	echo "$PWD"
	rclone sync --progress --size-only avgtxt sigma:/var/www/ggz/avgtxt
	rclone sync chapterDatabase.json sigma:/var/www/ggz/
	rclone sync --size-only index.html sigma:/var/www/ggz/
	cd -

all:
	build

.PHONY: all
