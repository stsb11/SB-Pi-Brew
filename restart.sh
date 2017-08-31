echo "Pi Boot-up script..."
echo "--------------------"
echo ""
echo "No-IP updater..."
cd /usr/local/bin/
sudo ./noip2
echo "DONE"
echo ""
echo "Sense Hat lights"
python3 /home/pi/mjpg-streamer/mjpg-streamer-experimental/www/lights.py &
echo "DONE"
echo ""
echo "Python3 sense hat data logger..."
python3 /home/pi/mjpg-streamer/mjpg-streamer-experimental/www/pi_data.py &
echo "DONE"
echo ""
echo "Restarting webcam..."
cd /home/pi/mjpg-streamer/mjpg-streamer-experimental
mjpg_streamer -i input_uvc.so -o "output_http.so -w ./www" &
echo "DONE"
echo ""
cd /home/pi
