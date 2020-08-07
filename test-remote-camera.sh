CAM=http://127.0.0.1:8585
echo starting video..
curl $CAM/start?fname=test >/dev/null
sleep 5
echo stopping..
curl $CAM/stop?fname=test >/dev/null
echo fetching..
time curl $CAM/send?fname=test >test.mp4.json
echo final video
ls -lh test.mp4.json
file test.mp4.json



