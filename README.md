<h1>i have never done a README before</h1>

<p>
the main ideia of pscript is to the middle man (you probably) make a python class that pscript can read
than the user will make a .ps file that will be read by the pscript interpreter and will be executed
by your python class
e.g
pscript.py reads psmidlle-git.py, then reads program.ps, then executes program.ps with psmidlle-git definitions

main ps line defs
label "#name"
label stop "##"
every other line mush be handled by psmidlle

you may NOT nest labels
only the main label will be executed normally

stdpsmiddle is included in main.py

everything but jumps shall be executed by psmiddle

</p>
