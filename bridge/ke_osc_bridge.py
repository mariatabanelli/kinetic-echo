#!/usr/bin/env python3
"""Kinetic Echo -> OSC bridge for TouchDesigner (and anything else that speaks OSC).

Reads the device's CSV lines over USB serial (six values 0..1:
flow, burst, tension, rhythm, drift, recovery) and sends them as OSC.

Usage:
    python ke_osc_bridge.py --port /dev/cu.usbmodem1101        # live device
    python ke_osc_bridge.py --sim                               # no device: fake movement
    python ke_osc_bridge.py --sim --host 127.0.0.1 --osc-port 7000

OSC messages sent at the device rate (or 50 Hz in --sim):
    /ke/flow      float
    /ke/burst     float
    /ke/tension   float
    /ke/rhythm    float
    /ke/drift     float
    /ke/recovery  float
    /ke/all       six floats in one message

--ws also serves the values as JSON over a WebSocket (ws://127.0.0.1:8765)
for web/index.html.

Needs:  pip install pyserial python-osc websockets
"""
import json
import threading
import argparse
import math
import random
import sys
import time

from pythonosc.udp_client import SimpleUDPClient

QUALITIES = ["flow", "burst", "tension", "rhythm", "drift", "recovery"]


def parse_line(line: str):
    parts = line.strip().split(",")
    if len(parts) < 6:
        return None
    try:
        vals = [min(1.0, max(0.0, float(p))) for p in parts[:6]]
    except ValueError:
        return None
    return vals


def simulate():
    """Slow, plausible fake movement so a TouchDesigner network can be built without the device."""
    t0 = time.time()
    burst_until = 0.0
    while True:
        t = time.time() - t0
        flow = 0.5 + 0.4 * math.sin(t * 0.7)
        if random.random() < 0.01:
            burst_until = t + 0.4
        burst = 1.0 if t < burst_until else max(0.0, 0.2 * math.sin(t * 5))
        tension = 0.3 + 0.3 * math.sin(t * 1.9 + 1)
        rhythm = 0.5 + 0.5 * math.sin(t * 2.4)
        drift = (t * 0.03) % 1.0
        recovery = max(0.0, 1.0 - (t - burst_until) * 0.8) if t >= burst_until else 0.0
        yield [flow, burst, tension, rhythm, drift, recovery]
        time.sleep(0.02)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", help="serial port, e.g. /dev/cu.usbmodem1101")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--osc-port", type=int, default=7000)
    ap.add_argument("--sim", action="store_true", help="send simulated values, no device needed")
    ap.add_argument("--print", action="store_true", help="echo values to the terminal")
    ap.add_argument("--ws", action="store_true", help="also serve JSON over WebSocket for web/index.html")
    ap.add_argument("--ws-port", type=int, default=8765)
    args = ap.parse_args()

    client = SimpleUDPClient(args.host, args.osc_port)
    print(f"OSC -> {args.host}:{args.osc_port}  addresses /ke/<quality> and /ke/all")

    clients = set()
    lock = threading.Lock()
    if args.ws:
        from websockets.sync.server import serve

        def handler(conn):
            with lock:
                clients.add(conn)
            try:
                for _ in conn:   # keep open; the browser sends nothing
                    pass
            finally:
                with lock:
                    clients.discard(conn)

        def run_ws():
            with serve(handler, "127.0.0.1", args.ws_port) as server:
                server.serve_forever()

        threading.Thread(target=run_ws, daemon=True).start()
        print(f"WS  -> ws://127.0.0.1:{args.ws_port}  JSON {{flow,...,recovery}}")

    def broadcast(vals):
        if not clients:
            return
        msg = json.dumps({n: round(float(x), 4) for n, x in zip(QUALITIES, vals)})
        with lock:
            dead = []
            for c in clients:
                try:
                    c.send(msg)
                except Exception:
                    dead.append(c)
            for c in dead:
                clients.discard(c)

    if args.sim:
        source = simulate()
    else:
        if not args.port:
            sys.exit("give --port or use --sim")
        import serial  # pyserial
        ser = serial.Serial(args.port, args.baud, timeout=1)
        print(f"serial <- {args.port} @ {args.baud}")

        def from_serial():
            while True:
                raw = ser.readline().decode("utf-8", errors="ignore")
                vals = parse_line(raw)
                if vals:
                    yield vals

        source = from_serial()

    try:
        for vals in source:
            for name, v in zip(QUALITIES, vals):
                client.send_message(f"/ke/{name}", float(v))
            client.send_message("/ke/all", [float(v) for v in vals])
            if args.ws:
                broadcast(vals)
            if args.print:
                print("  ".join(f"{n} {v:.2f}" for n, v in zip(QUALITIES, vals)), end="\r")
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
