"""Kinetic Echo headband mount for Nothing Headphone (1): one printed part.

A curved U-channel clips over the crown of the headband; a cradle on top holds the
Kinetic Echo puck (43.2 mm shell, 48.2 mm bezel lip) face up with three snap hooks.
The puck reads how the head moves and plays it back through the headphones.

Run: python make_mount_stl.py   (needs: pip install trimesh manifold3d numpy)
Edit the headband numbers from Nothing's drawings before printing.
"""
import numpy as np
import trimesh
from trimesh.creation import cylinder, box
from trimesh.transformations import rotation_matrix as rot

# ---------- headband: take these from Nothing's drawings (PLACEHOLDERS until then) ----------
band_w = 28.0   # width of the headband at the crown, across the head (mm)
band_t = 10.0   # thickness of the headband at the crown, top to underside (mm)
band_r = 95.0   # radius of the headband's top curve at the crown (mm); 0 = straight

# ---------- puck (from make_puck_stl.py) ----------
puck_d   = 43.2   # shell outer diameter
lip_d    = 48.2   # bezel lip outer diameter
lip_z0   = 1.6    # lip starts this far above the puck floor
lip_h    = 1.6    # lip height
usbc_angle = 0    # degrees, where the USB-C notch sits on the puck

# ---------- choose these ----------
wall      = 2.4
clearance = 0.4   # each side, headband channel
saddle_l  = 44.0  # length along the band
grip_lip  = 1.0   # inward lip under the band, each side (snap-over)
grip_gap  = 0.3   # vertical play for the band
cup_clear = 0.3   # radial clearance around the bezel lip
hook_n    = 3
hook_w    = 7.0
hook_t    = 1.4
hook_over = 0.8   # hook overhang over the lip's top edge
notch_w   = 11.0
SEG = 160


def cyl(d, h, z0=0.0, seg=SEG):
    c = cylinder(radius=d / 2, height=h, sections=seg)
    c.apply_translation([0, 0, z0 + h / 2])
    return c


def u_slice(dx):
    """One straight slice of the U-channel, dx long along X, open at the bottom.
    Band occupies y in [-band_w/2, band_w/2], z in [0, band_t]. Channel top at z = band_t + grip_gap + wall."""
    iw = band_w + 2 * clearance
    ih = band_t + grip_gap
    ow = iw + 2 * wall
    oh = ih + wall
    outer = box(extents=[dx, ow, oh]); outer.apply_translation([0, 0, oh / 2])
    inner = box(extents=[dx + 2, iw, ih + 1]); inner.apply_translation([0, 0, ih / 2 - 0.5])
    s = outer.difference(inner)
    # inward grip lips at the bottom edge of each arm, chamfered so the band pushes them open
    for sgn in (-1, 1):
        lip = box(extents=[dx, grip_lip + 0.01, 1.6])
        lip.apply_translation([0, sgn * (iw / 2 - grip_lip / 2), 0.8])
        s = s.union(lip)
    return s


def saddle():
    if band_r <= 0:
        return u_slice(saddle_l)
    n = 22
    half_ang = (saddle_l / 2) / band_r
    parts = []
    for i in range(n):
        a = -half_ang + (i + 0.5) * (2 * half_ang / n)
        dx = band_r * (2 * half_ang / n) * 1.08  # small overlap
        s = u_slice(dx)
        # rotate about the band's curvature centre (0, 0, -band_r) in the XZ plane
        s.apply_translation([0, 0, band_r])
        s.apply_transform(rot(a, [0, 1, 0]))
        s.apply_translation([0, 0, -band_r])
        parts.append(s)
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out


def cradle(z_base):
    """Cup for the puck: floor, wall around the bezel lip, three snap hooks, USB-C notch."""
    cup_id = lip_d + 2 * cup_clear
    cup_od = cup_id + 2 * wall
    floor_t = 2.0
    cup_h = floor_t + lip_z0 + lip_h            # rim level with the top of the lip
    c = cyl(cup_od, cup_h, z_base)
    c = c.difference(cyl(cup_id, cup_h, z_base + floor_t))
    # a window in the floor so the puck's underside and the headband breathe
    c = c.difference(cyl(puck_d - 8, floor_t + 2, z_base - 1))
    # hooks
    for k in range(hook_n):
        ang = 60 + k * (360 / hook_n)            # keep clear of the USB-C notch at 0 degrees
        h_h = lip_h + hook_over + 2.0
        post = box(extents=[hook_t, hook_w, h_h])
        post.apply_translation([cup_id / 2 + hook_t / 2 - 0.01, 0, z_base + floor_t + lip_z0 + h_h / 2])
        tip = box(extents=[cup_clear + hook_over + hook_t, hook_w, 1.2])
        tip.apply_translation([cup_id / 2 + hook_t / 2 - (cup_clear + hook_over) / 2 - 0.01, 0,
                               z_base + floor_t + lip_z0 + lip_h + 0.6 + 0.2])
        hk = post.union(tip)
        hk.apply_transform(rot(np.radians(ang), [0, 0, 1]))
        c = c.union(hk)
    # USB-C notch through the cup wall
    nt = box(extents=[wall + 4, notch_w, cup_h + 2])
    nt.apply_translation([cup_od / 2 - wall / 2, 0, z_base + floor_t + (cup_h + 2) / 2])
    nt.apply_transform(rot(np.radians(usbc_angle), [0, 0, 1]))
    c = c.difference(nt)
    return c


sad = saddle()
top_z = sad.bounds[1][2]
cr = cradle(top_z - 0.6)                        # sink the cup 0.6 mm into the saddle top so they fuse
# a neck plate between saddle and cup so the cup is supported across its width
neck = box(extents=[saddle_l * 0.9, band_w + 2 * clearance + 2 * wall, 2.0])
neck.apply_translation([0, 0, top_z - 0.6 + 1.0])
part = sad.union(neck).union(cr)
part.apply_translation([0, 0, -part.bounds[0][2]])
part.export("echo_headband_mount.stl")
print(f"mount: {part.extents.round(1)} mm, watertight={part.is_watertight}")
