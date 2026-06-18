# MicroPython driver for the 7.3" Spectra6 6-color e-ink display
# on the Seeed XIAO EE04 board (XIAO ESP32-S3 Plus + ED2208 driver IC).
#
# Pin mapping (raw GPIO numbers, sourced from EPaper_Board_Pins_Setups.h):
#   SPI SCK  → GPIO 7  (D8)
#   SPI MOSI → GPIO 9  (D10)
#   CS       → GPIO 44 (D7)
#   DC       → GPIO 10
#   BUSY     → GPIO 4  (D3)
#   RST      → GPIO 38
#   ENABLE   → GPIO 43 (D6) — must be HIGH to power the display logic
#
# Wire color codes (4 bits per pixel, sent to ED2208 — confirmed on hardware):
#   BLACK  = 0x0   WHITE  = 0x1   YELLOW = 0x2   RED    = 0x3
#   WHITE2 = 0x4   BLUE   = 0x5   GREEN  = 0x6

import machine
import time
import framebuf

# Display dimensions
WIDTH  = 800
HEIGHT = 480

# Color constants — confirmed against the physical Spectra6 panel
BLACK  = 0x0
WHITE  = 0x1
YELLOW = 0x2
RED    = 0x3
WHITE2 = 0x4  # second white — treat as unused
BLUE   = 0x5
GREEN  = 0x6


