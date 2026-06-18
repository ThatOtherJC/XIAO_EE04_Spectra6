# Color identification test — 7 bands (wire codes 0-6).
# Uses fill_rect so it runs fast instead of pixel-by-pixel.
# Look at the screen and confirm what color band 6 is.

from epaper import EPaper, BLACK, WHITE

epd = EPaper()
epd.fill(WHITE)

num_bands = 7
band_w = epd.width // num_bands  # ~114 px each

for i in range(num_bands):
    x = i * band_w
    epd.rect(x, 0, band_w, epd.height - 60, i, fill=True)
    # Number label centred in the white strip at the bottom
    label_x = x + band_w // 2 - 4
    epd.text(str(i), label_x, epd.height - 45, BLACK)

epd.update()
epd.sleep()
