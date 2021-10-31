#! /bin/python3.9
# lang/pscript/main.py
from util import *

class LINE:
	def __init__(this, num, tp, cont):
		this.LineNum =	num
		this.LineType = tp
		this.LineCont = cont

	def __repr__(this):
		return f"{this.LineNum} : {this.LineType}({this.LineCont})"
	def __str__(this):
		t = this.LineCont
		if this.LineType == "var":t = "def "+t
		if this.LineType == "label":t += "{"
		if this.LineType == "label stop":t += "}"
		if this.LineType == "conditional":t = "if "+t+':'
		if this.LineType == "jump":t += "()"
		return f"{t}"

errors = {
	1 : "missing file name as $1",
	2 : "file {s} does not exits",
}

def panic(errnum, *extra):
	errmsg = errors[errnum]
	if extra:
		errmsg = sprintf(errmsg, *extra, HideErrors = False)
	eprint(errmsg)
	#exit(errnum)

def ListIntoLINE(lst: list[str]) -> list[LINE]:
	ret = []
	for i in r(lst):
		ln = lst[i]
		tp = None
		cont = []
		if ln == "##":
			tp = "label stop"
			cont = ""
		elif ln[0] == '#':
			tp = "label"
			cont = ln[1:]
		elif ln[0] == '@':
			tp = "conditional"
			cont = ln[1:]
		elif ln[0] == '!':
			tp = "jump"
			cont = ln[1:]
		else:
			tp = "func"
			cont = ln
		cont = MakeString(cont)
		ret.append(LINE(i, tp, cont))
	if ret[-1].LineType != "label stop":
		ret.append(LINE(i+1, "label stop", ""))
	return ret

def ReadFile(filename):
	if exists(filename):
		with open(filename, 'r') as f:
			return ListIntoLINE(list(map(lambda x: x.strip(), f.readlines())))
	else:
		panic(2, filename)

def PrintFile(LINEfile: list[LINE]):
	inlabel = 0
	for ln in LINEfile:
		if ln.LineType == "label stop":
			inlabel -= 1
		print("    " * inlabel + str(ln))
		if ln.LineType == "label":
			inlabel += 1

def execute(psmidlle, lines):
	vars = {}
	for line in lines:
		if line.LineType == "func":
			psmidlle(line, vars)

class program:
	def get(this, name):
		if name in this.vars.keys():
			return this.vars[name]
		elif all([n in "+-0987654321" for n in name]):
			return eval(name)
		elif name[0] == '"' and name[-1] == '"':
				return name[1:-1].replace("\\\"", '"').replace("\\n", '\n')

	def panic(this, line):
		printl(COLOR.red+'[')
		printl(COLOR.orange+"ERROR")
		printl(COLOR.red+']'+COLOR.nc)
		print(repr(this.line))

	def exit (this, line):exit(this.get(line[0]))

	def write(this, line):
		for l in line:
			sout.write(this.get(l))

	def flush(this, line):sout.flush()

	def set(this, line):this.vars[line[0]] = this.get(line[1])

	def debug(this, line):
		print("DEBUG{")
		printl("	")
		print([this.get(l) for l in line])
		printl("	")
		print(this.vars)
		printl("	")
		print(repr(this.line))
		print("}DEBUG")

	def __call__(this, line, vars):
		this.vars = vars
		this.line = line
		{
			" panic":this.panic,
			"exit"	:this.exit,
			"write" :this.write,
			"flush" :this.flush,
			"set"	:this.set,
			"debug" :this.debug,
		}.get(line.LineCont[0],
		this.panic)(line.LineCont[1:])
		return this.vars

execute(program(), ReadFile("examples/test.ps"))

#TODO START
#	meta implement:
#		conditional
#		jumping
#	middle implement:
#		math
#		input
#TODO END
