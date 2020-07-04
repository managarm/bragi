import sys

from lark.lark import Lark
from lark.visitors import Transformer, v_args
from lark.exceptions import *

from bragi.tokens import *
from bragi.types import *

grammar = r'''
start: (message | enum | consts | ns)+

tag: "tag" "(" INT ")"
attributes: tag?

message: "message" NAME INT message_block
enum: "enum" NAME enum_block
consts: "consts" NAME type_name enum_block
ns: "namespace" ESCAPED_STRING ";"

head_section: "head" "(" INT ")" ":" message_member*
tail_section: "tail" ":" message_member*

enum_block: "{" (enum_member ",")* enum_member "}"
message_block: "{" (head_section | tail_section)+ "}"

enum_member: NAME ["=" INT]
message_member: attributes type_name NAME ";" -> message_member
                | "tags" "{" message_member+ "}" -> tags_block

type_name: NAME type_size*
NAME: CNAME

type_size: "[" INT "]"
         | "[" "]"

%import common.INT
%import common.CNAME
%import common.ESCAPED_STRING
%import common.NEWLINE

%import common.WS
%ignore WS

COMMENT: "//" /(.)+/ NEWLINE
       | "/*" /(.|\n)+/ "*/"

%ignore COMMENT
'''

flatten = lambda l: [item for sublist in l for item in sublist]

class IdlTransformer(Transformer):
    def start(self, items):
        return items

    @v_args(meta = True)
    def message(self, items, meta):
        return Message(meta.line, meta.column, items[0], items[1], flatten(items[2:]))

    def message_block(self, items):
        return items

    @v_args(meta = True)
    def head_section(self, items, meta):
        return HeadSection(meta.line, meta.column, int(items[0]), items[1:])

    @v_args(meta = True)
    def tail_section(self, items, meta):
        return TailSection(meta.line, meta.column, items)

    @v_args(meta = True)
    def message_member(self, items, meta):
        return MessageMember(meta.line, meta.column, items[0], items[1], items[2])

    @v_args(meta = True)
    def tags_block(self, items, meta):
        return TagsBlock(meta.line, meta.column, items)

    def attributes(self, items):
        return items[0] if len(items) > 0 else None

    @v_args(meta = True)
    def tag(self, items, meta):
        return Tag(meta.line, meta.column, items[0])

    @v_args(meta = True)
    def enum(self, items, meta):
        return Enum(meta.line, meta.column, items[0], 'enum', TypeName(0, 0, 'int32'), flatten(items[1:]))

    @v_args(meta = True)
    def consts(self, items, meta):
        return Enum(meta.line, meta.column, items[0], 'consts', items[1], flatten(items[2:]))

    @v_args(meta = True)
    def enum_member(self, items, meta):
        return EnumMember(meta.line, meta.column, items[0], int(items[1]) if len(items) > 1 else None)

    def enum_block(self, items):
        return items

    def NAME(self, items):
        return str(items)

    @v_args(meta = True)
    def type_name(self, items, meta):
        return TypeName(meta.line , meta.column, ''.join(items))

    @v_args(meta = True)
    def type_size(self, items, meta):
        return '[' + ''.join(items) + ']'

    def attributes(self, items):
        return items[0] if len(items) > 0 else None

def token_name_to_human_readable(token):
    if token == 'NAME':
        return 'a name'
    elif token == 'INT':
        return 'a number'
    elif token == 'TAIL':
        return 'a tail section'
    elif token == 'HEAD':
        return 'a head section'
    elif token == 'LPAR':
        return 'a left parenthesis'
    elif token == 'RPAR':
        return 'a right parenthesis'
    elif token == 'LBRACE':
        return 'a left brace'
    elif token == 'RBRACE':
        return 'a right brace'
    elif token == 'ATTRIBUTE_NAME':
        return 'an attribute'
    elif token == 'TYPE_NAME':
        return 'a type name'
    elif token == 'LSQB':
        return 'an array' # this is more descriptive than "a left square bracket"
    elif token == 'ESCAPED_STRING':
        return 'a string'
    elif token == 'SEMICOLON':
        return 'a semicolon'
    elif token == 'EQUAL':
        return 'an equals sign'
    elif token == 'COMMA':
        return 'a comma'
    elif token == 'MESSAGE':
        return '"message"'
    elif token == 'ENUM':
        return '"enum"'
    elif token == 'TAGS':
        return 'a tags block'
    elif token == 'TAG':
        return 'a tag'
    else:
        return token

def expected_to_human_readable(expected):
    return ', '.join(
            [token_name_to_human_readable(i if type(i) is str else i.name)
                for i in set(expected)])

