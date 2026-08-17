● Worth pushing on — you're right that it's not settled, and the repo has been assuming it.

  Both exist for 20x20. The 20-series comes as I-type with a 5 mm groove and as B-type with a 6 mm groove (franzek, myaluprofil 
  20x20 Nut 5 I-Typ, tecwalker Aluprofil 6 20x20 Typ B) — a 20 mm profile is too small for anything above Nut 6. So the profile has
  to be established, not inferred from the size.

  The M4 doesn't decide it. I'd expected M4 to point at Nut 5, but M4 Nutensteine are a standard product for Nut 6 as well — the
  Typ B 20x20 page lists M3, M4 and M5 slot nuts, and there are M4 hammer nuts sold specifically for "Aluprofil 20-er" Nut 6
  (montageprofile24, s-polytec). So the manual's Screw DIN 912 M4x10 + Nut f. Extrusion 2020 is consistent with either.

  The build page doesn't say. I re-read it: step 1 lists "32 Screw DIN 912 M4x10" and "32 Nut f. Extrusion 2020", one nut per bolt
  and no slot width anywhere. (That 1:1 pairing is a good independent confirmation of how the detector counts.)

  Where the repo's 6 mm came from. stock/2020-extrusion.py sets slot_mouth = 6.0 and justifies the section only through its area:
  "A real 20 x 20 slot 6 profile is catalogued at 0.53 kg/m, which at 2.70 g/cm³ is 196 mm²". That is one catalogue figure picked
  to match a section that had already been drawn, not a measurement of your machine — and it doesn't match either profile I just
  looked up:

  ┌─────────────────────┬───────┬───────────┐
  │                     │ kg/m  │ ⇒ section │
  ├─────────────────────┼───────┼───────────┤
  │ repo's assumption   │ 0.53  │ 196 mm²   │
  ├─────────────────────┼───────┼───────────┤
  │ 20x20 Nut 5, I-type │ 0.485 │ 180 mm²   │
  ├─────────────────────┼───────┼───────────┤
  │ 20x20 Nut 6, Typ B  │ 0.439 │ 163 mm²   │
  └─────────────────────┴───────┴───────────┘

  0.53 is the heavy-walled generic 2020 sold for printers. So the "sharp check" in that script can't arbitrate this — it only
  checks the section against itself. No printed part helps either: I looked for a feature that engages the slot, and there is none.
  BOT_BRACKETS is a flat plate with five clearance holes; every part bolts on through the face.

  One caliper reading settles it — the slot mouth on the machine, 5.0 or 6.0. Weighing a stick is weaker: 300 mm is 146 g vs 159 g
  vs 132 g across those three.

  What changes if it is Nut 5

  Not the detection. The 118 nuts, which stick and slot each is in, and where along it, all stand: the mouth width only enters as a
  ±1.5 mm slack test, and the nut's depth comes from the wall thickness over the channel, not from the mouth. What changes is the
  nut you order (a Nut-5 M4 hammer nut is ~4.7 mm across the mouth instead of ~5.8) and three constants in 2020-extrusion.py —
  slot_mouth, slot_channel, and section_area, which would need the right catalogue weight rather than the current 0.53.

  Two of the findings get sharper, and one is worth flagging regardless of which profile it is:

  - The four TOP_RAIL_HOLDER bolts sitting 1.15 mm off the slot centre line don't fit through the mouth either way: an M4 shank
  needs 3.15 mm of half-width there, against 3.0 for a 6 mm slot and 2.5 for a 5 mm one. The twelve at 0.50 mm clear a 6 mm mouth
  with 0.5 mm to spare, and are hard against both walls in a 5 mm one.
  - The ten bolts reaching 4.5 mm past the channel floor get worse in a Nut-5 channel, which is shallower.

  So: I'd hold off building the nut part until you've measured the slot. Everything upstream of the nut's own size is unaffected,
  and I can re-parameterise the section script so the slot is a single constant rather than three.

✻ Cogitated for 3m 28s

※ recap: Goal: model the missing slot nuts in the scripted assembly and get them into the BOM. Detection works — 118 found and
  verified, tool and data written. Next: measure the profile's slot mouth, 5 or 6 mm, before building the nut part. (disable recaps
  in /config)