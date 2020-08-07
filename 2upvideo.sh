
CAM1="rpi"
CAM2="rpzw"

NAME=$1

if [ -d "$NAME" ]; then
	
	for file in `ls -1 $NAME/*joints.json | sed -e s/-joints.json//` 
	do	
		echo $file
		bash 2upvideo.sh $file
	done

	ls -1 $NAME/*2up.h264 | sed -e 's/^/file /g' > /tmp/2ups.txt
	ffmpeg -safe 0 -f concat -i /tmp/2ups.txt -c copy $NAME/ALL.h264


else

	ffmpeg \
		-i $NAME-$CAM1.h264 \
		-i $NAME-$CAM2.h264 \
		-filter_complex hstack \
		$NAME-2up.h264

fi
