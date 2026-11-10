"""Generate puck_shell.stl and puck_lid.stl from the same parameters as puck.scad.
Run: python make_puck_stl.py   (needs: pip install trimesh manifold3d numpy)
Edit the numbers at the top to match your measured stack.
"""
import numpy as np
import trimesh
from trimesh.creation import cylinder, box

# ---------- measure these ----------
display_pcb_d    = 38.0   # common 7-pin round module: 36 to 38 mm circle; measure yours
display_active_d = 32.4
display_glass_h  = 2.0
display_pcb_t    = 1.6
stack_below      = 12.0   # Zero (3.2) + perfboard (1.6) + LiPo 503035 (5.0) + wiring margin

# ---------- choose these ----------
wall        = 2.0
clearance   = 0.6
floor_t     = 1.6
lid_lip     = 1.5
button_d    = 4.2
button_angles = [150, 180, 210]
usbc_w, usbc_h     = 9.2, 3.4
switch_w, switch_h = 7.0, 3.0
bezel_lip   = 2.5
tab_w, tab_l, tab_h = 12.5, 9.0, 3.6   # pocket for the display PCB header tab, at 270 degrees
SEG = 160

inner_d = display_pcb_d + 2 * clearance
outer_d = inner_d + 2 * wall
inner_h = stack_below + display_pcb_t + display_glass_h
outer_h = inner_h + floor_t


def cyl(d, h, z0=0.0):
    c = cylinder(radius=d / 2, height=h, sections=SEG)
    c.apply_translation([0, 0, z0 + h / 2])
    return c


def side_cut(w, h, z0, angle_deg, depth=wall + 2):
    """A box through the wall, centred on angle_deg, bottom at z0."""
    b = box(extents=[depth, w, h])
    b.apply_translation([outer_d / 2 - wall - 1 + depth / 2, 0, z0 + h / 2])
    b.apply_transform(trimesh.transformations.rotation_matrix(np.radians(angle_deg), [0, 0, 1]))
    return b


def button_hole(angle_deg):
    c = cylinder(radius=button_d / 2, height=wall + 2, sections=48)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.radians(90), [0, 1, 0]))
    c.apply_translation([outer_d / 2 - wall / 2, 0, outer_h - 4])
    c.apply_transform(trimesh.transformations.rotation_matrix(np.radians(angle_deg), [0, 0, 1]))
    return c


# shell
shell = cyl(outer_d, outer_h).union(cyl(outer_d + 2 * bezel_lip, 1.6, floor_t))
shell = shell.difference(cyl(inner_d, inner_h + 1, floor_t))
shell = shell.difference(side_cut(usbc_w, usbc_h, floor_t + 1.5, 0))
shell = shell.difference(side_cut(switch_w, switch_h, floor_t + 1.5, 90))
# pocket in the wall for the display header tab (sits in the display PCB plane)
shell = shell.difference(side_cut(tab_w, tab_h, floor_t + stack_below - 1.0, 270, depth=tab_l))
for a in button_angles:
    shell = shell.difference(button_hole(a))
for a in [45, 135, 225, 315]:
    p = cylinder(radius=0.8, height=2.0, sections=24)
    p.apply_translation([outer_d / 2 + bezel_lip / 2, 0, floor_t - 0.1 + 1.0])
    p.apply_transform(trimesh.transformations.rotation_matrix(np.radians(a), [0, 0, 1]))
    shell = shell.difference(p)

# lid (printed face down: window side on the bed)
lid = cyl(outer_d, wall).union(cyl(inner_d - 0.4, lid_lip, -lid_lip))
lid = lid.difference(cyl(display_active_d + 0.8, lid_lip + wall + 2, -lid_lip - 1))
lid.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
lid.apply_translation([0, 0, -lid.bounds[0][2]])

shell.export("puck_shell.stl")
lid.export("puck_lid.stl")
print(f"shell: outer {outer_d:.1f} mm, height {outer_h:.1f} mm, watertight={shell.is_watertight}")
print(f"lid: watertight={lid.is_watertight}")
