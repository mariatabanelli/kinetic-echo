# Kinetic Echo · web

Two browser pieces, one file each, Three.js from a CDN, nothing to install. Both take the six values live from the bridge over a WebSocket and fall back to a built-in simulator.

## index.html · World

A first-person field. Walk through a plane of glyph-points that moves the way the body moves: flow is the wind, drift turns it, tension raises the terrain, rhythm sends a wave out from where you stand, burst lifts everything near you for a moment, recovery flattens it.

Click to capture: a column of points rises where you aim, frozen with the six values at that instant, and keeps playing a tone on its own rhythm (pitch from flow, root from drift, filter from tension, decay from recovery, square wave on a burst). Every captured column is a step in a loop you build by moving. R releases them all.

Keys: WASD walk, Shift run, mouse look, click or C capture, R release, B invert, S sim/live, H hide the HUD, Esc frees the mouse.

## field.html · Field

The puck's display at wall size: a disc of 160,000 glyph-points in six wedges, denser at the centre, driven by the same rule as the firmware. C freezes the current field as a layer behind the live one (up to 8), R clears.

## Live from the device

    pip install -r ../bridge/requirements.txt
    python ../bridge/ke_osc_bridge.py --port /dev/cu.usbmodemXXXX --ws

Open the page in Chrome; the status changes from SIM to LIVE. `--sim --ws` runs without a device. The page also accepts `{"event":"capture"}` and `{"event":"release"}` on the socket for when the puck's buttons are routed through the bridge.

Built from a blank file: THREE.Points with custom ShaderMaterials, fbm noise in the vertex shader, Web Audio for the tones.
