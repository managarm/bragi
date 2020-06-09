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
    def __init__(self, line, column, tag, type, name):
        self.line = line
        self.column = column
        self.tag = tag
        self.type = type
        self.name = name

    def __repr__(self):
        return (str(self.tag) + ' ' if self.tag else '') + str(self.type) + ' ' + self.name

class TagsBlock:
    def __init__(self, line, column, members):
        self.line = line
        self.column = column
        self.members = members

    def __repr__(self):
        return 'TagsBlock { ' + str(self.members) + ' }'


class Type:
    def __init__(self, line, column, name):
        self.line = line
        self.column = column

        if name != 'string':
            parts = name.split('[', 1)
            self.is_array = len(parts) > 1
            self.base_type = parts[0]
            self.array_size = (int(parts[1][:-1]) if parts[1] != ']' else -1) if self.is_array else 0
        else:
            self.is_array = True
            self.base_type = 'uint8'
            self.array_size = -1

    def __repr__(self):
        return self.base_type + (('[' + str(self.array_size) + ']') if self.is_array else '')

class Tag:
    def __init__(self, line, column, value):
        self.line = line
        self.column = column
        self.value = value

    def __repr__(self):
        return 'tag(' + str(self.value) + ')'

class Enum:
    def __init__(self, line, column, name, mode, type, members):
        self.line = line
        self.column = column
        self.name = name
        self.mode = mode
        self.type = Type(line, column, type)
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

class EofToken:
    def __init__(self, line, column):
        self.line = line
        self.column = column

def fixed_type_size(t):
    size = None

    if t.base_type == 'byte' or t.base_type == 'uint8' or t.base_type == 'int8':
        size = 1
    elif t.base_type == 'int16' or t.base_type == 'uint16':
        size = 2
    elif t.base_type == 'int32' or t.base_type == 'uint32':
        size = 4
    elif t.base_type == 'int64' or t.base_type == 'uint64':
        size = 8

    if t.is_array:
        if t.array_size > 0:
            size *= t.array_size
        else:
            size = None

    return size

def subscript_type_size(t):
    if t.base_type == 'byte' or t.base_type == 'uint8' or t.base_type == 'int8':
        return 1
    elif t.base_type == 'int16' or t.base_type == 'uint16':
        return 2
    elif t.base_type == 'int32' or t.base_type == 'uint32':
        return 4
    elif t.base_type == 'int64' or t.base_type == 'uint64':
        return 8

    return None
