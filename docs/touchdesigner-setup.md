# TouchDesigner: driving the visual from Kinetic Echo

Goal: replace the sample-data CHOP in the existing network with six live channels from the device.

## 1. Start the bridge

Without the device (tonight):

    pip install python-osc pyserial
    python bridge/ke_osc_bridge.py --sim --print

With the device:

    python bridge/ke_osc_bridge.py --port /dev/cu.usbmodemXXXX --print

It sends `/ke/flow`, `/ke/burst`, `/ke/tension`, `/ke/rhythm`, `/ke/drift`, `/ke/recovery` to `127.0.0.1:7000`.

## 2. Receive in TouchDesigner

1. Add an **OSC In CHOP**. Set Network Port to `7000`. Leave Network Address empty (local).
2. The CHOP shows six channels named `ke/flow` ... `ke/recovery` as soon as the bridge runs.
3. Add a **Rename CHOP** after it: From `ke/*`, To `*`. Channels become `flow`, `burst`, `tension`, `rhythm`, `drift`, `recovery`.
4. Add a **Lag CHOP** (lag 0.05 to 0.15 s) to smooth jitter. Burst can stay unsmoothed: use a **Select CHOP** to split it out if needed.
5. Find the CHOP that currently feeds your visual with sample data (a Noise, Pattern, or Constant CHOP). Wire the Lag CHOP into the same place and delete the sample one.

## 3. Mapping that reads well on a party wall

| Channel | Drive | Why |
|---|---|---|
| flow | speed or smoothness of a particle field | smooth movement reads as smooth motion |
| burst | a flash, a scale pop, a new emission | one-to-one with the burst note in Ableton |
| tension | noise amplitude or line thickness | held effort looks tight |
| rhythm | a pulse rate, feedback amount | repetition becomes a beat |
| drift | hue rotation or slow camera drift | slow change, slow colour |
| recovery | fade to rest, trail length | the image settles as the body does |

Keep the six-wedge character field as one layer so the wall matches the puck.

## 4. Record a clip tonight

Run `--sim`, record 60 seconds with the TouchDesigner Movie File Out TOP. Caption it "sample data" on the website until the live clip replaces it.
