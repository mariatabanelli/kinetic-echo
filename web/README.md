# Kinetic Echo · Field (web)

A browser visual for Kinetic Echo. One file, `index.html`, Three.js from a CDN, nothing to install.

- 160,000 glyph-points on a disc divided into six wedges, one per quality, denser at the centre, thinning to the rim, the same rule the puck uses.
- flow moves the field, burst pops and flashes it, tension jitters it, rhythm pulses it, drift turns it, recovery settles it.
- **C** captures the current field as a frozen layer that stays behind the live one (up to 8). **R** releases all layers.
- **B** inverts (black on white, or white on black for a wall). **S** toggles the built-in simulator. **F** fullscreen. **H** hides the HUD.

## Live from the device

    pip install -r ../bridge/requirements.txt
    python ../bridge/ke_osc_bridge.py --port /dev/cu.usbmodemXXXX --ws

Then open `index.html` in Chrome. The status in the corner changes from SIM to LIVE. Without a device, `--sim --ws` sends simulated movement.

The page also accepts `{"event":"capture"}` and `{"event":"release"}` over the same socket, for when the puck's buttons are wired through the bridge.
