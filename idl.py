from lark import Lark, Transformer, v_args
from lark.exceptions import *
import sys

grammar = '''
start: (message | enum)+

value: INT                          -> number
     | ESCAPED_STRING               -> string
     | "[" (value ",")* value? "]"  -> array

ATTRIBUTE_NAME: "tag" | "optional"
attribute: ATTRIBUTE_NAME ["(" (value ",")* value? ")"]
attributes: [attribute*]

message: "message" NAME INT message_block
enum: "enum" NAME enum_block

head_section: "head" "(" INT ")" ":" message_member+
tail_section: "tail" ":" message_member+

enum_block: "{" (enum_member ",")* enum_member "}"
message_block: "{" (head_section | tail_section)+ "}"

enum_member: NAME ["=" value]
message_member: attributes TYPE_NAME NAME ["=" value] ";"

TYPE_NAME: NAME ["[" [INT] "]"]
NAME: CNAME

%import common.INT
%import common.CNAME
%import common.ESCAPED_STRING

%import common.WS
%ignore WS
'''

class Message:
    def __init__(self, line, column, name, id, body):
        self.line = line
        self.column = column
        self.name = name
        self.id = id
        self.body = body

    def __repr__(self):
        return 'Message(' + self.name + ', ' + self.id + ') { ' + str(self.body) + ' }'

class HeadSection:
    def __init__(self, line, column, size, members):
        self.line = line
        self.column = column
        self.size = size
        self.members = members

    def __repr__(self):
        return 'HeadSection(' + self.size + ') { ' + str(self.members) + ' }'

class TailSection:
    def __init__(self, line, column, members):
        self.line = line
        self.column = column
        self.members = members

    def __repr__(self):
        return 'TailSection() { ' + str(self.members) + " }"

class MessageMember:
    def __init__(self, line, column, attributes, type, name, default_value):
        self.line = line
        self.column = column
        self.attributes = attributes
        self.type = type
        self.name = name
        self.default_value = default_value

    def __repr__(self):
        return (('(' + str(self.attributes) + ') ') if len(self.attributes) > 0 else '') + str(self.type) + ' ' + self.name + ((' = ' + str(self.default_value)) if self.default_value is not None else '')

class Type:
    def __init__(self, line, column, name):
        self.line = line
        self.column = column

        parts = name.split('[', 1)
        self.is_array = len(parts) > 1
        self.base_type = parts[0]
        self.array_size = (int(parts[1][:-1]) if parts[1] != ']' else -1) if self.is_array else 0

    def __repr__(self):
        return self.base_type + (('[' + str(self.array_size) + ']') if self.is_array else '')

class Attribute:
    def __init__(self, line, column, name, values):
        self.line = line
        self.column = column
        self.name = name
        self.values = values

    def __repr__(self):
        return self.name + (('( ' + str(self.values) + ' )') if len(self.values) > 0 else '')

class Enum:
    def __init__(self, line, column, name, members):
        self.line = line
        self.column = column
        self.name = name
        self.members = members

    def __repr__(self):
        return 'Enum(' + self.name + ') { ' + str(self.members) + ' }'

class EnumMember:
    def __init__(self, line, column, name, value = None):
        self.line = line
        self.column = column
        self.name = name
        self.value = value

    def __repr__(self):
        return self.name + ((' = ' + str(self.value)) if self.value is not None else '')

class ConstantValue:
    def __init__(self, line, column, type, value):
        self.line = line
        self.column = column
        self.value = value
        self.type = type

    def __repr__(self):
        return str(self.value)

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
        return MessageMember(meta.line, meta.column, items[0], Type(meta.line, meta.column, items[1]), items[2], items[3] if len(items) > 3 else None)

    def attributes(self, items):
        return items

    @v_args(meta = True)
    def attribute(self, items, meta):
        return Attribute(meta.line, meta.column, items[0], items[1:])

    @v_args(meta = True)
    def enum(self, items, meta):
        return Enum(meta.line, meta.column, items[0], flatten(items[1:]))

    @v_args(meta = True)
    def enum_member(self, items, meta):
        return EnumMember(meta.line, meta.column, items[0], items[1] if len(items) > 1 else None)

    def enum_block(self, items):
        return items

    @v_args(meta = True)
    def number(self, item, meta):
        return ConstantValue(meta.line, meta.column, 'number', int(item[0]))

    @v_args(meta = True)
    def string(self, item, meta):
        return ConstantValue(meta.line, meta.column, 'string', item[0])

    @v_args(meta = True)
    def array(self, items, meta):
        return ConstantValue(meta.line, meta.column, 'array', items)


def report_error(filename, line_str, line_no, column_no, message, message2):
    n_tabs = line_str.count('\t')
    line_str = line_str.replace('\t', '        ')
    line_no_str = str(line_no)

    n_spaces = ((column_no + n_tabs * 7) - 1)

    print('In {} at {}:{}: error: {}'.format(filename, line_no, column_no, message))
    print('  {} | {}'.format(line_no_str, line_str))
    print('  {} | {}^'.format(len(line_no_str) * ' ', n_spaces * ' '))
    if len(message2) > 0:
        print('{}{}'.format((len(line_no_str) + 5 + n_spaces) * ' ', message2))

    sys.exit(1)

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
    else:
        return token