class EPaper:
    def __init__(self):
        # Enable pin powers up the display logic board — must come first
        self._enable = machine.Pin(43, machine.Pin.OUT)
        self._enable.value(1)

        # Control pins
        self._cs   = machine.Pin(44, machine.Pin.OUT, value=1)
        self._dc   = machine.Pin(10, machine.Pin.OUT, value=0)
        self._rst  = machine.Pin(38, machine.Pin.OUT, value=1)
        self._busy = machine.Pin(4,  machine.Pin.IN)

        # SPI bus — the ED2208 can handle up to 20 MHz; 10 MHz is safe
        self._spi = machine.SPI(
            1,
            baudrate=10_000_000,
            polarity=0,
            phase=0,
            sck=machine.Pin(7),
            mosi=machine.Pin(9),
            miso=machine.Pin(8),
        )

        # Frame buffer: 4 bits per pixel (GS4_HMSB), 2 pixels per byte
        # High nibble = left pixel, low nibble = right pixel
        self._buf = bytearray(WIDTH * HEIGHT // 2)
        self._fb  = framebuf.FrameBuffer(self._buf, WIDTH, HEIGHT, framebuf.GS4_HMSB)
        self.width  = WIDTH
        self.height = HEIGHT

        self._init_display()

    # ------------------------------------------------------------------
    # Low-level SPI helpers
    # ------------------------------------------------------------------

    def _cmd(self, cmd):
        """Send a single command byte."""
        self._dc.value(0)
        self._cs.value(0)
        self._spi.write(bytes([cmd]))
        self._cs.value(1)

    def _data(self, *values):
        """Send one or more data bytes."""
        self._dc.value(1)
        self._cs.value(0)
        self._spi.write(bytes(values))
        self._cs.value(1)

    def _wait_busy(self, timeout_ms=30_000):
        """Block until the BUSY pin goes LOW (display is idle)."""
        start = time.ticks_ms()
        time.sleep_ms(10)
        while self._busy.value() == 1:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                raise RuntimeError("EPaper busy timeout")
            time.sleep_ms(10)

    def _reset(self):
        self._rst.value(0)
        time.sleep_ms(20)
        self._rst.value(1)
        time.sleep_ms(10)

    # ------------------------------------------------------------------
    # Display initialisation  (derived from ED2208_Init.h)
    # ------------------------------------------------------------------

    def _init_display(self):
        self._reset()

        self._cmd(0xAA)           # Command header unlock
        self._data(0x49, 0x55, 0x20, 0x08, 0x09, 0x18)

        self._cmd(0x01)           # PWRR — power setting
        self._data(0x3F, 0x00, 0x32, 0x2A, 0x0E, 0x2A)

        self._cmd(0x00)           # PSR — panel setting
        self._data(0x5F, 0x69)

        self._cmd(0x03)           # POFS — power-off sequence
        self._data(0x00, 0x54, 0x00, 0x44)

        self._cmd(0x05)           # BTST1 — booster 1
        self._data(0x40, 0x1F, 0x1F, 0x2C)

        self._cmd(0x06)           # BTST2 — booster 2
        self._data(0x6F, 0x1F, 0x16, 0x25)

        self._cmd(0x08)           # BTST3 — booster 3
        self._data(0x6F, 0x1F, 0x1F, 0x22)

        self._cmd(0x13)           # IPC
        self._data(0x00, 0x04)

        self._cmd(0x30)           # PLL — clock
        self._data(0x02)

        self._cmd(0x41)           # TSE — temperature sensor enable
        self._data(0x00)

        self._cmd(0x50)           # CDI — VCOM and data interval
        self._data(0x3F)

        self._cmd(0x60)           # TCON — gate/source non-overlap
        self._data(0x02, 0x00)

        self._cmd(0x61)           # TRES — resolution (800 × 480)
        self._data(0x03, 0x20, 0x01, 0xE0)

        self._cmd(0x82)           # VDCS — VCOM DC setting
        self._data(0x1E)

        self._cmd(0x84)           # T_VDCS
        self._data(0x01)

        self._cmd(0x86)           # AGID
        self._data(0x00)

        self._cmd(0xE3)           # PWS — power saving
        self._data(0x2F)

        self._cmd(0xE0)           # CCSET
        self._data(0x00)

        self._cmd(0xE6)           # TSSET
        self._data(0x00)

        self._cmd(0x04)           # PON — power on
        self._wait_busy()

    # ------------------------------------------------------------------
    # Drawing API  (thin wrappers around framebuf)
    # ------------------------------------------------------------------

    def fill(self, color):
        """Fill the entire screen with one color."""
        self._fb.fill(color)

    def pixel(self, x, y, color):
        self._fb.pixel(x, y, color)

    def rect(self, x, y, w, h, color, fill=False):
        if fill:
            self._fb.fill_rect(x, y, w, h, color)
        else:
            self._fb.rect(x, y, w, h, color)

    def line(self, x1, y1, x2, y2, color):
        self._fb.line(x1, y1, x2, y2, color)

    def text(self, string, x, y, color):
        """Draw text using the built-in 8×8 pixel font."""
        self._fb.text(string, x, y, color)

    def circle(self, x, y, r, color, fill=False):
        """Draw a circle.  MicroPython framebuf has ellipse() from v1.20."""
        try:
            self._fb.ellipse(x, y, r, r, color, fill)
        except AttributeError:
            # Fallback for older firmware: draw pixel-by-pixel
            self._circle_fallback(x, y, r, color, fill)

    def _circle_fallback(self, cx, cy, r, color, fill):
        x, y, d = r, 0, 1 - r
        while x >= y:
            pts = [(cx+x,cy+y),(cx-x,cy+y),(cx+x,cy-y),(cx-x,cy-y),
                   (cx+y,cy+x),(cx-y,cy+x),(cx+y,cy-x),(cx-y,cy-x)]
            if fill:
                for px, py in pts:
                    self._fb.line(cx, py, px, py, color)
            else:
                for px, py in pts:
                    self._fb.pixel(px, py, color)
            y += 1
            if d < 0:
                d += 2*y + 1
            else:
                x -= 1
                d += 2*(y - x) + 1

    # ------------------------------------------------------------------
    # Display update — sends the framebuffer to the screen and refreshes
    # ------------------------------------------------------------------

    def update(self):
        """Push the framebuffer to the display and trigger a full refresh.

        This takes 15–30 seconds.  Do not call any other methods until it
        returns.
        """
        print("Sending pixel data…")
        self._cmd(0x10)           # DTM — data transmission start
        self._dc.value(1)
        self._cs.value(0)

        bytes_per_row = WIDTH // 2
        for row in range(HEIGHT):
            row_start = row * bytes_per_row
            # Each stored byte holds 2 pixels as nibbles with wire color values.
            # Remap each nibble through COLOR_GET to match what the ED2208 expects.
            out = bytearray(bytes_per_row)
            for col in range(bytes_per_row):
                b = self._buf[row_start + col]
                c1 = _color_get((b >> 4) & 0x0F)
                c2 = _color_get(b & 0x0F)
                out[col] = (c1 << 4) | c2
            self._spi.write(out)

        self._cs.value(1)

        print("Triggering refresh (please wait ~20 s)…")
        self._cmd(0x12)           # DRF — display refresh
        self._data(0x00)
        time.sleep_ms(1)
        self._wait_busy(timeout_ms=60_000)
        print("Refresh complete.")

    def sleep(self):
        """Put the display into deep sleep.  The image is retained."""
        self._cmd(0x02)           # POF — power off
        self._data(0x00)
        self._wait_busy()

    def wake(self):
        """Wake the display from deep sleep (re-runs init)."""
        self._init_display()


# ------------------------------------------------------------------
# Color lookup table (mirrors COLOR_GET macro from ED2208_Defines.h)
# Maps the 4-bit value stored in the framebuffer to the wire code
# the ED2208 expects.
#
# framebuf value → ED2208 wire code (confirmed on physical panel):
#   BLACK  (0)   WHITE  (1)   YELLOW (2)   RED    (3)
#   WHITE2 (4)   BLUE   (5)   GREEN  (6)
#
# Values 0-6 map straight through.  Anything else → black.
# ------------------------------------------------------------------

_COLOR_LUT = bytes([
    0x0,  # 0  BLACK
    0x1,  # 1  WHITE
    0x2,  # 2  YELLOW
    0x3,  # 3  RED
    0x4,  # 4  WHITE2 (unused)
    0x5,  # 5  BLUE
    0x6,  # 6  GREEN
    0x0,  # 7  (unused → black)
    0x0,  # 8  (unused → black)
    0x0,  # 9  (unused → black)
    0x0,  # 10 (unused → black)
    0x0,  # 11 (unused → black)
    0x0,  # 12 (unused → black)
    0x0,  # 13 (unused → black)
    0x0,  # 14 (unused → black)
    0x0,  # 15 (unused → black)
])

def _color_get(nibble):
    return _COLOR_LUT[nibble & 0x0F]
