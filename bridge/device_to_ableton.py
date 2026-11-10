#!/usr/bin/env python3
"""Read Kinetic Echo's six values over USB serial and drive Ableton via MIDI.

The device prints one line per frame: six values 0..1, comma separated, e.g.
    0.231,0.447,0.193,0.808,0.034,0.553
in the order flow, burst, tension, rhythm, drift, recovery.

This script opens that serial port, and for each line sends the same MIDI CCs
your Ableton set already learned from the simulator, so nothing in Ableton needs
re-mapping. It opens a virtual MIDI port called "Kinetic Echo" (the one you
already enabled in Ableton's MIDI settings).

Usage:
    python3 device_to_ableton.py                       # default port
    python3 device_to_ableton.py /dev/cu.usbmodem1101  # name the port
    python3 device_to_ableton.py --no-midi             # print only

Needs:  pip3 install pyserial python-rtmidi
"""

import sys
import time

QUALITIES = ("flow", "burst", "tension", "rhythm", "drift", "recovery")
CC = {"flow": 20, "burst": 21, "tension": 22, "rhythm": 23,
      "drift": 24, "recovery": 25, "intensity": 26}
BURST_NOTE = 60
BURST_ON, BURST_OFF = 0.60, 0.40
DEFAULT_PORT = "/dev/cu.usbmodem1101"
BAUD = 115200

_CC, _NOTE_ON, _NOTE_OFF = 0xB0, 0x90, 0x80


def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def intensity(v):
    raw = (0.20 * v[0] + 0.30 * v[1] + 0.25 * v[2]
           + 0.10 * v[3] + 0.05 * v[4] + 0.10 * (1.0 - v[5]))
    return clamp01(raw)


def parse(line):
    """Return a list of six floats, or None if the line is malformed."""
    parts = line.strip().split(",")
    if len(parts) != 6:
        return None
    try:
        return [clamp01(float(p)) for p in parts]
    except ValueError:
        return None


class Midi:
    def __init__(self, enable=True, name="Kinetic Echo", channel=0):
        self.ch = channel & 0x0F
        self.out = None
        self.last = {}
        self.burst_on = False
        if enable:
            try:
                import rtmidi
                self.out = rtmidi.MidiOut()
                self.out.open_virtual_port(name)
                print(f"[midi] virtual port open: '{name}'")
            except ImportError:
                print("[midi] python-rtmidi not installed; print-only.")
                print("[midi] pip3 install python-rtmidi")
            except Exception as e:
                print(f"[midi] could not open port ({e}); print-only.")

    def cc(self, num, value01):
        val = int(round(clamp01(value01) * 127))
        if self.last.get(num) == val:
            return
        self.last[num] = val
        if self.out:
            self.out.send_message([_CC | self.ch, num, val])

    def note(self, on):
        if not self.out:
            return
        status = (_NOTE_ON if on else _NOTE_OFF) | self.ch
        self.out.send_message([status, BURST_NOTE, 100 if on else 0])

    def send(self, v):
        for i, q in enumerate(QUALITIES):
            self.cc(CC[q], v[i])
        self.cc(CC["intensity"], intensity(v))
        if not self.burst_on and v[1] >= BURST_ON:
            self.burst_on = True
            self.note(True)
        elif self.burst_on and v[1] <= BURST_OFF:
            self.burst_on = False
            self.note(False)

    def close(self):
        if self.burst_on:
            self.note(False)
        if self.out:
            try:
                self.out.close_port()
            except Exception:
                pass


def bar(x, w=10):
    n = int(round(clamp01(x) * w))
    return "#" * n + "-" * (w - n)


def main():
    args = [a for a in sys.argv[1:]]
    enable = "--no-midi" not in args
    args = [a for a in args if a != "--no-midi"]
    port = args[0] if args else DEFAULT_PORT

    try:
        import serial
    except ImportError:
        print("Need pyserial:  pip3 install pyserial")
        return

    try:
        ser = serial.Serial(port, BAUD, timeout=1)
    except Exception as e:
        print(f"Could not open {port}: {e}")
        print("Check the port name (Arduino: Tools > Port) and that the")
        print("Serial Monitor is CLOSED, only one program can hold the port.")
        return

    midi = Midi(enable=enable)
    print(f"[serial] reading {port} at {BAUD}. Ctrl-C to stop.\n")
    time.sleep(0.3)
    ser.reset_input_buffer()

    try:
        while True:
            raw = ser.readline().decode("utf-8", "ignore")
            v = parse(raw)
            if v is None:
                continue
            midi.send(v)
            line = "  ".join(f"{q[:4]} {bar(v[i])}" for i, q in enumerate(QUALITIES))
            sys.stdout.write("\r" + line + "  ")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        midi.close()
        ser.close()
        print("\nstopped.")


if __name__ == "__main__":
    main()
