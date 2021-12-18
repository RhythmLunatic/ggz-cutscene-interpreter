#!/bin/bash
cd avgtexture
find *.png -exec convert {} -gravity center -rezise 1024x576! {} \;
