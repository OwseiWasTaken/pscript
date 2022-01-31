#! /bin/python3.9
# by owsei: lang/pscript/main.py
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
	2 : "file \"{s}\" does not exits",
	3 : "no \"main\" label!",
	4 : "no \"main\" label in {s}",
	# runtime errors
	127 : "file {s} does not exits",
	128 : "can't close system out stream",
	129 : "no such command",
	130 : "no such var \"{s}\"",
	131 : "can't convert {r} (type {r}) to {r}",
}

def panic(errnum, *extra):
	extra = list(extra)
	if errnum > 126:
		printl( COLOR.red + "[" )
		printl( SetColorMode(COLOR.orange, '5')+"RUNTIME ERROR" )
		print( COLOR.red + "]" + COLOR.nc )
		line = extra.pop(-1)
		print(repr(line))
	else:
		printl( COLOR.red + "[" )
		printl( SetColorMode(COLOR.orange, '5')+"ERROR" )
		print ( COLOR.red + "]"+COLOR.nc )

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
			elif ln[0] == '>':
				tp = "include"
				cont = ln[1:]
			else:
				tp = "func"
				cont = ln
			cont = TrimSpaces(cont)
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
			if lbl:
				ret[lbl].append(line)
	return ret

def IncludeFile(filename: str) -> dict[str:list]:
	return WrapLines(ReadFile(filename))

def IncludeFiles(filenames: list[str]) -> dict[str:list]:
	ret = {}
	for flname in filenames:
		ret = ret | IncludeFile(flname)
	return ret
	return [ (ret:=ret | IncludeFile(x)) for x in filenames][-1]

def ExecuteWrap(psmiddle, name, program, passed = {}):
	execnext = None
	prog = program[name]
	myps = psmiddle()
	myps.vars = myps.vars | passed
	passon = {}
	for i in r(prog):
		if not myps.running:break
		line = prog[i]
		if line.LineType == "func":
			myps(line)
		elif line.LineType == "include":
			toinclude = IncludeFiles(line.LineCont)
			if "init" in toinclude.keys():
				myps.vars = ExecuteWrap(psmiddle, "init", toinclude)
			program = program | toinclude
		elif line.LineType == "jump":
			myps.vars = myps.vars | ExecuteWrap(
psmiddle, line.LineCont[0], program,)
#{program[line.LineCont[0]][x]:myps.get(line.LineCont[1:][x]) for x in r(line.LineCont[1:])})
#gotta make program struct to fit program recs and stuff
	return myps.Return

def execute(psmiddle, lines):
	vars = {}
	lines = WrapLines(lines)
	if "main" in lines.keys():
		coderan = ExecuteWrap(psmiddle, "main", lines)
		if coderan:
			return coderan[list(coderan.keys())[0]]
		else:
			return 0
	else:
		ll = lines.keys()
		if len(ll) == 1:
			panic(4, list(ll)[0])
		else:
			panic(4, tuple(lines.keys()))

class stdpsmiddle: # stdpm
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
		print("DEBUG %d {" % (this.line.LineNum+1))
		if this.gets(line):
			print(' '*4+', '.join(list(map(repr, this.gets(line)))))
		print(' '*4+str(this.vars))
		print(' '*4+repr(this.line))
		print("} %d DEBUG" % (this.line.LineNum+1))

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
			elif streamto == "eout":streamto = eout
			else: streamto = open(streamto, streamtype)
			def _stream_out(line):
				if line == ["close"]:
					if streamto in [ sout , eout]:
						panic(128, this.line)
					streamto.close()
					del this.commands[streamname]
				elif line[0] == "<<":
					for w in line[1:]:
						streamto.write(this.get(w))
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

	def ret(this, line):
		for l in line:
			this.Return[l] = this.get(l)
		this.running = False

	def delete(this, line):
		for l in line:
			if l in this.vars.keys():
				del this.vars[l]
			else:
				panic(130, l, this.line)

	def cdb(this, line):
		print(this.commands)

	def StringToDigit(this, line):
		toconv = line[0]
		value = this.get(line[0])
		if type(value) != str:
			panic(131, value, type(value), str, this.line)
		if all([n in "+-0987654321." for n in value]):
			this.vars[toconv] = eval(value)
		else:
			this.vars[toconv] = 0
		print(this.vars)

	def DigitToString(this, line):
		toconv = line[0]
		value = this.get(line[0])
		this.vars[toconv] = str(value)

	def ToBool(this, line):
		toconv = line[0]
		value = this.get(line[0])
		this.vars[toconv] = not not value

	def puts(this, line):
		stdout.write(', '.join([this.get(l) for l in line]))

	def read(this, line):
		tw = line[-1]
		if len(line) > 1:
			stdout.write(this.get(line[0]))
		this.vars[tw] = input()

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
			"read"  :this.read,
			"mkstream":this.MakeStream,
			"//":nop,# comment
			"math":this.math,
			"@":this.startif,
			"@@":this.endif,
			"return":this.ret,
			"StoD":this.StringToDigit,
			"DtoS":this.DigitToString,
			"ToB":this.ToBool,
			"del":this.delete,
			"cdb":this.cdb,
			"puts":this.puts,
		}
		this.vars = {}
		this.bool = None
		this.Return = {}
		this.running = True
	def __call__(this, line):
		this.line = line
		if this.bool != False or line.LineCont[0] in ["@", "@@"]:
			this.commands.get(line.LineCont[0],
			this.panic)(line.LineCont[1:])
		return this.vars

if __name__ == "__main__":
	args = get("").list
	if len(args) == 2:
		if '.' in args[0]:
			psmiddle = __import__('.'.join(args[0].split('.')[:-1])).psmiddle
		else:
			psmiddle = __import__(args[0]).psmiddle
		filename = args[1]
	elif len(args) == 1:
		psmiddle = stdpsmiddle
		filename = args[0]
	else:
		panic(1)

	exit(execute(
		psmiddle,
		ReadFile(filename)
	))
#TODO# ps executor
#error[4] printf {ls} '' && "" wrapping#
#λ./main.py examples/include.ps#
#[ERROR]#
#no "main" label in ["'yee'", "'yeet'"]#
#TODO#

#TODO# stdpm
#debug SYSTEM (don't stop at debug print)#
#TODO#
