#!

PATTERN=${1}

#ffmpeg -r 30 -pattern_type glob -i ${PATTERN}/\*.jpg -vf scale=480:-1 -r 30 -f image2pipe -vcodec ppm - \
#    | convert -delay 0 -coalesce                    -layers Optimize -loop 0 - ${PATTERN}.gif
#

ffmpeg -r 30 -pattern_type glob -i ${PATTERN}/\*.jpg  -vf scale=-1:-1 -r 30 -f image2pipe -vcodec ppm - \
    |convert -crop 2670x2670+652+88 +repage -resize 480x480 - junk.gif
