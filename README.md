# SB-Pi-Brew
Climate monitoring system for brew

Hardware
--------
DS18B20 probe. 3.3V, GND and GPIO4 (pin 7). Used for external temperature.
Add a 4k7 resistor between data and power.

Pi sense hat. Will need breaking out for better temperature accuracy,
and to provide access to the extra pins for the DS18B20.
Sense hat will also provide light for webcam.

Cheapo USB webcam.

Install
-------
Install mjpg-streamer (to stream the webcam).
Install matplotlib to render the graphs.
Copy all the HTML and py files into the mjpg-streamer/mjpg-streamer/www/ dir.
Set up a cronjob to fire up the restart.py script on reboot (for auto-start).
Browse to IP address in a browser to test.