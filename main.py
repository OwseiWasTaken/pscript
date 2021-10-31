#! /bin/python3.9
# lang/pscript/main.py
from util import *

class LINE:
	def __init__(this, num, tp, cont):
		this.LineNum =	num
		this.LineType = tp
		this.LineCont = cont

	def __repr__(this):
		return f"{this.LineNum+1} : {this.LineType}({this.LineCont})"
	def __str__(this):
		t = this.LineCont
		if this.LineType == "var":t = "def "+t
		if this.LineType == "label":t += "{"
		if this.LineType == "label stop":t += "}"
		if this.LineType == "conditional":t = "if "+' && '.join(t)+':'
		if this.LineType == "jump":t += "()"
		return f"{t}"

errors = {
	1 : "missing file name as $1",
	2 : "file {s} does not exits",
	127 : "file {s} does not exits",
	128 : "can't close system out stream",
	129 : "no such command",
	130 : "no such var \"{s}\"",
}

def panic(errnum, *extra):
	extra = list(extra)
	if errnum > 126:
		printl(COLOR.red+'[')
		printl(COLOR.orange+"RUNTIME ERROR")
		print(COLOR.red+']'+COLOR.nc)
		line = extra.pop(-1)
		print(repr(line))
	else:
		printl(COLOR.red+'[')
		printl(COLOR.orange+"ERROR")
		print(COLOR.red+']'+COLOR.nc)

	errmsg = errors[errnum]
	if extra:
		errmsg = sprintf(errmsg, *extra, HideErrors = False)
	eprint(errmsg)
	exit(errnum)

def ListIntoLINE(lst: list[str]) -> list[LINE]:
	ret = []
	for i in r(lst):
		ln = lst[i]
		tp = None
		cont = ""
		if ln:
			if ln == "##":
				tp = "label stop"
			elif ln[0] == '#':
				tp = "label"
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
	if filename:
		if exists(filename):
			with open(filename, 'r') as f:
				return ListIntoLINE(list(map(lambda x: x.strip(), f.readlines())))
		else:
			panic(2, filename)
	else:
		panic(1)

def PrintFile(LINEfile: list[LINE]):
	inlabel = 0
	for ln in LINEfile:
		if ln.LineType == "label stop":
			inlabel -= 1
		print("    " * inlabel + str(ln))
		if ln.LineType == "label":
			inlabel += 1

def WrapLines(lines : list[LINE]) -> dict[str:list[LINE]]:
	lbl = ""
	ret = {}
	for line in lines:
		if line.LineType == "label" and not lbl:
			lbl = line.LineCont[0]
			ret[lbl] = []
		elif line.LineType == "label stop":
			lbl = ""
		else:
			ret[lbl].append(line)
	return ret

def ExecuteWrap(psmidlle, name, program):
	execnext = None
	prog = program[name]
	for i in r(prog):
		line = prog[i]
		#if line.LineType == "conditional reset":
		#	execnext = None
		#elif line.LineCond != None:
		#	if line.LineCond != execnext:
		#		continue
		if line.LineType == "func":
			psmidlle(line)
		elif line.LineType == "jump":
			ExecuteWrap(psmidlle, line.LineCont[0], program)
		#elif line.LineType == "conditional":
		#	execnext = psmidlle.evalif(line)

def execute(psmidlle, lines):
	vars = {}
	lines = WrapLines(lines)
	ExecuteWrap(psmidlle, "main", lines)

class program:
	def get(this, name):
		if name in this.vars.keys():
			return this.vars[name]
		elif all([n in "+-0987654321." for n in name]):
			return eval(name)
		elif name[0] == '"' and name[-1] == '"':
				return name[1:-1].replace("\\\"", '"').replace("\\n", '\n')
		elif name in ["false", "true"]:
			return eval(name)
		else:
			panic(130, name, this.line)

	def gets(this, *names):
		names = SingleList(names)
		ret = []
		for name in names:
			ret.append(this.get(name))
		return ret

	def evalif(this, line):
		return all(this.gets(line.LineCont))

	def panic(this, line):
		panic(129, this.line)

	def exit (this, line):exit(this.get(line[0]))

	def write(this, line):
		for l in line:
			sout.write(this.get(l))

	def print(this, line):
		for l in line:
			sout.write(this.get(l))
		sout.write("\n")

	def flush(this, line):sout.flush()

	def set(this, line):this.vars[line[0]] = this.get(line[1])

	def debug(this, line):
		print("DEBUG{")
		printl("	")
		print(this.gets(line))
		printl("	")
		print(this.vars)
		printl("	")
		print(repr(this.line))
		print("}DEBUG")

	def sprintf(this, line):
		toset = line[0]
		string = this.get(line[1])
		args = this.gets(line[2:])
		this.vars[toset] = sprintf(string, *args)

	def printf(this, line):
		string = this.get(line[0])
		args = this.gets(line[1:])
		printf(string, *args)

	def MakeStream(this, line):
		streamname = line[0]
		streamtype = this.get(line[1])
		if streamtype == "w":
			streamto = this.get(line[2])
			if streamto == "sout":streamto = sout
			else: streamto = open(streamto, streamtype)
			def _stream_out(line):
				if line == ["close"]:
					if streamto == sout:
						panic(128, this.line)
					streamto.close()
					del this.commands[streamname]
				elif line[0] == "<<":
					streamto.write(this.get(line[1]))
				else:
					streamto.write(this.get(line[0]))
			this.commands[streamname] = _stream_out
		#
		elif streamtype == "r":
			streamto = this.get(line[2])
			if streamto == "sin":
				def _stream_in(line):
					this.vars[line[1]] = input()
			else:
				if not exists(streamto):
					panic(127, streamto, this.line)
				streamto = open(streamto, 'r')
				def _stream_in(line):
					#print(repr(streamto.readline()))
					if line[0] == "close":
						streamto.close()
						del this.commands[streamname]
					elif line[0] == ">>":
						this.vars[line[1]] = streamto.readline()
					else:
						this.vars[line[0]] = streamto.readline()

			this.commands[streamname] = _stream_in

	def math(this, line):
		resto = line.pop(0)
		oprd = []
		for op in line:
			if op in "+ - / * // ** %".split():
				oprd.append(str(op))
			else:
				oprd.append(str(this.get(op)))
		this.vars[resto] = eval(' '.join(oprd))

	def startif(this, line):
		if len(line) == 0:
			this.bool = not this.bool
		else:
			this.bool = all(this.gets(line))
	def endif(this, line):
		this.bool = None

	def __init__(this):
		this.commands = {
			" panic":this.panic,
			"exit"	:this.exit,
			"write" :this.write,
			"flush" :this.flush,
			"set"	:this.set,
			"debug" :this.debug,
			"print" :this.print,
			"sprintf":this.sprintf,
			"printf":this.printf,
			"mkstream":this.MakeStream,
			"//":nop,# comment
			"math":this.math,
			"@":this.startif,
			"@@":this.endif,
		}
		this.vars = {}
		this.bool = None
	def __call__(this, line):
		this.line = line
		if this.bool != False or line.LineCont[0] in ["@", "@@"]:
			this.commands.get(line.LineCont[0],
			this.panic)(line.LineCont[1:])
		return this.vars

execute(program(), ReadFile(get("").first))


#TODO#
#bool is global! (stop it)#
#make new psmiddle for every label? (thus making scopes) #
#return (get var up a scope)#
#TODO#
