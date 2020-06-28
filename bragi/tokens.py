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
    def __init__(self, line, column, tag, typename, name):
        self.line = line
        self.column = column
        self.tag = tag
        self.typename = typename
        self.type = None
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


class TypeName:
    def __init__(self, line, column, name):
        self.line = line
        self.column = column
        self.name = name

    def __repr__(self):
        return self.name

class Tag:
    def __init__(self, line, column, value):
        self.line = line
        self.column = column
        self.value = value

    def __repr__(self):
        return 'tag(' + str(self.value) + ')'

class Enum:
    def __init__(self, line, column, name, mode, typename, members):
        self.line = line
        self.column = column
        self.name = name
        self.mode = mode
        self.type = typename
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

class NamespaceTag:
    def __init__(self, line, column, name):
        self.line = line
        self.column = column
        self.name = name
