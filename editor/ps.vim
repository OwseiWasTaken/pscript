
" vim syntax file for the s programming lang

if exists("b:current_syntax")
	finish
endif

syn match KWD '\(@\|!\)'
syn match KWD '#main'
syn match KWD '##'


syn match Number '[+-]\?\d\d*'
syn match Number '\(null\|false\|true\)'
syn match Comment '^\t//.*'
syn match Todo '^\t// \?TODO'


syn match SpecialStr '\({[sifbx]}\|\\"\|\\n\)' contained
syn match String '\"\([^"]\{-\}\|\"+\)\"' contains=SpecialStr




hi def link KWD				Keyword
hi def link SpecialStr		Keyword
hi def link QuoteCancel		Keyword
hi def link Todo			Todo
hi def link Comment			Comment
hi def link String			Constant
hi def link Number			Constant
hi def link Function		Function
