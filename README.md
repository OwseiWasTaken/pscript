<h1>i have never dene a README before</h1>

<p>
the main ideia of pscript is to the middle man (you probably) make a python program that pscript can read
than the user will make a ps script that will be read by the pscript interpreter and will be executed
by your python program
e.g
pscript.py reads psmidlle-git.py, then reads program.ps, then executes program.ps with psmidlle-git definitions

main ps line defs
label "#name"
label stop "##"
func exec "func vars"
jump "@label" will jump to that label and execute it
conditional "!boolean" if true will execute the next line

you may NOT nest labels
making a conditional jump to a label is recomended

only the main label will be executed normally

</p>
