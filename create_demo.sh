#!/bin/bash
# Regenerate demo.gif for README
# Requires: vhs (brew install charmbracelet/tap/vhs)

set -e

# Create demo files with credible media names
rm -rf /tmp/demo_master /tmp/demo_other
mkdir -p /tmp/demo_master /tmp/demo_other

echo "movie content 1" > /tmp/demo_master/Inception.mkv
echo "movie content 1" > /tmp/demo_other/inception_2010.mkv

echo "movie content 2" > /tmp/demo_master/Matrix.mkv
echo "movie content 2" > /tmp/demo_other/the_matrix_1999.mkv

echo "movie content 3" > /tmp/demo_master/Interstellar.mkv
echo "movie content 3" > /tmp/demo_other/interstellar_hd.mkv

echo "tv content 1" > /tmp/demo_master/Breaking_Bad_S01E01.mkv
echo "tv content 1" > /tmp/demo_other/bb_pilot.mkv

echo "tv content 2" > /tmp/demo_master/Game_of_Thrones_S01E01.mkv
echo "tv content 2" > /tmp/demo_other/got_winter_is_coming.mkv

echo "doc content" > /tmp/demo_master/Planet_Earth.mkv
echo "doc content" > /tmp/demo_other/planet_earth_2006.mkv

echo "Created demo files in /tmp/demo_master and /tmp/demo_other"

# Generate GIF
cd "$(dirname "$0")"
rm -f demo.gif
vhs demo.tape

echo "Generated demo.gif"
ls -lh demo.gif
