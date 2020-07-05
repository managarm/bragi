" Language: Bragi
" Maintainer: The Managarm Project (info@managarm.org)
" Last Change: 2020 Jul 5

if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syn case match

syn keyword bragiTopLevel enum consts namespace message struct using
syn keyword bragiType int8 int16 int32 int64 
syn keyword bragiType uint8 uint16 uint32 uint64
syn keyword bragiType byte char string tags

syn keyword bragiTodo TODO XXX FIXME HACK contained 
syn cluster bragiCommentGrp contains=bragiTodo

syn match bragiNameSep /::/ contained 
syn cluster bragiNameGrp contains=bragiNameSep

syn keyword bragiStructure head tail tag

syn match bragiNumber /-\?\<\d\+\>/

syn region bragiComment start='\/\*' end='\*\/' contains=@bragiCommentGrp
syn region bragiComment start='//' skip='\\$' end='$' keepend contains=@bragiCommentGrp

syn region bragiNameString  start=/"/ skip=/\\./ end=/"/ contains=@bragiNameGrp


if version >= 508 || !exists("did_bragi_syn_inits")
  if version <= 508
    let did_bragi_syn_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

  " The default highlight links.  Can be overridden later.
  HiLink bragiType Type
  HiLink bragiTopLevel Keyword
  HiLink bragiNumber Number
  HiLink bragiStructure Statement
  HiLink bragiComment Comment
  HiLink bragiTodo Todo
  HiLink bragiNameString String
  HiLink bragiNameSep Special

  delcommand HiLink
endif

let b:current_syntax = "bragi"
