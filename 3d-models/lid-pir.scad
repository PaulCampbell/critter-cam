


$fn=180;

difference() {
cube([118.2,4,38.2]);

translate([2,2,2])
    cube([114.2,4,34.2]);
    
    translate([88,7,19])
    rotate([90,0,0])
        cylinder(10,d=14);
    
     translate([35,-1,7])
      cube([24,24,24]);
}

