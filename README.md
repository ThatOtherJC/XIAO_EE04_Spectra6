# EE04 ePaper MicroPython Template

A working MicroPython driver and demo for the **Seeed XIAO EE04 board** with the **7.3-inch Spectra6 6-color e-ink display**. Use this as a starting point for your own projects.

---

## Hardware

| Component | Part |
|-----------|------|
| Microcontroller board | [Seeed XIAO ePaper Display Board EE04](https://www.seeedstudio.com/XIAO-ePaper-Display-Board-EE04-p-6560.html) (XIAO ESP32-S3 Plus) |
| Display | [7.3-inch Spectra6 ePaper — 800×480, 6-color](https://www.seeedstudio.com/7-3inch-Six-Color-eInk-ePaper-Display-with-800x480-Pixels-p-6567.html) |
| Display driver IC | ED2208 |
| Connection | 50-pin FPC — set the EE04 jumper to **50 Pin** |

> ⚠️ Make sure the jumper on the EE04 board is set to **50 Pin** before powering on. The wrong setting will prevent the display from working.

---

## What's in this repo

| File | Purpose |
|------|---------|
| `epaper.py` | The driver — copy this to every project that uses this hardware |
| `main.py` | Demo sketch: white background, red circle, green square, blue text |
| `color_test.py` | Diagnostic tool that draws all 6 color bands so you can verify wiring |

---

## Setup

### 1. Flash MicroPython onto the board

The board ships ready for Arduino. You need to replace the firmware with MicroPython once.

1. Download the latest **ESP32-S3 with SPIRAM** firmware from [micropython.org/download/ESP32_GENERIC_S3](https://micropython.org/download/ESP32_GENERIC_S3/) — look for the file in the section labelled `Support for Octal-SPIRAM`.
   
   For example: ESP32_GENERIC_S3-SPIRAM_OCT-20260406-v1.28.0.bin
2. Install esptool:
   ```
   pip install esptool
   ```
3. Hold the **BOOT** button on the XIAO, plug in USB, then release.
4. Erase the old firmware (replace the port with your actual port):
   ```
   esptool --port /dev/tty.usbmodem* erase-flash
   ```
   On Windows the port will be something like `COM3`.
5. Flash MicroPython:
   ```
   esptool --chip esp32s3 --port /dev/tty.usbmodem* write-flash -z 0x0 firmwareyourdownloaded.bin
   ```
6. Unplug and replug the USB cable (no need to hold BOOT this time).

### 2. Install Thonny

[Thonny](https://thonny.org) is the easiest way to work with MicroPython boards — it has a built-in file manager and REPL console.

1. Download and open Thonny.
2. Go to **Tools → Options → Interpreter**.
3. Select **MicroPython (ESP32)** from the dropdown.
4. Select your serial port and click OK.
5. You should see a `>>>` prompt in the Shell panel — the board is alive.

### 3. Upload the files

In Thonny, open each file and go to **File → Save As → MicroPython device**:

- Upload `epaper.py` first (the driver must be present before anything else can import it).
- Upload `main.py`.
- Upload `color_test.py` if you want the diagnostic tool.

### 4. Run the demo

With `main.py` open, press the green **Run** button (▶) in Thonny. Watch the Shell panel:

```
Initialising display…
Drawing…
Sending to display (this will take ~20 seconds)…
Triggering refresh (please wait ~20 s)…
Refresh complete.
Done!  Putting display to sleep.
```

The refresh takes 15–30 seconds — this is normal for a 6-color e-ink display.

---

## Pin mapping

These are the raw GPIO numbers used in MicroPython (sourced from the EE04 hardware schematic).

| Signal | GPIO | EE04 label | Notes |
|--------|------|-----------|-------|
| SPI SCK | 7 | D8 | SPI clock |
| SPI MOSI | 9 | D10 | Data to display |
| CS | 44 | D7 | Chip select, active LOW |
| DC | 10 | — | Data/Command select |
| BUSY | 4 | D3 | HIGH while display is refreshing |
| RST | 38 | — | Active LOW reset |
| ENABLE | 43 | D6 | **Must be driven HIGH** or the display gets no power |
| Button 1 | 2 | D1/A1 | Active LOW, use INPUT_PULLUP |
| Button 2 | 3 | D2/A2 | Active LOW, use INPUT_PULLUP |
| Button 3 | 5 | D4/A4 | Active LOW, use INPUT_PULLUP |
| Battery ADC | 1 | A0 | Analog voltage reading |
| ADC enable | 6 | A5 | Drive HIGH before reading battery voltage |

> The ENABLE pin (GPIO 43) is the most common source of a blank screen. The driver sets it HIGH automatically in `__init__`, but if you ever control pins manually make sure this one stays HIGH.

---

## Color constants

The Spectra6 panel supports 6 colors. Wire codes were confirmed by running `color_test.py` on the physical hardware.

| Constant | Wire code | Color |
|----------|-----------|-------|
| `BLACK` | 0 | Black |
| `WHITE` | 1 | White |
| `YELLOW` | 2 | Yellow |
| `RED` | 3 | Red |
| `WHITE2` | 4 | White (treat as unused) |
| `BLUE` | 5 | Blue |
| `GREEN` | 6 | Green |

Import them directly from `epaper.py`:

```python
from epaper import EPaper, BLACK, WHITE, RED, YELLOW, BLUE, GREEN
```

---

## Drawing API

Create one `EPaper` instance. The driver initialises the display and allocates the frame buffer automatically.

```python
from epaper import EPaper, BLACK, WHITE, RED, YELLOW, BLUE, GREEN

epd = EPaper()
```

All drawing methods write into an in-memory frame buffer. Nothing appears on the screen until you call `epd.update()`.

### Fill the background

```python
epd.fill(WHITE)
```

### Draw a filled rectangle

```python
epd.rect(x, y, width, height, color, fill=True)
```

Outline only:

```python
epd.rect(x, y, width, height, color)   # fill defaults to False
```

### Draw a line

```python
epd.line(x1, y1, x2, y2, color)
```

### Draw a circle

```python
epd.circle(cx, cy, radius, color, fill=True)   # filled
epd.circle(cx, cy, radius, color)              # outline only
```

### Draw a single pixel

```python
epd.pixel(x, y, color)
```

### Draw text

Uses the built-in MicroPython 8×8 pixel font.

```python
epd.text("Hello!", x, y, color)
```

### Send to the screen

Pushes the frame buffer to the display and triggers a full refresh. Takes 15–30 seconds.

```python
epd.update()
```

### Sleep and wake

The e-ink panel retains its image with zero power while sleeping.

```python
epd.sleep()    # image stays on screen, display uses ~0 mW
epd.wake()     # re-initialises, ready to draw again
```

---

## Minimal project template

```python
from epaper import EPaper, BLACK, WHITE, RED, YELLOW, BLUE, GREEN

epd = EPaper()

epd.fill(WHITE)

# --- your drawing code here ---
epd.text("My Project", 10, 10, BLACK)
epd.rect(10, 30, 200, 4, RED, fill=True)
# --- end drawing ---

epd.update()
epd.sleep()
```

---

## Useful tips

**Refresh time is always slow.** E-ink displays need 15–30 seconds for a full 6-color refresh. This is a hardware constraint, not a software one. Plan your project around infrequent updates — e-ink is ideal for dashboards, labels, and status displays that change every few minutes or hours.

**The image persists with no power.** Once `epd.update()` completes and you call `epd.sleep()`, you can cut power entirely and the image stays on screen. This makes e-ink extremely efficient for battery-powered projects.

**Deep sleep between updates.** After `epd.sleep()`, put the ESP32-S3 into deep sleep to save battery:

```python
import machine
epd.sleep()
machine.deepsleep(60_000)   # wake after 60 seconds
```

On wake, MicroPython restarts from the top of `main.py`, so call `EPaper()` again to re-initialise.

**Reading the user buttons:**

```python
import machine

btn1 = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)
btn2 = machine.Pin(3, machine.Pin.IN, machine.Pin.PULL_UP)
btn3 = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

if btn1.value() == 0:   # LOW = pressed
    print("Button 1 pressed")
```

**Reading battery voltage:**

```python
import machine, time

adc_en = machine.Pin(6, machine.Pin.OUT)
adc_en.value(1)           # enable the ADC circuit
time.sleep_ms(10)         # allow it to settle

adc = machine.ADC(machine.Pin(1))
adc.atten(machine.ADC.ATTN_11DB)
voltage = (adc.read() / 4095.0) * 7.16
print(f"Battery: {voltage:.2f} V")
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Blank screen, no error | ENABLE pin not HIGH | Check GPIO 43 is driven HIGH — the driver does this automatically, so make sure `epaper.py` is uploaded correctly |
| `EPaper busy timeout` | Display stuck in BUSY state | Power-cycle the board and retry. Check the FPC cable is fully inserted and the jumper is set to 50 Pin |
| Wrong colors | Color mapping mismatch | Run `color_test.py` and compare the numbered bands against the constants in `epaper.py` |
| `ImportError: no module named 'epaper'` | Driver not on the board | Upload `epaper.py` to the MicroPython device via Thonny |
| Refresh never finishes | BUSY pin issue | Verify GPIO 4 is the BUSY signal — check nothing else is holding it HIGH |

---

## Resources

- [Seeed EE04 Wiki](https://wiki.seeedstudio.com/epaper_ee04/)
- [MicroPython ESP32 quick reference](https://docs.micropython.org/en/latest/esp32/quickref.html)
- [MicroPython framebuf docs](https://docs.micropython.org/en/latest/library/framebuf.html)
- [7.3-inch Spectra6 datasheet](https://wiki.seeedstudio.com/epaper_ee04/) *(linked from the EE04 wiki Resources section)*

---

## License

MIT — use freely, attribution appreciated but not required.
