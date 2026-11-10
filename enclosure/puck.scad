// Kinetic Echo puck enclosure, parametric
// Units: mm. Measure your own stack and change the numbers at the top.
// Print: PLA or PETG, 0.2 mm layers, shell and lid printed face down, no supports.

// ---------- measure these ----------
display_pcb_d   = 36.0;   // diameter of the round GC9A01 module PCB (measure)
display_active_d= 32.4;   // visible glass diameter
display_glass_h = 2.0;    // glass + cover height above the PCB
display_pcb_t   = 1.6;    // PCB thickness
stack_below     = 9.0;    // everything under the display: perfboard + Zero + IMU + battery (measure tallest path)
battery_l       = 30.0;   // LiPo footprint (only used for a check print)
battery_w       = 20.0;
battery_t       = 5.0;

// ---------- choose these ----------
wall            = 2.0;
clearance       = 0.6;    // radial gap around the display PCB
floor_t         = 1.6;
lid_lip         = 1.5;    // lid rim height that sits inside the shell
button_d        = 4.2;    // hole for 4 mm tactile caps, 3 at the rim
button_angles   = [150, 180, 210];
usbc_w          = 9.2;    // USB-C opening on the side
usbc_h          = 3.4;
switch_w        = 7.0;    // slide switch slot
switch_h        = 3.0;
bezel_lip       = 2.5;    // outward flange that the sewn bezel grips

// ---------- derived ----------
inner_d  = display_pcb_d + 2*clearance;
outer_d  = inner_d + 2*wall;
inner_h  = stack_below + display_pcb_t + display_glass_h;
outer_h  = inner_h + floor_t;

$fn = 160;

module shell() {
    difference() {
        union() {
            cylinder(d = outer_d, h = outer_h);
            // bezel flange near the bottom, for the sleeve ring to grip
            translate([0,0,floor_t]) cylinder(d = outer_d + 2*bezel_lip, h = 1.6);
        }
        // cavity
        translate([0,0,floor_t]) cylinder(d = inner_d, h = inner_h + 1);
        // USB-C opening, at angle 0
        translate([outer_d/2 - wall - 1, -usbc_w/2, floor_t + 1.5])
            cube([wall + 2, usbc_w, usbc_h]);
        // slide switch slot, at angle 90
        rotate([0,0,90])
            translate([outer_d/2 - wall - 1, -switch_w/2, floor_t + 1.5])
                cube([wall + 2, switch_w, switch_h]);
        // three buttons through the wall near the top
        for (a = button_angles)
            rotate([0,0,a])
                translate([outer_d/2 - wall - 1, 0, outer_h - 4])
                    rotate([0,90,0]) cylinder(d = button_d, h = wall + 2);
        // ventilation / cable slot for the sleeve bezel stitching
        for (a = [45, 135, 225, 315])
            rotate([0,0,a])
                translate([outer_d/2 + bezel_lip/2, 0, floor_t - 0.1])
                    cylinder(d = 1.6, h = 2.0);
    }
}

module lid() {
    difference() {
        union() {
            cylinder(d = outer_d, h = wall);
            translate([0,0,-lid_lip]) cylinder(d = inner_d - 0.4, h = lid_lip);
        }
        // display window
        translate([0,0,-lid_lip - 1]) cylinder(d = display_active_d + 0.8, h = lid_lip + wall + 2);
    }
}

// a block the size of the battery, to check it fits before you print the shell
module battery_check() {
    cube([battery_l, battery_w, battery_t]);
}

// ---------- layout ----------
shell();
translate([outer_d + 10, 0, wall]) rotate([180,0,0]) lid();
// translate([0, outer_d + 10, 0]) battery_check();

echo(str("outer diameter ", outer_d, " mm, outer height ", outer_h, " mm"));
