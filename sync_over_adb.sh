#!/bin/bash

set -e

adb push zentral_und_ostalpen_de.txt sdcard/Android/data/org.xcsoar/files
adb push zentral_und_ostalpen_de.cup sdcard/Android/data/org.xcsoar/files
adb push images/zentral_und_ostalpen_de/* sdcard/Android/data/org.xcsoar/files/images/zentral_und_ostalpen_de
