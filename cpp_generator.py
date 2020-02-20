from tokens import *

class StdlibTraits:
    def needs_allocator(self):
        return False
    def allocator_argument(self):
        return ''
    def allocator_parameter(self):
        return ''
    def vector(self):
        return 'std::vector'
    def string(self):
        return 'std::string'
    def assert_func(self):
        return 'assert'

class FriggTraits:
    def needs_allocator(self):
        return True
    def allocator_argument(self):
        return 'Allocator allocator = Allocator()'
    def allocator_parameter(self):
        return 'allocator'
    def vector(self):
        return 'frg::vector'
    def string(self):
        return 'frg::string'
    def assert_func(self):
        return 'FRG_ASSERT'

flatten = lambda l: [item for sublist in l for item in sublist]

class CodeGenerator:
    def __init__(self, stdlib = 'libc++'):
        self.stdlib_traits = None

        if stdlib == 'libc++':
            self.stdlib_traits = StdlibTraits()
        elif stdlib == 'frigg':
            self.stdlib_traits = FriggTraits()
        else:
            raise AttributeError('invalid standard library')

    def generate(self, thing):
        if type(thing) == Enum:
            return self.generate_enum(thing)
        if type(thing) == Message:
            return self.generate_message(thing)

    def generate_enum(self, enum):
        out = 'namespace {} {{\n'.format(enum.name)
        i = 0

        for m in enum.members:
            if m.value is not None:
                i = m.value.value

            out += '\tinline constexpr {} {} = {};\n'.format(
                    'int', m.name, i) # TODO: get type from the enum

            i += 1

        return out + '}} // namespace {}\n'.format(enum.name)

    def generate_type(self, t):
        base_type_name = t.base_type

        if t.base_type == 'byte' or t.base_type == 'uint8':
            base_type_name = 'uint8_t'
        elif t.base_type == 'int8':
            base_type_name = 'int8_t'
        elif t.base_type == 'int16':
            base_type_name = 'int16_t'
        elif t.base_type == 'uint16':
            base_type_name = 'uint16_t'
        elif t.base_type == 'int32':
            base_type_name = 'int32_t'
        elif t.base_type == 'uint32':
            base_type_name = 'uint32_t'
        elif t.base_type == 'int64':
            base_type_name = 'int64_t'
        elif t.base_type == 'uint64':
            base_type_name = 'uint64_t'
        elif t.base_type == 'string':
            base_type_name = '{}{}'.format(self.stdlib_traits.string(),
                    '<Allocator>' if self.stdlib_traits.needs_allocator() else '')
        if t.is_array:
            out = self.stdlib_traits.vector()
            out += '<{}{}>'.format(base_type_name,
                    ', Allocator' if self.stdlib_traits.needs_allocator() else '')
            return out
        else:
            return base_type_name

    def generate_encoder(self, message):
        out = '\tbool serialize_to_array(void *buf, size_t size) {\n'
        out += '\t\tbragi::internals::writer wr{static_cast<uint8_t *>(buf), size};\n'
        out += '\t\tif (size < head_size)\n\t\t\treturn false;\n'

        out += '\t\twr.serialize(0, message_id);\n'

        i = 8
        try:
            for m in message.head.members:
                if m.type.is_array:
                    out += '\t\twr.serialize({}, {}, {});\n'.format(i, 'm_' + m.name, m.type.array_size)
                    i += int(base_type_size(m.type.base_type) * m.type.array_size)
                else:
                    out += '\t\twr.serialize({}, {});\n'.format(i, 'm_' + m.name)
                    i += int(base_type_size(m.type.base_type))

            i = message.head.size
        except:
            pass

        try:
            out += '\t\tsize_t i = {}; // Index into tail\n'.format(message.head.size);
            for m in message.tail.members:
                tag_present = False
                tag = 0
                optional = False
                for attr in m.attributes:
                    if attr.name == 'tag':
                        tag_present = True
                        tag = attr.values[0]
                    elif attr.name == 'optional':
                        optional = True

                assert tag_present # Implement untagged fields in tail later
                
                if optional:
                    out += '\t\tif ({}) {{\n'.format('p_' + m.name)
                else:
                    out += '\t\tassert({});\n'.format('p_' + m.name)

                if tag_present:
                    if optional:
                        out += '\t' # Keep outputted code looking nice
                    out += '\t\ti += wr.serialize(i, {});\n'.format(f'varint{{{tag}}}')

                if optional:
                        out += '\t' # Keep outputted code looking nice
                if m.type.is_array:
                    out += '\t\ti += wr.serialize(i, {}, {});\n'.format('m_' + m.name, m.type.array_size)
                else:
                    out += '\t\ti += wr.serialize(i, {});\n'.format('m_' + m.name)
                
                if optional:
                    out += '\t\t}}\n'.format()
        except:
            pass

        return out + '\t\treturn true;\n\t}\n\n'

    def generate_decoder(self, message):
        out = '\tbool deserialize_from_array(void *buf, size_t size) {\n'
        out += '\t\tbragi::internals::reader rd{static_cast<uint8_t *>(buf), size};\n'
        out += '\t\tif (size < head_size)\n\t\t\treturn false;\n'

        out += '\t\tuint64_t id = rd.deserialize<uint64_t>(0);\n'
        out += '\t\tif(id != message_id)\n\t\t\treturn false;\n'

        i = 8
        try:
            for m in message.head.members:
                if m.type.is_array:
                    out += '\t\t{} = rd.deserialize<{}>({}, {});\n'.format('m_' + m.name, self.generate_type(m.type), i, m.type.array_size)
                    out += '\t\t{} = true;\n'.format('p_' + m.name)
                    i += int(fixed_type_size(m.type))
                else:
                    out += '\t\t{} = rd.deserialize<{}>({});\n'.format('m_' + m.name, self.generate_type(m.type), i)
                    out += '\t\t{} = true;\n'.format('p_' + m.name)
                    i += int(fixed_type_size(m.type))
            i = message.head.size
        except:
            pass

        try:
            out += '\t\tsize_t i = {}; // Index into tail\n'.format(message.head.size);
            out += '\t\twhile (i < size) {\n'
            out += '\t\t\tsize_t varint_size = 0;\n'
            out += '\t\t\tuint64_t tag = rd.deserialize<varint>(i, varint_size);\n'
            out += '\t\t\ti += varint_size;\n'
            out += '\t\t\tswitch (tag) {\n'
            for m in message.tail.members:
                tag_present = False
                tag = 0
                optional = False
                for attr in m.attributes:
                    if attr.name == 'tag':
                        tag_present = True
                        tag = attr.values[0]
                    elif attr.name == 'optional':
                        optional = True

                assert tag_present # Implement untagged fields in tail later

                out += '\t\t\t\tcase {}:\n'.format(tag)
                out += '\t\t\t\t\t{} = true;\n'.format('p_' + m.name)

                if m.type.is_array and m.type.array_size > 0:
                    out += '\t\t\t\t\t{} = rd.deserialize<{}>(i, {});\n'.format('m_' + m.name, self.generate_type(m.type), m.type.array_size)
                    out += '\t\t\t\t\ti += {};\n'.format(fixed_type_size(m.type))
                elif m.type.base_type != 'string' and m.type.array_size == 0:
                    out += '\t\t\t\t\t{} = rd.deserialize<{}>(i);\n'.format('m_' + m.name, self.generate_type(m.type))
                    out += '\t\t\t\t\ti += {};\n'.format(fixed_type_size(m.type))
                else:
                    print('TODO: Encode dynamic width members')

                out += '\t\t\t\t\tbreak;\n'

            out += '\t\t\t\tdefault:\n'
            out += '\t\t\t\t\t// TODO: Unknown tag, panic\n'
            out += '\t\t\t\t\treturn false;\n'

            out += '\t\t\t}\n'
            out += '\t\t}\n'
        except:
            pass

        return out + '\t\treturn true;\n\t}\n\n'

    def generate_message(self, message):
        head = None
        tail = None

        try:
            head = message.head
        except:
            head = None

        try:
            tail = message.tail
        except:
            tail = None

        all_members = flatten([
            head.members if head is not None else [],
            tail.members if tail is not None else []
        ])

        out = ''
        if self.stdlib_traits.needs_allocator():
            out += 'template <typename Allocator>\n'

        out += 'struct {} {{\n'.format(message.name)
        out += '\tstatic constexpr uint64_t message_id = {};\n'.format(message.id)
        out += '\tstatic constexpr size_t head_size = {};\n\n'.format(message.head.size)

        out += '\t{}({})\n\t: '.format(message.name, self.stdlib_traits.allocator_argument())

        i = 0
        for m in all_members:
            out += 'm_{}{{{}}}, p_{}{{false}}'.format(m.name,
                    self.stdlib_traits.allocator_parameter() if m.type.is_array else '',
                    m.name)

            if i < len(all_members) - 1:
                out += ', \n\t  '

            i += 1

        out += ' {}\n\n'

        for m in all_members:
            # getter
            out += '\tinline {} {}() {{\n'.format(self.generate_type(m.type), m.name)
            out += '\t\t{}(p_{});\n'.format(self.stdlib_traits.assert_func(), m.name)
            out += '\t\treturn m_{};\n'.format(m.name)
            out += '\t}\n\n'

            # setter
            out += '\tinline void set_{}({} val) {{\n'.format(m.name, self.generate_type(m.type))
            out += '\t\tp_{} = true;\n'.format(m.name)
            out += '\t\tm_{} = val;\n'.format(m.name)
            out += '\t}\n\n'

        out += self.generate_encoder(message)
        out += self.generate_decoder(message)

        out += 'private:\n'
        for m in all_members:
            out += '\t{} m_{}; bool p_{};\n'.format(self.generate_type(m.type), m.name,
                    m.name)

        return out + '};\n'