def expected_to_human_readable(expected):
    return ', '.join(
            [token_name_to_human_readable(i if type(i) is str else i.name)
                for i in set(expected)])

def parse_and_transform(filename, code):
    parser = Lark(grammar, propagate_positions = True, parser = 'earley')
    lines = code.split('\n')
    parsed = None

    try:
        parsed = parser.parse(code)
    except UnexpectedToken as e:
        report_error(filename, lines[e.line - 1],
                e.line, e.column,
                'unexpected token \'{}\''.format(e.token),
                'Was expecting {} here'.format(expected_to_human_readable(e.expected)))
    except UnexpectedCharacters as e:
        report_error(filename, lines[e.line - 1],
                e.line, e.column,
                'unexpected character \'{}\''.format(lines[e.line - 1][e.column - 1]),
                'Was expecting {} here'.format(expected_to_human_readable(e.allowed)))
    except UnexpectedEOF as e:
        report_error(filename, lines[-2],
                len(lines) - 1, len(lines[-2]) + 1, 
                'unexpected end of file', 
                'Was expecting {} here'.format(expected_to_human_readable(e.expected)))

    return IdlTransformer().transform(parsed)

def verify_enum(filename, lines, enum):
    max_val = 0
    for m in enum.members:
        if type(m) is not EnumMember:
            report_error(filename, lines[m.line - 1],
                m.line, m.column,
                'unexpected token inside of an enum', '')
        if m.value is not None and m.value.type != 'number':
            report_error(filename, lines[m.value.line - 1],
                m.value.line, m.value.column,
                'enum value must be a number', '')

        # XXX: remove if we want to allow for this
        if m.value is not None and m.value.value < max_val:
            report_error(filename, lines[m.value.line - 1],
                m.value.line, m.value.column,
                'enum value must not go backwards', '')

        if m.value is None:
            max_val += 1
        else:
            max_val = m.value.value

# most of this function is a hack
def base_type_size(t):
    if t.count('int') > 0:
        return int(t.split('int', 1)[1]) / 8
    elif t == 'byte':
        return 1
    else:
        return -1

# returns size of member in bytes
def verify_member(filename, lines, m):
    if type(m) is not MessageMember:
        report_error(filename, lines[m.line - 1],
            m.line, m.column,
            'unexpected token inside of an message section', '')

    if m.default_value is not None:
        # TODO: allow this?
        if m.type.is_array and m.type.base_type == 'string':
            report_error(filename, lines[m.type.line - 1],
                m.type.line, m.type.column,
                'arrays of strings are not allowed', '')

        if m.default_value.type == 'array' and not m.type.is_array:
            report_error(filename, lines[m.default_value.line - 1],
                m.default_value.line, m.default_value.column,
                'default value of a non-array member cannot be an array', 
                'Was expecting a {} here'.format(m.type))

        if m.type.is_array and m.default_value.type != 'array':
            report_error(filename, lines[m.default_value.line - 1],
                m.default_value.line, m.default_value.column,
                'default value of an array member must be an array',
                'Was expecting an array here')

        # TODO: check type mismatch

        if m.type.is_array and m.type.array_size != -1 and m.type.array_size < len(m.default_value.value):
            report_error(filename, lines[m.default_value.line - 1],
                m.default_value.line, m.default_value.column,
                'expected array with at most {} elements, but array with {} was given'.format(
                    m.type.array_size, len(m.default_value.value)),
                'Was expecting an at most {} element array here'.format(m.type.array_size))

    member_size = base_type_size(m.type.base_type)

    if m.type.is_array and m.type.array_size != -1:
        member_size *= m.type.array_size

    return member_size

def verify_message(filename, lines, msg):
    for s in msg.body:
        if type(s) is HeadSection:
            memb_size_total = 0
            for m in s.members:
                size = verify_member(filename, lines, m)
                if size < 0:
                    report_error(filename, lines[m.line - 1],
                            m.line, m.column,
                            'dynamically sized member not allowed in head section', '')
                for attr in m.attributes:
                    if attr.name == 'tag':
                        report_error(filename, lines[attr.line - 1],
                            attr.line, attr.column,
                            'tagged member not allowed in the head section', '')
                memb_size_total += size
            if memb_size_total > s.size:
                report_error(filename, lines[s.line - 1],
                        s.line, s.column,
                        'head section is {} bytes too short to fit all members'.format(memb_size_total - s.size), '')
        elif type(s) is TailSection:
            for m in s.members:
                verify_member(filename, lines, m)
        else:
            report_error(filename, lines[s.line - 1],
                s.line, s.column,
                'unexpected token in message body',
                'Was expecting {} here'.format(expected_to_human_readable(['HEAD', 'TAIL'])))

def verify_idl(filename, code, idl):
    lines = code.split('\n')

    for i in idl:
        if type(i) is Enum:
            verify_enum(filename, lines, i)
        elif type(i) is Message:
            verify_message(filename, lines, i)
        else:
            report_error(filename, lines[i.line - 1],
                    i.line, i.column,
                    'unexpected token in top level', '')

source = 'sample.idl'

with open(source, "r") as f:
    code = f.read()
    idl = parse_and_transform(source, code)
    verify_idl(source, code, idl)
    print('Input verified correctly. TODO: Compile it');
