# Demo — replicates the original Arduino EE04-init.ino sketch in MicroPython.
#
# What it draws:
#   • White background
#   • Filled red circle at top-left
#   • Filled green square at top-right
#   • Horizontal black lines with "Hello ePaper" in blue below each

import time
from epaper import EPaper, BLACK, WHITE, RED, YELLOW, BLUE, GREEN

print("Initialising display…")
epd = EPaper()

print("Drawing…")
epd.fill(WHITE)

# Filled red circle at top-left (centre 25,25 radius 15)
epd.circle(25, 25, 15, RED, fill=True)

# Filled green square at top-right
epd.rect(epd.width - 40, 10, 30, 30, GREEN, fill=True)

# Horizontal lines with "Hello ePaper" below each
for i, y in enumerate([70, 130, 190, 250]):
    epd.line(10, y, epd.width - 10, y, BLACK)
    epd.text("Hello ePaper", 10, y + 8, BLUE)

print("Sending to display (this will take ~20 seconds)…")
epd.update()

print("Done!  Putting display to sleep.")
epd.sleep()
