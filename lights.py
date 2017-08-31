from sense_hat import SenseHat
sense = SenseHat()

for x in range (0,8):
    for y in range (0,8):
        sense.set_pixel(x, y, (220, 220, 220))
