
CAM1="rpi"
CAM2="rpzw"

NAME=$1

if [ "x$1" = "x--montage" ]; then	
	NAME=$(echo $2 | sed -e 's/\/$//g')
	echo MONTAGING $NAME
	ls -1 $NAME/*2up.h264 | sed -e 's/^/file /g' | shuf > 2ups-files.txt
	ffmpeg -safe 0 -f concat -i 2ups-files.txt -c copy $NAME/ALL.h264
	exit 0
fi

if [ -d "$NAME" ]; then
	for file in `ls -1 $NAME/*joints.json | sed -e s/-joints.json//` 
	do	
		echo $file
		bash 2upvideo.sh $file
	done
	bash 2upvideo.sh --montage $NAME
	exit 0
else
	ffmpeg \
		-i $NAME-$CAM1.h264 \
		-i $NAME-$CAM2.h264 \
		-filter_complex hstack \
		$NAME-2up.h264
fi
