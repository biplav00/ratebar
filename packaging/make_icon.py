"""Render the ratebar app icon master PNG (1024x1024): a ring gauge on a
gradient squircle, matching the menu-bar ring motif. Output: argv[1] (default
/tmp/ratebar_icon.png). The .icns is assembled from this by make_icon.sh."""
import sys
import math

from AppKit import (
    NSApplication, NSImage, NSBitmapImageRep, NSColor, NSGradient,
    NSBezierPath, NSMakeRect, NSMakePoint, NSShadow, NSMakeSize,
    NSGraphicsContext, NSLineCapStyleRound,
)

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ratebar_icon.png"
S = 1024.0

NSApplication.sharedApplication()
img = NSImage.alloc().initWithSize_((S, S))
img.lockFocus()
ctx = NSGraphicsContext.currentContext()
ctx.setShouldAntialias_(True)

# --- squircle background with a slate->indigo gradient ---
inset = 0.0
radius = 0.2237 * S
squircle = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
    NSMakeRect(inset, inset, S - 2 * inset, S - 2 * inset), radius, radius)
ctx.saveGraphicsState()
squircle.addClip()
NSGradient.alloc().initWithStartingColor_endingColor_(
    NSColor.colorWithRed_green_blue_alpha_(0.16, 0.23, 0.36, 1.0),   # top slate-blue
    NSColor.colorWithRed_green_blue_alpha_(0.05, 0.08, 0.16, 1.0),   # bottom near-black
).drawInRect_angle_(NSMakeRect(0, 0, S, S), -90)
# subtle top sheen
NSGradient.alloc().initWithStartingColor_endingColor_(
    NSColor.colorWithWhite_alpha_(1.0, 0.10),
    NSColor.colorWithWhite_alpha_(1.0, 0.0),
).drawInRect_angle_(NSMakeRect(0, S * 0.55, S, S * 0.45), -90)
ctx.restoreGraphicsState()

# --- ring gauge ---
cx = cy = S / 2.0
ring_r = S * 0.31
line = S * 0.12

# faint full track
NSColor.colorWithWhite_alpha_(1.0, 0.14).set()
track = NSBezierPath.bezierPath()
track.setLineWidth_(line)
track.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
    NSMakePoint(cx, cy), ring_r, 0, 360)
track.stroke()

# accent arc (~72%), green, round caps, soft glow
ctx.saveGraphicsState()
glow = NSShadow.alloc().init()
glow.setShadowColor_(NSColor.colorWithRed_green_blue_alpha_(0.20, 0.85, 0.45, 0.55))
glow.setShadowBlurRadius_(36)
glow.setShadowOffset_(NSMakeSize(0, 0))
glow.set()
sweep = 0.72 * 360.0
arc = NSBezierPath.bezierPath()
arc.setLineWidth_(line)
arc.setLineCapStyle_(NSLineCapStyleRound)
NSColor.colorWithRed_green_blue_alpha_(0.24, 0.86, 0.46, 1.0).set()
arc.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
    NSMakePoint(cx, cy), ring_r, 90.0, 90.0 - sweep, True)
arc.stroke()
ctx.restoreGraphicsState()

img.unlockFocus()

tiff = img.TIFFRepresentation()
rep = NSBitmapImageRep.imageRepWithData_(tiff)
png = rep.representationUsingType_properties_(4, None)  # 4 = PNG
png.writeToFile_atomically_(OUT, True)
print("wrote", OUT)
