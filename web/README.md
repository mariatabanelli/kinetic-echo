# Kinetic Echo · web

Two browser pieces, one file each, Three.js from a CDN, nothing to install. Both take the six values live from the bridge over a WebSocket and fall back to a built-in simulator.

## index.html · World

A first-person world grown from a seed: a plane of glyph-points, a sky, fireflies, and 103 forms of five kinds placed across 150 metres. At the centre stands the beacon, your live signature: tall with burst, wide with tension, twisting with flow, spinning with drift, ringed by rhythm, settling with recovery.

The ground moves the way the body moves: flow is the wind, drift turns it, tension raises the terrain, rhythm sends a wave out from where you stand, burst lifts everything near you for a moment.

Aim at a form and click: it wakes with the six values of that instant, lights the ground around it, and joins a 16-step loop at 84 BPM. Its rhythm value decides how often it plays (every 2, 4, 8 or 16 steps). Each kind has its own voice:

| form | shape | voice |
|---|---|---|
| reed | tall stalk, leans in the wind, rings travel up it | pluck (pitch from flow, brightness from tension, decay from recovery) |
| stone | low mound, breathes on the beat | thud (pitch drop set by burst) plus a click |
| ring | flat on the ground, a spot runs round it | tick (noise, highpass by tension) |
| arc | standing half-ring you walk under, light pours along it | hum (two detuned saws, held, filter by tension) |
| thread | wavy line in the air, tightens with tension | bell (FM, ratio from drift, long decay from recovery) |

Click an awake form to put it back to sleep. R sleeps everything. Drift chooses the root note for the whole world, so the key moves as you drift.

Keys: WASD walk, Shift run, mouse look, click or C wake/sleep, R sleep all, B palette (ash, moss, ember, paper), S sim/live, H hide the HUD, Esc frees the mouse.

## field.html · Field

The puck's display at wall size: a disc of 160,000 glyph-points in six wedges, denser at the centre, driven by the same rule as the firmware. C freezes the current field as a layer behind the live one (up to 8), R clears.

## Live from the device

    pip install -r ../bridge/requirements.txt
    python ../bridge/ke_osc_bridge.py --port /dev/cu.usbmodemXXXX --ws

Open the page in Chrome; the status changes from SIM to LIVE. `--sim --ws` runs without a device. The page also accepts `{"event":"capture"}` and `{"event":"release"}` on the socket for when the puck's buttons are routed through the bridge.

Built from a blank file: THREE.Points with custom ShaderMaterials, fbm noise in the vertex shader, Web Audio for the tones.
