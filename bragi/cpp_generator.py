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
    def includes(self):
        return ['<stdint.h>', '<stddef.h>', '<vector>', '<cassert>', '<optional>', '<string>']

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
    def includes(self):
        return ['<stdint.h>', '<stddef.h>', '<frg/vector.hpp>', '<frg/macros.hpp>', '<frg/optional.hpp>', '<frg/string.hpp>']

flatten = lambda l: [item for sublist in l for item in sublist]

class CodeGenerator:
    def __init__(self, unit, stdlib, protobuf_compat = False):
        self.unit = unit
        self.protobuf_compat = protobuf_compat
        self.stdlib_traits = None

        if stdlib == 'stdc++':
            self.stdlib_traits = StdlibTraits()
        elif stdlib == 'frigg':
            self.stdlib_traits = FriggTraits()
        else:
            raise AttributeError('invalid standard library')

        self.current_ns = None

    def generate(self):
        out = ''

        for i in self.stdlib_traits.includes():
            out += f'#include {i}\n'

        out += '#include "bragi_internals.hpp"\n\n'

        for thing in self.unit.tokens:
            if type(thing) == NamespaceTag:
                out += self.switch_ns(thing)
            if type(thing) == Enum and thing.mode == "enum":
                out += self.generate_enum(thing)
            if type(thing) == Enum and thing.mode == "consts":
                out += self.generate_consts(thing)
            if type(thing) == Message:
                out += self.generate_message(thing)

        out += self.finalize_ns()

        return out

    def switch_ns(self, ns):
        out = ''

        if self.current_ns != None:
            out += self.finalize_ns()

        out += f'namespace {ns.name} {{\n\n'

        self.current_ns = ns
        return out

    def finalize_ns(self):
        if self.current_ns != None:
            return f'}} // namespace {self.current_ns.name}\n\n'

        return ''

    def generate_consts(self, enum):
        out = f'namespace {enum.name} {{\n'
        i = 0

        for m in enum.members:
            if m.value is not None:
                i = m.value

            assert not enum.type.is_array

            out += f'\tinline constexpr {self.generate_type(enum.type)} {m.name} = {i};\n'

            i += 1

        return out + f'}} // namespace {enum.name}\n\n'

    def generate_enum(self, enum):
        out = f'enum class {enum.name} : int32_t {{\n'
        i = 0

        for m in enum.members:
            if m.value is not None:
                i = m.value

            out += f'\t{m.name} = {i},\n'

            i += 1

        return out + f'}} // enum class {enum.name}\n\n'

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
        else:
            for thing in self.unit.tokens:
                if thing.name != t.base_type:
                    continue

                if type(thing) is Enum and thing.mode == 'consts':
                    base_type_name = self.generate_type(thing.type)
                elif type(thing) is Enum and thing.mode == 'enum':
                    base_type_name = thing.name

        if t.is_array:
            return '{}<{}{}>'.format(self.stdlib_traits.vector(), base_type_name,
                    ', Allocator' if self.stdlib_traits.needs_allocator() else '')
        if t.base_type == 'string':
            return '{}{}'.format(self.stdlib_traits.string(),
                    '<Allocator>' if self.stdlib_traits.needs_allocator() else '')
        else:
            return base_type_name

    def subscript_type(self, t):
        if t.base_type == 'string':
            return 'char'
        return self.generate_type(Type(t.line, t.column, t.base_type))

    def is_simple_integer(self, t):
        return t in ['char', 'int8_t', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t', 'int64_t', 'uint64_t']

    def is_dyn_pointer(self, m):
        return type(m) is TagsBlock or ((m.type.is_array and m.type.array_size == -1) or m.type.base_type == 'string')

    def count_dynamic(self, members):
        i = 0

        for m in members:
            if self.is_dyn_pointer(m): i += 1

        return i

    def emit_stmt_checked(self, stmt, depth = 1):
        indent = '\t' * depth

        out = f'{indent}if (!{stmt})\n'

        depth += 1
        indent = '\t' * depth
        out += f'{indent}return false;\n'

        return out

    def emit_write_varint(self, value, depth = 1):
        return self.emit_stmt_checked(f'sr.write_varint(wr, {value})', depth)

    def emit_write_integer(self, value, depth = 1, type = None):
        assert type
        if self.is_simple_integer(type):
            return self.emit_stmt_checked(f'sr.template write_integer<{type}>(wr, {value})', depth)
        else: # this is an enum, explicitly cast to underlying number type
            return self.emit_stmt_checked(f'sr.template write_integer<int32_t>(wr, static_cast<int32_t>({value}))', depth)

    def emit_write_fixed_array(self, m, depth = 1):
        indent = '\t' * depth
        out = f'{indent}for (size_t i = 0; i < {m.type.array_size}; i++)\n'
        # TODO: write a more generic function to write whatever here?
        out += self.emit_write_integer(f'i < m_{m.name}.size() ? m_{m.name}[i] : 0', depth + 1, self.subscript_type(m.type))

        return out

    def emit_write_dynamic_array(self, m, depth = 1):
        indent = '\t' * depth
        out = self.emit_write_varint(f'm_{m.name}.size()', depth)
        out += f'{indent}for (size_t i = 0; i < m_{m.name}.size(); i++)\n'
        # TODO: write a more generic function to write whatever here?
        out += self.emit_write_integer(f'm_{m.name}[i]', depth + 1, self.subscript_type(m.type))
        return out

    def emit_assert_that(self, stmt, depth = 1):
        indent = '\t' * depth
        return f'{indent}{self.stdlib_traits.assert_func()}({stmt});\n'

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
                if m.type.is_array or m.type.base_type == 'string':
                    out += self.emit_write_dynamic_array(m, depth)
                else:
                    out += self.emit_write_varint(f'm_{m.name}', depth)

                depth -= 1
                indent = '\t' * depth
                out += f'{indent}}}\n'

            out += self.emit_write_varint(0, depth) # terminator tag
        else:
            assert member.type.is_array or member.type.base_type == 'string'
            out += self.emit_write_dynamic_array(member, depth)

        return out + '\n'

    def determine_pointer_size(self, what, size):
        if what != 'head':
            return 8

        if size < 256:
            return 1
        elif size < 65536:
            return 2
        elif size < 4294967296:
            return 4
        elif size < 18446744073709551616:
            return 8
        else:
            return None

    def calculate_fixed_part_size(self, what, members, parent):
        i = 8 if what == 'head' else 0

        ptr_size = self.determine_pointer_size(what, parent.head.size if what == 'head' else None)

        for m in members:
            if not self.is_dyn_pointer(m):
                size = fixed_type_size(self.unit, m.type)
                assert size
                i += size
            else:
                i += ptr_size

        return i

    def emit_determine_dyn_off_for(self, skip, prev, n, depth = 1):
        indent = '\t' * depth
        out = ''
        into = f'dyn_offs[{n}]'

        if n > 0:
            out += f'{indent}{into} = dyn_offs[{n - 1}];\n'
        else:
            out += f'{indent}{into} = {skip};\n'

        if not prev:
            return out + '\n'

        if type(prev) is TagsBlock:
            for m in prev.members:
                out += f'{indent}if ({"p_" + m.name}) {{\n'
                depth += 1
                indent = '\t' * depth

                assert m.tag

                out += f'{indent}{into} += bragi::detail::size_of_varint({m.tag.value});\n'
                if m.type.is_array:
                    out += f'{indent}{into} += bragi::detail::size_of_varint(m_{m.name}.size());\n'
                    out += f'{indent}{into} += {subscript_type_size(m.type)} * m_{m.name}.size();\n'
                else:
                    out += f'{indent}{into} += bragi::detail::size_of_varint(m_{m.name});\n'

                depth -= 1
                indent = '\t' * depth
                out += f'{indent}}}\n'

            out += f'{indent}{into} += bragi::detail::size_of_varint(0);\n'
        else:
            assert prev.type.is_array or prev.type.base_type == 'string'
            out += f'{indent}{into} += bragi::detail::size_of_varint(m_{prev.name}.size());\n'
            out += f'{indent}{into} += {subscript_type_size(prev.type)} * m_{prev.name}.size();\n'

        return out + '\n'

    def determine_pointer_type(self, what, size):
        size = self.determine_pointer_size(what, size)
        if not size:
            return None

        return f'uint{size * 8}_t'

    def emit_part_encoder(self, what, parent, members, depth = 1):
        indent = '\t' * depth

        out = f'{indent}template <typename Writer>\n'
        out += f'{indent}bool encode_{what}(Writer &wr) {{\n'
        depth += 1
        indent = '\t' * depth

        out += f'{indent}bragi::serializer sr;\n'

        fixed_size = self.calculate_fixed_part_size(what, members, parent)
        ptrs = [i for i in members if self.is_dyn_pointer(i)]

        ptr_type = self.determine_pointer_type(what, parent.head.size if what == 'head' else None)

        if len(ptrs) > 0:
            out += f'{indent}{ptr_type} dyn_offs[{len(ptrs)}];\n'

        out += '\n'

        for i, m in enumerate(ptrs):
            out += self.emit_determine_dyn_off_for(fixed_size, ptrs[i - 1] if i > 0 else None, i, depth)

        if what == 'head':
            out += f'{indent}// Encode ID\n'
            out += self.emit_write_integer('message_id', depth, 'uint64_t') + '\n'

        i = 0
        for m in members:
            out += f'{indent}// Encode {"tags" if type(m) is TagsBlock else m.name}\n';
            if self.is_dyn_pointer(m):
                if type(m) is not TagsBlock:
                    out += self.emit_assert_that(f'p_{m.name}', depth)
                out += self.emit_write_integer(f'dyn_offs[{i}]', depth, ptr_type)
                i += 1
            elif m.type.is_array:
                out += self.emit_assert_that(f'p_{m.name}', depth)
                out += self.emit_write_fixed_array(m, depth)
            else:
                out += self.emit_assert_that(f'p_{m.name}', depth)
                out += self.emit_write_integer(f'm_{m.name}', depth, self.generate_type(m.type))
            out += '\n'

        for m in members:
            if not self.is_dyn_pointer(m): continue

            out += f'{indent}// Encode {"tags" if type(m) is TagsBlock else m.name} (dynamic width)\n';
            out += self.emit_dynamic_member_encoder(m, depth)

        out += f'{indent}return true;\n'
        depth -= 1
        indent = '\t' * depth
        out += f'{indent}}}\n\n'

        return out

    def emit_read_integer_into(self, to, type, depth = 1):
        if self.is_simple_integer(type):
            return self.emit_stmt_checked(f'de.read_integer<{type}>(rd, {to})', depth)
        else: # this is an enum, read into an integer and cast to enum type
            indent = '\t' * depth
            out = self.emit_stmt_checked(f'de.read_integer<int32_t>(rd, enum_tmp)', depth)
            out += f'{indent}{to} = static_cast<{type}>(enum_tmp);\n'
            return out

    def emit_read_varint_into(self, to, depth = 1):
        return self.emit_stmt_checked(f'de.read_varint(rd, {to})', depth)

    def emit_set_member(self, member, enabled, depth = 1):
        indent = '\t' * depth
        return f'{indent}p_{member.name} = {"true" if enabled else "false"};\n'

    def emit_loop_resize_read_into(self, m, size, depth = 1):
        indent = '\t' * depth

        target_size = size

        if m.type.array_size != -1 and m.type.is_array:
            target_size = m.type.array_size

        out = f'{indent}m_{m.name}.resize({target_size});\n'
        out += f'{indent}for (size_t i = 0; i < {target_size}; i++)\n'
        if target_size != size:
            depth += 1
            indent = '\t' * depth
            out += f'{indent}if (i < {size})\n'
        out += self.emit_read_integer_into(f'*(m_{m.name}.data() + i)', self.subscript_type(m.type), depth + 1)

        return out

    def emit_decode_dynamic_member(self, m, ptr_type, depth = 1):
        indent = '\t' * depth
        out = self.emit_read_integer_into('ptr', ptr_type, depth)
        out += f'{indent}de.push_index(ptr);\n'

        if type(m) is TagsBlock:
            out += f'{indent}do {{\n'
            depth += 1
            indent = '\t' * depth
            out += f'{indent}uint64_t tmp2;\n'
            out += self.emit_read_varint_into('tmp', depth)
            out += f'{indent}switch(tmp) {{\n'
            depth += 1
            indent = '\t' * depth
            out += f'{indent}case 0:\n{indent}\tbreak;\n'
            for mm in m.members:
                assert mm.tag
                out += f'{indent}case {mm.tag.value}:\n'
                depth += 1
                indent = '\t' * depth

                if mm.type.is_array or mm.type.base_type == 'string':
                    out += self.emit_read_varint_into('tmp2', depth)
                    out += self.emit_loop_resize_read_into(mm, 'tmp2', depth)
                else:
                    # TODO: is this correct w.r.t. signed numbers?
                    out += self.emit_read_varint_into('tmp2', depth)
                    out += f'{indent}m_{mm.name} = static_cast<{self.generate_type(mm.type)}>(tmp2);\n'
                out += self.emit_set_member(mm, True, depth)

                out += f'{indent}break;\n'
                depth -= 1
                indent = '\t' * depth
            out += f'{indent}default:\n'
            out += self.emit_assert_that('!"Unknown tag!"', depth + 1)
            depth -= 1
            indent = '\t' * depth
            out += f'{indent}}}\n'
            depth -= 1
            indent = '\t' * depth
            out += f'{indent}}} while(tmp);\n'
        else:
            out += self.emit_read_varint_into('tmp', depth)
            out += self.emit_loop_resize_read_into(m, 'tmp', depth)
            out += self.emit_set_member(m, True, depth)

        out += f'{indent}de.pop_index();\n'

        return out

    def emit_part_decoder(self, what, parent, members, depth = 1):
        indent = '\t' * depth

        out = f'{indent}template <typename Reader>\n'
        out += f'{indent}bool decode_{what}(Reader &rd) {{\n'
        depth += 1
        indent = '\t' * depth

        out += f'{indent}bragi::deserializer de;\n'
        out += f'{indent}uint64_t tmp;\n'
        out += f'{indent}int32_t enum_tmp;\n'

        ptr_type = self.determine_pointer_type(what, parent.head.size if what == 'head' else None)

        out += f'{indent}{ptr_type} ptr;\n'

        if what == 'head':
            out += f'{indent}// Decode and check ID\n'
            out += self.emit_read_integer_into('tmp', 'uint64_t', depth)
            out += self.emit_assert_that('tmp == message_id', depth)
            out += '\n'

        for m in members:
            out += f'{indent}// Decode {"tags" if type(m) is TagsBlock else m.name}\n';
            if self.is_dyn_pointer(m):
                out += self.emit_decode_dynamic_member(m, ptr_type, depth)
            else:
                if m.type.is_array:
                    assert m.type.array_size > 0
                    out += self.emit_loop_resize_read_into(m, m.type.array_size, depth)
                else:
                    out += self.emit_read_integer_into(f'm_{m.name}', self.generate_type(m.type), depth)
                out += self.emit_set_member(m, True, depth)
            out += '\n'

        out += f'{indent}return true;\n'
        depth -= 1
        indent = '\t' * depth
        out += f'{indent}}}\n\n'

        return out

    # Protobuf compatibilty code
    def emit_serialize_as_string(self, parent, depth = 1):
        indent = '\t' * depth
        out = ''

        if type(self.stdlib_traits) is FriggTraits:
            out = f'{indent}bool SerializeToString(frg::string<Allocator> *str) {{\n'
            depth += 1
            indent = '\t' * depth

            out += f'{indent}str->resize({parent.head.size});\n'
            out += f'{indent}bragi::limited_writer wr{{str->data(), str->size()}};\n\n'
            out += f'{indent}return encode_head(wr);\n'
            depth -= 1
            indent = '\t' * depth

            out += f'{indent}}}\n\n'
        else:
            out = f'{indent}std::string SerializeAsString() {{\n'
            depth += 1
            indent = '\t' * depth

            out += f'{indent}std::string str{{{parent.head.size}, \'\\0\'}};\n'
            out += f'{indent}bragi::limited_writer wr{{str.data(), str.size()}};\n\n'
            out += self.emit_assert_that('encode_head(wr)', depth) + '\n'
            out += f'{indent}return str;\n'
            depth -= 1
            indent = '\t' * depth

            out += f'{indent}}}\n\n'

        return out

    # Protobuf compatibilty code
    def emit_parse_from_array(self, parent, depth = 1):
        indent = '\t' * depth
        out = f'{indent}bool ParseFromArray(const char *data, size_t size) {{\n'
        depth += 1
        indent = '\t' * depth

        out += f'{indent}bragi::limited_reader rd{{data, size}};\n\n'
        out += f'{indent}return decode_head(rd);\n'
        depth -= 1
        indent = '\t' * depth

        out += f'{indent}}}\n\n'

        return out

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
            out += self.emit_part_encoder('head', message, message.head.members)
            out += self.emit_part_decoder('head', message, message.head.members)
        if message.tail:
            out += self.emit_part_encoder('tail', message, message.tail.members)
            out += self.emit_part_decoder('tail', message, message.tail.members)

        if self.protobuf_compat:
            out += self.emit_serialize_as_string(message)
            out += self.emit_parse_from_array(message)

        out += 'private:\n'
        for m in all_members:
            out += '\t{} m_{}; bool p_{};\n'.format(self.generate_type(m.type), m.name,
                    m.name)

        return out + f'}}; // struct {message.name}\n\n'
