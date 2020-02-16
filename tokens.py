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

class Message:
    def __init__(self, line, column, name, id, body):
        self.line = line
        self.column = column
        self.name = name
        self.id = id
        self.head = None
        self.tail = None
        for m in body:
            if self.head is None and type(m) is HeadSection:
                self.head = m
            elif self.tail is None and type(m) is TailSection:
                self.tail = m

    def __repr__(self):
        return 'Message(' + self.name + ', ' + self.id + ') { ' + str(self.body) + ' }'

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

class EofToken:
    def __init__(self, line, column):
        self.line = line
        self.column = column

# most of this function is a hack
def base_type_size(t):
    if t.count('int') > 0:
        return int(t.split('int', 1)[1]) / 8
    elif t == 'byte':
        return 1
    else:
        return -1


