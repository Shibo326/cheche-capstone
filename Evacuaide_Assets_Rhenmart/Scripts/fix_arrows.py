"""One-off fix: give evac floor arrows real thickness.

The 53 Mat_Arrow route markers were authored with d[2] == 0.0 (a degenerate,
zero-volume box). make_box scales the cube by dims/2, so scale.z = 0 collapses
the mesh to a plane -> flickering / broken shards in the viewport and in Unity.

Fix: set d[2] to a small real thickness so each arrow is a valid thin floor
decal. Center is nudged up by half the thickness so the arrow rests ON the
floor surface instead of sinking half-in.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "building_layout.json")
BACKUP = JSON_PATH + ".bak"
THICK = 0.03  # 3 cm thick decal slab

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# backup once
if not os.path.exists(BACKUP):
    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(data, f)

fixed = 0
for rec in data["objects"]:
    if rec.get("m") == "Mat_Arrow" and float(rec["d"][2]) == 0.0:
        rec["d"][2] = THICK
        # lift center up by half thickness so the slab sits on the floor
        rec["c"][2] = round(float(rec["c"][2]) + THICK / 2.0, 4)
        fixed += 1

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f)

print(f"Fixed {fixed} arrow objects (d[2] -> {THICK}).")
remaining = [o["n"] for o in data["objects"]
             if float(o["d"][0]) == 0 or float(o["d"][1]) == 0 or float(o["d"][2]) == 0]
print(f"Objects with any zero dimension remaining: {len(remaining)}")
if remaining:
    print(remaining[:10])
