from .tokens import *

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
    def __init__(self, stdlib):
        self.stdlib_traits = None

        if stdlib == 'libc++':
            self.stdlib_traits = StdlibTraits()
        elif stdlib == 'frigg':
            self.stdlib_traits = FriggTraits()
        else:
            raise AttributeError('invalid standard library')

    def generate(self, thing):
        if type(thing) == Enum and thing.mode == "enum":
            return self.generate_enum(thing)
        if type(thing) == Enum and thing.mode == "consts":
            return self.generate_consts(thing)
        if type(thing) == Message:
            return self.generate_message(thing)

    def generate_consts(self, enum):
        out = f'namespace {enum.name} {{\n'
        i = 0

        for m in enum.members:
            if m.value is not None:
                i = m.value.value

            out += f'\tinline constexpr {"int"} {m.name} = {i};\n' # TODO: get type from the enum

            i += 1

        return out + f'}} // namespace {enum.name}\n'

    def generate_enum(self, enum):
        out = f'enum class {enum.name} {{\n'
        i = 0

        for m in enum.members:
            if m.value is not None:
                i = m.value.value

            out += f'\t{m.name} = {i};\n'

            i += 1

        return out + f'}} // enum class {enum.name}\n'



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
        if t.is_array:
            return '{}<{}{}>'.format(self.stdlib_traits.vector(), base_type_name,
                    ', Allocator' if self.stdlib_traits.needs_allocator() else '')
        else:
            return base_type_name

    def needs_fixup(self, m):
        return type(m) is TagsBlock or (m.type.is_array and m.type.array_size == -1)

    def count_fixups_required(self, members):
        i = 0
        for m in members:
            if self.needs_fixup(m):
                i += 1

        return i

    def emit_fixed_member_encoder(self, member, depth = 1, n_fixup = 0):
        indent = '\t' * depth

        mname = ''
        pname = ''
        if type(member) is TagsBlock:
            mname = f'tags{n_fixup}'
            pname = f'?? tags{n_fixup}'
        else:
            mname = f'm_{member.name}'
            pname = f'p_{member.name}'

        out = f'{indent}// Encode {mname}\n';
        if self.needs_fixup(member):
            out += f'{indent}fixups[{n_fixup}] = i;\n'
            out += f'{indent}i += 16;\n' # skip pointer + size
        elif member.type.is_array:
            out += f'{indent}{self.stdlib_traits.assert_func()}({pname});\n'
            out += f'{indent}i += wr.serialize(i, {mname}, {member.type.array_size});\n'
        else:
            out += f'{indent}{self.stdlib_traits.assert_func()}({pname});\n'
            out += f'{indent}i += wr.serialize(i, {mname});\n'

        return out + '\n'

    def emit_dynamic_member_encoder(self, member, depth = 1):
        indent = '\t' * depth
        out = ''

        if type(member) is TagsBlock:
            for m in member.members:
                out += f'{indent}if ({"p_" + m.name}) {{\n'
                depth += 1
                indent = '\t' * depth

                tag = -1
                for attr in m.attributes:
                    if attr.name == 'tag':
                        tag_present = True
                        tag = attr.values[0]

                mname = f'm_{m.name}'
                pname = f'p_{m.name}'

                out += f'{indent}i += bragi::varint{{{tag}}}.encode(wr.buf() + i);\n'
                if m.type.is_array:
                    out += f'{indent}i += wr.serialize(i, {mname}, {mname}.size());\n'
                else:
                    out += f'{indent}i += wr.serialize(i, {"p_" + m.name});\n'

                depth -= 1
                indent = '\t' * depth
                out += f'{indent}}}\n'

        return out

    def emit_head_encoder(self, message, depth = 1):
        n_fixups = self.count_fixups_required(message.head.members)
        indent = '\t' * depth

        out = f'{indent}bool encode_head(void *buf, size_t size) {{\n'
        depth += 1
        indent = '\t' * depth

        out += f'{indent}bragi::writer wr{{buf, size}};\n'
        out += f'{indent}uint64_t i = 0;\n'

        if n_fixups > 0:
            out += f'{indent}uint64_t fixups[{n_fixups}];\n'
            out += f'{indent}uint64_t old_i = 0;\n'

        out += '\n'

        n_fixup = 0
        for m in message.head.members:
            out += self.emit_fixed_member_encoder(m, depth, n_fixup)
            if self.needs_fixup(m):
                n_fixup += 1

        n_fixup = 0
        for m in message.head.members:
            if not self.needs_fixup(m):
                continue

            mname = ''
            if type(m) is TagsBlock:
                mname = f'tags{n_fixup}'
            else:
                mname = f'm_{m.name}'

            out += f'{indent}// Encode {mname} (dynamic width)\n';
            out += f'{indent}wr.serialize<uint64_t>(fixups[{n_fixup}], i);\n'
            out += f'{indent}old_i = i;\n'
            out += self.emit_dynamic_member_encoder(m, depth)
            out += f'{indent}wr.serialize<uint64_t>(fixups[{n_fixup}] + 8, i - old_i);\n'

            n_fixup += 1

        out += f'{indent}return true;\n'
        depth -= 1
        indent = '\t' * depth
        out += f'{indent}}}\n\n'

        return out

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
            flatten((m.members if type(m) is TagsBlock else [m] for m in head.members) if head is not None else []),
            flatten((m.members if type(m) is TagsBlock else [m] for m in tail.members) if tail is not None else [])
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
            out += '\t{} {}() {{\n'.format(self.generate_type(m.type), m.name)
            out += '\t\t{}(p_{});\n'.format(self.stdlib_traits.assert_func(), m.name)
            out += '\t\treturn m_{};\n'.format(m.name)
            out += '\t}\n\n'

            # setter
            out += '\tvoid set_{}({} val) {{\n'.format(m.name, self.generate_type(m.type))
            out += '\t\tp_{} = true;\n'.format(m.name)
            out += '\t\tm_{} = val;\n'.format(m.name)
            out += '\t}\n\n'

        out += self.emit_head_encoder(message)

#        out += self.generate_encoder(message)
#        out += self.generate_decoder(message)

        out += 'private:\n'
        for m in all_members:
            out += '\t{} m_{}; bool p_{};\n'.format(self.generate_type(m.type), m.name,
                    m.name)

        return out + '};\n'
