import enum

class TypeIdentity(enum.Enum):
    INTEGER = 1
    ENUM = 2
    CONSTS = 3
    STRUCT = 4
    ARRAY = 5
    STRING = 6

class Type:
    def __init__(self, name, identity, fixed_size = None, dynamic = False, subtype = None, signed = False, n_elements = None):
        self.name = name
        self.identity = identity
        self.fixed_size = fixed_size
        self.dynamic = dynamic
        self.subtype = None
        self.n_elements = None
        self.signed = None

        if self.identity in {TypeIdentity.ARRAY, TypeIdentity.STRING}:
            assert subtype
            self.subtype = subtype

        if self.identity is TypeIdentity.ARRAY and n_elements:
            self.n_elements = n_elements

        if self.identity is TypeIdentity.INTEGER:
            self.signed = signed

class TypeRegistry:
    def __init__(self):
        self.types = {
            'int8': Type('int8', TypeIdentity.INTEGER, fixed_size = 1, signed = True),
            'int16': Type('int16', TypeIdentity.INTEGER, fixed_size = 2, signed = True),
            'int32': Type('int32', TypeIdentity.INTEGER, fixed_size = 4, signed = True),
            'int64': Type('int64', TypeIdentity.INTEGER, fixed_size = 8, signed = True),

            'uint8': Type('uint8', TypeIdentity.INTEGER, fixed_size = 1, signed = False),
            'uint16': Type('uint16', TypeIdentity.INTEGER, fixed_size = 2, signed = False),
            'uint32': Type('uint32', TypeIdentity.INTEGER, fixed_size = 4, signed = False),
            'uint64': Type('uint64', TypeIdentity.INTEGER, fixed_size = 8, signed = False),

            'char': Type('char', TypeIdentity.INTEGER, fixed_size = 1),
            'byte': Type('byte', TypeIdentity.INTEGER, fixed_size = 1, signed = False)
        }

        self.types['string'] = Type('string', TypeIdentity.STRING, dynamic = True, subtype = self.types['char'])

    def get_type(self, name):
        return self.types[name] if name in self.types else None

    def register_type(self, type):
        self.types[type.name] = type

    def is_known_type(self, name):
        return name in self.types

    def parse_type(self, name):
        base, delim, size = name.rpartition('[')

        if size[-1] != ']':
            return None

        if delim == '':
            if name in self.types:
                return None
            else:
                return self.types[name]

        size = size[:-1]
        i_size = None

        if len(size) > 0:
            try:
                i_size = int(size)
            except ValueError:
                return None

        base_type = parse_type(base)
        if not base_type:
            return None

        dynamic = base_type.dynamic or len(size) > 0
        t_size = base_type.size * i_size if not dynamic else None

        return Type(name, TypeIdentity.ARRAY,
                fixed_size = t_size,
                n_elements = i_size,
                dynamic = dynamic,
                subtype = base_type)