class CompilationUnit:
    def __init__(self, filename, source):
        self.filename = filename
        self.source = source
        self.lines = source.split('\n')
        self.tokens = None
        self.eof = EofToken(len(self.lines) - 1, len(self.lines[-2]) + 1)
        self.type_registry = TypeRegistry()

    def report_message(self, token, mesg_type, mesg1, mesg2, fatal = True):
        line = self.lines[token.line - 1]

        n_tabs = line.count('\t')
        line = line.replace('\t', '        ')
        line_number = str(token.line)
        line_no_len = len(line_number)

        n_spaces = len(line_number) + ((token.column + n_tabs * 7) - 1) + 5
        spaces = n_spaces * ' '

        print(f'{self.filename}:{token.line}:{token.column}: {mesg_type}: {mesg1}')
        print(f'  {line_number} | {line}')
        print(f'{spaces}^')

        if len(mesg2) > 0:
            print(f'{spaces}{mesg2}')

        if fatal:
            sys.exit(1)

    def process(self):
        parser = Lark(grammar, propagate_positions = True, parser = 'lalr')
        lines = self.source.split('\n')
        parsed = None

        try:
            parsed = parser.parse(self.source)
        except UnexpectedToken as e:
            self.report_message(e, 'error',
                    'unexpected token \'{}\''.format(e.token),
                    'Was expecting {} here'.format(expected_to_human_readable(e.expected)))
        except UnexpectedCharacters as e:
            self.report_message(e, 'error',
                    'unexpected character \'{}\''.format(lines[e.line - 1][e.column - 1]),
                    'Was expecting {} here'.format(expected_to_human_readable(e.allowed)))
        except UnexpectedEOF as e:
            self.report_message(eof, 'error',
                    'unexpected end of file', 
                    'Was expecting {} here'.format(expected_to_human_readable(e.expected)))

        self.tokens = IdlTransformer().transform(parsed)

        for t in self.tokens:
            if type(t) is Enum:
                if self.type_registry.is_known_type(t.name):
                    self.report_message(t.type, 'error', f'name {t.name} is already in use.', '')

                subtype = self.type_registry.get_type(t.type.name)
                if not subtype:
                    self.report_message(t.type, 'error', f'unknown type for this {t.mode} block', f'{t.type.name} is not a known type', True)
                if subtype.identity is not TypeIdentity.INTEGER:
                    self.report_message(t.type, 'error', f'{t.name} {t.mode} block\'s type is not an integer', f'{t.type.name} is not an integer')

                self.type_registry.register_type(
                    Type(t.name,
                        TypeIdentity.CONSTS if t.mode == 'consts' else TypeIdentity.ENUM,
                        fixed_size = subtype.fixed_size,
                        signed = subtype.signed,
                        subtype = subtype)
                )

                t.type = self.type_registry.get_type(t.name)

    def verify_enum(self, enum):
        for m in enum.members:
            if type(m) is not EnumMember:
                self.report_message(m, 'error',
                    'unexpected token inside of an enum', '')

    def determine_pointer_size(self, size):
        if size < 256:
            return 1
        elif size < 65536:
            return 2
        elif size < 4294967296:
            return 4
        elif size < 18446744073709551616:
            return 8

    # returns size of member in bytes
    def verify_member(self, m, parent):
        if type(m) is TagsBlock:
            for t in m.members:
                self.verify_member(t, m)
                if not t.tag:
                    self.report_message(t, 'error',
                        'untagged member in tags block', '')

            if type(parent) is HeadSection:
                return self.determine_pointer_size(parent.size)
        else:
            if type(m) is not MessageMember:
                self.report_message(m, 'error',
                    'unexpected token inside of an message section', '', True)

            if m.tag and type(parent) is not TagsBlock:
                self.report_message(m, 'error',
                    'tagged member outside of tags block', '')

            m.type = self.type_registry.parse_type(m.typename.name)
            if not m.type:
                self.report_message(m, 'error',
                    'unknown type for this member', f'{m.typename.name} is not a known type')

            if type(parent) is HeadSection:
                return m.type.fixed_size if not m.type.dynamic else self.determine_pointer_size(parent.size)

    def verify_message(self, msg):
        if msg.head is not None:
            total_size = 8
            for m in msg.head.members:
                total_size += self.verify_member(m, msg.head)
            if total_size > msg.head.size:
                self.report_message(s, 'error',
                        'head section is {} bytes too short to fit all fixed-width members'.format(total_size - msg.head.size),
                        'note: the head has two hidden uint32 members for the message id and tail size')
        if msg.tail is not None:
            for m in msg.tail.members:
                self.verify_member(m, msg.tail)

    def verify(self):
        for i in self.tokens:
            if type(i) is Enum:
                self.verify_enum(i)
            elif type(i) is Message:
                self.verify_message(i)
            elif type(i) is not NamespaceTag:
                self.report_message(i, 'error',
                        'unexpected token in top level', '')
