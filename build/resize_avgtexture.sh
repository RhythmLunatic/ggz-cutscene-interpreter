#!/bin/bash
cd avgtexture
find . -name "*.png" -exec convert {} -gravity center -resize 1024x576! {} \;
#find . -name "*.png" -exec optipng {} \;
