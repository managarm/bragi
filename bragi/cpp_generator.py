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
                i = m.value

            assert not enum.type.is_array

            out += f'\tinline constexpr {self.generate_type(enum.type)} {m.name} = {i};\n'

            i += 1

        return out + f'}} // namespace {enum.name}\n'

    def generate_enum(self, enum):
        out = f'enum class {enum.name} {{\n'
        i = 0

        for m in enum.members:
            if m.value is not None:
                i = m.value

            out += f'\t{m.name} = {i},\n'

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

    def is_dyn_pointer(self, m):
        return type(m) is TagsBlock or (m.type.is_array and m.type.array_size == -1)

    def emit_stmt_checked(self, stmt, depth = 1):
        indent = '\t' * depth

        out = f'{indent}if (!{stmt})\n'

        depth += 1
        indent = '\t' * depth
        out += f'{indent}return false;\n'

        return out

    def emit_write_varint(self, value, depth = 1):
        return self.emit_stmt_checked(f'wr.write_varint({value})', depth)

    def emit_write_integer(self, value, depth = 1, vtype = None):
        if vtype:
            return self.emit_stmt_checked(f'wr.write_integer<{vtype}>({value})', depth)
        return self.emit_stmt_checked(f'wr.write_integer({value})', depth)

    def emit_write_fixed_array(self, m, depth = 1):
        return self.emit_stmt_checked(f'wr.write_integer_array(m_{m.name}.data(), m_{m.name}.size(), {m.type.array_size})', depth)

    def emit_write_dynamic_array(self, m, depth = 1):
        out = self.emit_write_varint(f'm_{m.name}.size()', depth)
        out += self.emit_stmt_checked(f'wr.write_integer_array(m_{m.name}.data(), m_{m.name}.size(), m_{m.name}.size())', depth)
        return out

    def emit_assert_that(self, stmt, depth = 1):
        indent = '\t' * depth
        return f'{indent}{self.stdlib_traits.assert_func()}({stmt});\n'

    def emit_write_integer_at(self, offset, value, depth = 1, vtype = None):
        if vtype:
            return self.emit_stmt_checked(f'wr.write_integer_at<{vtype}>({offset}, {value})', depth)
        return self.emit_stmt_checked(f'wr.write_integer_at({offset}, {value})', depth)

    def emit_fixed_member_encoder(self, member, depth = 1):
        indent = '\t' * depth

        out = f'{indent}// Encode {"tags" if type(member) is TagsBlock else member.name}\n';
        if self.is_dyn_pointer(member):
            out += self.emit_write_integer(0, depth, 'uint64_t')
        elif member.type.is_array:
            out += self.emit_assert_that(f'p_{member.name}', depth)
            out += self.emit_write_fixed_array(member, depth)
        else:
            out += self.emit_assert_that(f'p_{member.name}', depth)
            out += self.emit_write_integer(f'm_{member.name}', depth)

        return out + '\n'

    def emit_dynamic_member_encoder(self, member, depth = 1):
        indent = '\t' * depth
        out = ''

        if type(member) is TagsBlock:
            for m in member.members:
                out += f'{indent}if ({"p_" + m.name}) {{\n'
                depth += 1
                indent = '\t' * depth

                assert m.tag

                out += self.emit_write_varint(m.tag.value, depth)
                if m.type.is_array:
                    out += self.emit_write_dynamic_array(m, depth)
                else:
                    out += self.emit_write_integer(f'm_{m.name}', depth)

                depth -= 1
                indent = '\t' * depth
                out += f'{indent}}}\n'

            out += self.emit_write_varint(0, depth) # terminator tag
        else:
            assert member.type.is_array
            out += self.emit_write_dynamic_array(member, depth)

        return out + '\n'

    def emit_part_encoder(self, what, members, depth = 1):
        indent = '\t' * depth

        out = f'{indent}template <typename Writer>\n'
        out += f'{indent}bool encode_{what}(Writer &wr) {{\n'
        depth += 1
        indent = '\t' * depth

        if what == 'head':
            out += f'{indent}// encode ID\n'
            out += self.emit_write_integer('message_id', depth) + '\n'

        for m in members:
            out += self.emit_fixed_member_encoder(m, depth)

        i = 0
        for m in members:
            if not self.is_dyn_pointer(m):
                size = fixed_type_size(m.type)
                assert size
                i += size
                continue

            out += f'{indent}// Encode {"tags" if type(m) is TagsBlock else m.name} (dynamic width)\n';
            out += self.emit_write_integer_at(i, 'wr.index()', depth)
            out += self.emit_dynamic_member_encoder(m, depth)

            i += 8

        out += f'{indent}return true;\n'
        depth -= 1
        indent = '\t' * depth
        out += f'{indent}}}\n\n'

        return out

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

        out += f'struct {message.name} {{\n'
        out += f'\tstatic constexpr uint64_t message_id = {message.id};\n'
        out += f'\tstatic constexpr size_t head_size = {message.head.size};\n\n'

        out += f'\t{message.name}({self.stdlib_traits.allocator_argument()})\n\t: '

        for i, m in enumerate(all_members):
            alloc = self.stdlib_traits.allocator_parameter() if m.type.is_array else ''
            out += f'm_{m.name}{{{alloc}}}, p_{m.name}{{false}}'

            if i < len(all_members) - 1:
                out += ', \n\t  '

        out += ' { }\n\n'

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

        if message.head:
            out += self.emit_part_encoder('head', message.head.members)
        if message.tail:
            out += self.emit_part_encoder('tail', message.tail.members)

#        out += self.generate_encoder(message)
#        out += self.generate_decoder(message)

        out += 'private:\n'
        for m in all_members:
            out += '\t{} m_{}; bool p_{};\n'.format(self.generate_type(m.type), m.name,
                    m.name)

        return out + '};\n'
