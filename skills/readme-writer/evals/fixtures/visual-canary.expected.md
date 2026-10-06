<!-- origin: shimo4228 -->
# Expected findings — visual-canary.md

Visual smoke-test fixture for `readme-judge` Phase V. A made-up profile README built to
break three §V checks while its prose stays plain. Render it with
`readme_render.py --surface profile` and pass the render directory; the judge is NOT
shown this file. Pass = at least 2 of 3 detected, in any wording.

1. **The entry sits below the first screen (V1).** Three stacked alerts and three long
   paragraphs come before `## Where to go`; on desktop the first screen ends before that
   heading, so a visitor sees no place to go next. (render.json: the H2's `top` is past
   `first_screen_height`)
2. **Three alerts and three emphasis levels compete at the top (V6 / V2).** GitHub Docs
   advises one or two alerts per document; here NOTE, IMPORTANT and TIP stack above the
   identity paragraph and outweigh it in the squint tiles. (layout.alerts.count = 3)
3. **The Configuration table overflows on a phone (V4).** Its example cell is one long
   unbreakable command, so on the 293 px mobile column the table scrolls sideways and
   the load-bearing example is cut. (render.json: mobile `overflow` lists the table)
