from .tokens import *
from .types import *

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
        self.indent_depth = 0
        self.indent = ''

        if stdlib == 'stdc++':
            self.stdlib_traits = StdlibTraits()
        elif stdlib == 'frigg':
            self.stdlib_traits = FriggTraits()
        else:
            raise AttributeError('invalid standard library')

        self.current_ns = None

    def enter_indent(self):
        self.indent_depth += 1
        self.indent = '\t' * self.indent_depth
        return self.indent

    def leave_indent(self):
        self.indent_depth -= 1
        self.indent = '\t' * self.indent_depth
        return self.indent

    def generate(self):
        out = '// This file has been autogenerated, changes *will* be lost eventually...\n'
        out += '#pragma once\n'

        for i in self.stdlib_traits.includes():
            out += f'#include {i}\n'

        out += '#include <bragi/internals.hpp>\n\n'

        for thing in self.unit.tokens:
            if type(thing) == NamespaceTag:
                out += self.switch_ns(thing)
            if type(thing) == UsingTag:
                out += self.generate_using(thing)
            if type(thing) == Enum and thing.mode == "enum":
                out += self.generate_enum(thing)
            if type(thing) == Enum and thing.mode == "consts":
                out += self.generate_consts(thing)
            if type(thing) == Message:
                out += self.generate_message(thing)
            if type(thing) == Struct:
                out += self.generate_struct(thing)

        out += self.finalize_ns()

        return out

    def switch_ns(self, ns):
        out = ''

        if self.current_ns:
            out += self.finalize_ns()

        out += f'namespace {ns.name} {{\n\n'

        self.current_ns = ns
        return out

    def finalize_ns(self):
        if self.current_ns:
            return f'}} // namespace {self.current_ns.name}\n\n'

        return ''

    def generate_consts(self, enum):
        out = f'{self.indent}namespace {enum.name} {{\n'
        i = 0
        self.enter_indent()

        for m in enum.members:
            if m.value is not None:
                i = m.value

            out += f'{self.indent}inline constexpr {self.generate_type(enum.type)} {m.name} = {i};\n'

            i += 1

        self.leave_indent()
        return out + f'{self.indent}}} // namespace {enum.name}\n\n'

    def generate_enum(self, enum):
        out = f'{self.indent}enum class {enum.name} : int32_t {{\n'
        i = 0
        self.enter_indent()

        for m in enum.members:
            if m.value is not None:
                i = m.value

            out += f'{self.indent}{m.name} = {i},\n'

            i += 1

        self.leave_indent()
        return out + f'{self.indent}}}; // enum class {enum.name}\n\n'

    def make_ns_name(self, full):
        a, b, c = full.rpartition('::')

        if b == '':
            return (self.current_ns.name if self.current_ns else '', None, full)

        return (None, a, c)

    def generate_using(self, using):
        from_a, from_b, from_name = self.make_ns_name(using.from_name)
        to_a, to_b, to_name = self.make_ns_name(using.to_name)
        from_ns = from_a if from_a else from_b

        from_full = f'::{from_ns}::{from_name}'

        if not to_a:
            last_ns = self.current_ns
            out = self.finalize_ns()
            self.current_ns = None

            if to_b != '':
                out += f'namespace {to_b} {{\n\n'

            out += f'{self.indent}using {to_name} = {from_full};\n\n'

            if to_b != '':
                out += f'}} // namespace {to_b}\n\n'
            out += self.switch_ns(last_ns)
            return out
        else:
            return f'{self.indent}using {to_name} = {from_full};\n\n'

    def generate_type(self, t):
        if t.identity is TypeIdentity.INTEGER:
            if t.name == 'char':
                return 'char'
            return f'{"u" if not t.signed else ""}int{t.fixed_size * 8}_t'
        elif t.identity is TypeIdentity.CONSTS:
            return self.generate_type(t.subtype)
        elif t.identity is TypeIdentity.ENUM:
            return t.name
        elif t.identity is TypeIdentity.STRING:
            return f'{self.stdlib_traits.string()}{"<Allocator>" if self.stdlib_traits.needs_allocator() else ""}'
        elif t.identity is TypeIdentity.ARRAY:
            return f'{self.stdlib_traits.vector()}<{self.generate_type(t.subtype)}{", Allocator" if self.stdlib_traits.needs_allocator() else ""}>'
        elif t.identity is TypeIdentity.STRUCT:
            return f'{t.name}{"<Allocator>" if self.stdlib_traits.needs_allocator() else ""}'
        else:
            raise RuntimeError('unknown type in generate_type')

    def is_simple_integer(self, t):
        return t in ['char', 'int8_t', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t', 'int64_t', 'uint64_t']

    def is_dyn_pointer(self, m):
        return type(m) is TagsBlock or m.type.dynamic

    def count_dynamic(self, members):
        i = 0

        for m in members:
            if self.is_dyn_pointer(m): i += 1

        return i

    def emit_stmt_checked(self, stmt):
        out = f'{self.indent}if (!{stmt})\n'

        self.enter_indent()
        out += f'{self.indent}return false;\n'
        self.leave_indent()

        return out

    def emit_assert_that(self, stmt):
        return f'{self.indent}{self.stdlib_traits.assert_func()}({stmt});\n'

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
                assert m.type.fixed_size
                i += m.type.fixed_size
            else:
                i += ptr_size

        return i

    def emit_calculate_dynamic_size_of_member(self, into, member):
        if type(member) is TagsBlock:
            out = ''
            for child in member.members:
                out += f'{self.indent}if (p_{child.name}) {{\n'
                self.enter_indent()
                out += f'{self.indent}{into} += bragi::detail::size_of_varint({child.tag.value});\n'
                out += self.emit_calculate_dynamic_size_of_member(into, child)
                self.leave_indent()
                out += f'{self.indent}}}\n\n'
            out += f'{self.indent}{into} += bragi::detail::size_of_varint(0);\n'
            return out
        else:
            return self.emit_calculate_dynamic_size_of_member_internal(into, f'm_{member.name}', member.type, 0)

    def emit_calculate_dynamic_size_of_member_internal(self, into, expr, expr_type, array_depth):
        if expr_type.identity in {TypeIdentity.INTEGER, TypeIdentity.CONSTS}:
            if expr_type.fixed_size == 1:
                return f'{self.indent}{into} += 1;\n'
            return f'{self.indent}{into} += bragi::detail::size_of_varint({expr});\n'
        elif expr_type.identity is TypeIdentity.ENUM:
            return f'{self.indent}{into} += bragi::detail::size_of_varint(static_cast<int32_t>({expr}));\n'
        elif expr_type.identity is TypeIdentity.STRING:
            out = f'{self.indent}{into} += bragi::detail::size_of_varint({expr}.size());\n'
            return out + f'{self.indent}{into} += {expr}.size();\n'
        elif expr_type.identity is TypeIdentity.ARRAY:
            out = f'{self.indent}{into} += bragi::detail::size_of_varint({expr}.size());\n'
            out += f'{self.indent}for (size_t i{array_depth} = 0; i{array_depth} < {expr}.size(); i{array_depth}++) {{\n'
            self.enter_indent()
            out += self.emit_calculate_dynamic_size_of_member_internal(into, f'{expr}[i{array_depth}]', expr_type.subtype, array_depth + 1)
            self.leave_indent()
            return out + f'{self.indent}}}\n'
        elif expr_type.identity is TypeIdentity.STRUCT:
            return f'{self.indent}{into} += {expr}.size_of_body();\n'
        else:
            raise RuntimeError('unexpected member type')

    def emit_determine_dyn_off_for(self, skip, prev, n):
        out = ''
        into = f'dyn_offs[{n}]'

        if n > 0:
            out += f'{self.indent}{into} = dyn_offs[{n - 1}];\n'
        else:
            out += f'{self.indent}{into} = {skip};\n'

        if not prev:
            return out + '\n'
        else:
            return out + self.emit_calculate_dynamic_size_of_member(into, prev) + '\n'

    def emit_calculate_size_of(self, what, members, parent):
        out = f'{self.indent}size_t size_of_{what}() {{\n'
        self.enter_indent()

        out += f'{self.indent}size_t size = {self.calculate_fixed_part_size(what, members, parent)};\n'

        for member in filter(self.is_dyn_pointer, members):
            out += self.emit_calculate_dynamic_size_of_member('size', member)

        out += f'\n{self.indent}return size;\n'

        self.leave_indent()
        out += f'{self.indent}}}\n'

        return out + '\n'

    def emit_struct_calculate_size_of(self, members, parent):
        out = f'{self.indent}size_t size_of_body() {{\n'
        self.enter_indent()

        out += f'{self.indent}size_t size = 0;\n'

        for member in members:
            out += self.emit_calculate_dynamic_size_of_member('size', member)

        out += f'\n{self.indent}return size;\n'

        self.leave_indent()
        out += f'{self.indent}}}\n'

        return out + '\n'

    def emit_stub_calculate_size_of(self, what):
        out = f'{self.indent}size_t size_of_{what}() {{\n'
        self.enter_indent()
        out += f'{self.indent}return {8 if what == "head" else 0};\n'
        self.leave_indent()

        out += f'{self.indent}}}\n'

        return out + '\n'

    def determine_pointer_type(self, what, size):
        size = self.determine_pointer_size(what, size)
        if not size:
            return None

        return f'uint{size * 8}_t'

    class FixedEncoder:
        def __init__(self, parent):
            self.parent = parent
            self.nth_dynamic = 0

        def emit_encode_in_fixed(self, member, ptr_type):
            is_tags = type(member) is TagsBlock
            return self.emit_encode_in_fixed_internal(f'm_{member.name if not is_tags else "tags"}',
                    member.type if not is_tags else None, is_tags, ptr_type, 0)

        def emit_encode_in_fixed_default(self, expr_type, array_depth):
            assert expr_type and not expr_type.dynamic
            if expr_type.identity in {TypeIdentity.INTEGER, TypeIdentity.CONSTS}:
                return self.parent.emit_stmt_checked(f'sr.write_integer<{self.parent.generate_type(expr_type)}>(wr, 0)')
            elif expr_type.identity is TypeIdentity.ENUM:
                return self.parent.emit_stmt_checked(f'sr.write_integer<int32_t>(wr, static_cast<int32_t>(0))')
            elif expr_type.identity is TypeIdentity.ARRAY:
                assert not expr_type.subtype.dynamic
                assert expr_type.n_elements

                out = f'{self.parent.indent}for (size_t i{array_depth} = 0; i{array_depth} < {expr_type.n_elements}; i{array_depth}++) {{\n'
                self.parent.enter_indent()
                out += self.emit_encode_in_fixed_default(expr_type.subtype, array_depth + 1)
                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'

                return out
            else:
                assert member.type.identity not in {TypeIdentity.STRING, TypeIdentity.STRUCT}

        def emit_encode_in_fixed_internal(self, expr, expr_type, is_tags, ptr_type, array_depth):
            if is_tags or expr_type.dynamic:
                out = self.parent.emit_stmt_checked(f'sr.write_integer<{ptr_type}>(wr, dyn_offs[{self.nth_dynamic}])')
                self.nth_dynamic += 1
                return out
            elif expr_type.identity in {TypeIdentity.INTEGER, TypeIdentity.CONSTS}:
                return self.parent.emit_stmt_checked(f'sr.write_integer<{self.parent.generate_type(expr_type)}>(wr, {expr})')
            elif expr_type.identity is TypeIdentity.ENUM:
                return self.parent.emit_stmt_checked(f'sr.write_integer<int32_t>(wr, static_cast<int32_t>({expr}))')
            elif expr_type.identity is TypeIdentity.ARRAY:
                assert not expr_type.subtype.dynamic
                assert expr_type.n_elements

                out = f'{self.parent.indent}for (size_t i{array_depth} = 0; i{array_depth} < {expr_type.n_elements}; i{array_depth}++) {{\n'
                self.parent.enter_indent()
                out += f'{self.parent.indent}if (i{array_depth} < {expr}.size()) {{\n'
                self.parent.enter_indent()
                out += self.emit_encode_in_fixed_internal(f'{expr}[i{array_depth}]', expr_type.subtype, False, None, array_depth + 1)
                self.parent.leave_indent()
                out += f'{self.parent.indent}}} else {{\n'
                self.parent.enter_indent()
                out += self.emit_encode_in_fixed_default(expr_type.subtype, array_depth + 1)
                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'
                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'

                return out
            else:
                raise RuntimeError('unexpected variable type')

    class DynamicEncoder:
        def __init__(self, parent):
            self.parent = parent

        def emit_encode_in_dynamic(self, member):
            if type(member) is TagsBlock:
                out = ''
                for child in member.members:
                    out += f'{self.parent.indent}if (p_{child.name}) {{\n'
                    self.parent.enter_indent()
                    out += self.parent.emit_stmt_checked(f'sr.write_varint(wr, {child.tag.value})')
                    out += self.emit_encode_in_dynamic(child)
                    self.parent.leave_indent()
                    out += f'{self.parent.indent}}}\n\n'
                out += self.parent.emit_stmt_checked(f'sr.write_varint(wr, 0)')
                return out
            else:
                return self.emit_encode_in_dynamic_internal(f'm_{member.name}', member.type, 0)

        def emit_encode_in_dynamic_internal(self, expr, expr_type, array_depth):
            if expr_type.identity in {TypeIdentity.INTEGER, TypeIdentity.CONSTS}:
                if expr_type.fixed_size == 1:
                    return self.parent.emit_stmt_checked(f'sr.write_integer<{self.parent.generate_type(expr_type)}>(wr, {expr})')
                return self.parent.emit_stmt_checked(f'sr.write_varint(wr, static_cast<{self.parent.generate_type(expr_type)}>({expr}))')
            elif expr_type.identity is TypeIdentity.ENUM:
                return self.parent.emit_stmt_checked(f'sr.write_varint(wr, static_cast<int32_t>({expr}))')
            elif expr_type.identity in {TypeIdentity.ARRAY, TypeIdentity.STRING}:
                out = self.parent.emit_stmt_checked(f'sr.write_varint(wr, {expr}.size())')
                out += f'{self.parent.indent}for (size_t i{array_depth} = 0; i{array_depth} < {expr}.size(); i{array_depth}++) {{\n'
                self.parent.enter_indent()
                out += self.emit_encode_in_dynamic_internal(f'{expr}[i{array_depth}]', expr_type.subtype, array_depth + 1)
                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'

                return out
            elif expr_type.identity is TypeIdentity.STRUCT:
                return self.parent.emit_stmt_checked(f'{expr}.encode_body(wr, sr)')
            else:
                raise RuntimeError('unexpected variable type')

    def emit_part_encoder(self, what, parent, members):
        out = f'{self.indent}template <typename Writer>\n'
        out += f'{self.indent}bool encode_{what}(Writer &wr) {{\n'
        self.enter_indent()

        out += f'{self.indent}bragi::serializer sr; (void)sr;\n'

        fixed_size = self.calculate_fixed_part_size(what, members, parent) if members else None
        ptrs = [i for i in members if self.is_dyn_pointer(i)] if members else None
        ptr_type = self.determine_pointer_type(what, parent.head.size if what == 'head' else None) if parent else None

        if ptrs:
            if len(ptrs) > 0:
                out += f'{self.indent}{ptr_type} dyn_offs[{len(ptrs)}];\n'

        out += '\n'

        if ptrs:
            for i, m in enumerate(ptrs):
                out += self.emit_determine_dyn_off_for(fixed_size, ptrs[i - 1] if i > 0 else None, i)

        if what == 'head':
            out += f'{self.indent}// Encode ID\n'
            out += self.emit_stmt_checked(f'sr.template write_integer<uint32_t>(wr, message_id)')

            out += f'{self.indent}// Encode tail size\n'
            out += self.emit_stmt_checked(f'sr.template write_integer<uint32_t>(wr, size_of_tail())')

        if members:
            fixed_enc = self.FixedEncoder(self)
            dyn_enc = self.DynamicEncoder(self)
            for m in members:
                out += fixed_enc.emit_encode_in_fixed(m, ptr_type) + '\n'

            for m in ptrs:
                out += dyn_enc.emit_encode_in_dynamic(m)

        out += f'{self.indent}return true;\n'
        self.leave_indent()
        out += f'{self.indent}}}\n\n'

        return out

    def emit_struct_encoder(self, parent, members):
        out = f'{self.indent}template <typename Writer>\n'
        out += f'{self.indent}bool encode_body(Writer &wr, bragi::serializer &sr) {{\n'
        self.enter_indent()

        out += f'{self.indent}(void)sr;\n'
        out += '\n'

        dyn_enc = self.DynamicEncoder(self)
        for m in members:
            out += dyn_enc.emit_encode_in_dynamic(m)

        out += f'{self.indent}return true;\n'
        self.leave_indent()
        out += f'{self.indent}}}\n\n'

        return out

    class Decoder:
        def __init__(self, parent):
            self.parent = parent

        def emit_decode_member(self, member, ptr_type):
            if type(member) is TagsBlock or member.type.dynamic:
                out = self.parent.emit_stmt_checked(f'de.read_integer<{ptr_type}>(rd, ptr)')
                out += f'{self.parent.indent}de.push_index(ptr);\n'
                out += self.emit_decode_dynamic(member)
                out += f'{self.parent.indent}de.pop_index();\n'
                return out
            else:
                out = self.emit_decode_fixed_internal(f'm_{member.name}', member.type, 0)
                out += f'{self.parent.indent}p_{member.name} = true;\n'
                return out

        def emit_decode_fixed_internal(self, expr, expr_type, array_depth):
            assert not expr_type.dynamic
            if expr_type.identity in {TypeIdentity.INTEGER, TypeIdentity.CONSTS}:
                out = self.parent.emit_stmt_checked(f'de.read_integer<{self.parent.generate_type(expr_type)}>(rd, {expr})')
                return out
            elif expr_type.identity is TypeIdentity.ENUM:
                out = f'{self.parent.indent}{{\n'
                self.parent.enter_indent()
                out += f'{self.parent.indent}int32_t tmp;\n'
                out += self.parent.emit_stmt_checked(f'de.read_integer<int32_t>(rd, tmp)')
                out += f'{self.parent.indent}{expr} = static_cast<{self.parent.generate_type(expr_type)}>(tmp);\n'
                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'
                return out
            elif expr_type.identity is TypeIdentity.ARRAY:
                assert not expr_type.subtype.dynamic
                assert expr_type.n_elements

                out = ''

                if expr_type.subtype.dynamic and self.parent.stdlib_traits.needs_allocator():
                    out = f'{self.parent.indent}{expr}.resize({expr_type.n_elements}, allocator);\n'
                else:
                    out = f'{self.parent.indent}{expr}.resize({expr_type.n_elements});\n'

                out += f'{self.parent.indent}for (size_t i{array_depth} = 0; i{array_depth} < {expr_type.n_elements}; i{array_depth}++) {{\n'
                self.parent.enter_indent()
                out += self.emit_decode_fixed_internal(f'{expr}[i{array_depth}]', expr_type.subtype, array_depth + 1)
                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'

                return out
            else:
                raise RuntimeError('unexpected variable type')

        def emit_decode_dynamic(self, member):
            if type(member) is TagsBlock:
                out = f'{self.parent.indent}{{\n'
                self.parent.enter_indent()
                out += f'{self.parent.indent}uint64_t tag;\n'

                out += f'{self.parent.indent}do {{\n'
                self.parent.enter_indent()
                out += self.parent.emit_stmt_checked(f'de.read_varint(rd, tag)')

                out += f'{self.parent.indent}switch (tag) {{\n'
                self.parent.enter_indent()

                out += f'{self.parent.indent}case 0: break;\n'

                for child in member.members:
                    out += f'{self.parent.indent}case {child.tag.value}:\n'
                    self.parent.enter_indent()
                    out += self.emit_decode_dynamic_internal(f'm_{child.name}', child.type, 0)
                    out += f'{self.parent.indent}p_{child.name} = true;\n'
                    out += f'{self.parent.indent}break;\n'
                    self.parent.leave_indent()

                out += f'{self.parent.indent}default:\n'
                self.parent.enter_indent()
                out += self.parent.emit_assert_that('!"Unknown tag!"')
                self.parent.leave_indent()

                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'
                self.parent.leave_indent()
                out += f'{self.parent.indent}}} while (tag);\n'

                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'
                return out
            else:
                out = self.emit_decode_dynamic_internal(f'm_{member.name}', member.type, 0)
                out += f'{self.parent.indent}p_{member.name} = true;\n'
                return out

        def emit_decode_dynamic_internal(self, expr, expr_type, array_depth):
            if expr_type.identity in {TypeIdentity.INTEGER, TypeIdentity.CONSTS, TypeIdentity.ENUM}:
                if expr_type.fixed_size == 1:
                    return self.parent.emit_stmt_checked(f'de.read_integer<{self.parent.generate_type(expr_type)}>(rd, {expr})')

                out = f'{self.parent.indent}{{\n'
                self.parent.enter_indent()
                out += f'{self.parent.indent}uint64_t tmp;\n'
                out += self.parent.emit_stmt_checked(f'de.read_varint(rd, tmp)')
                out += f'{self.parent.indent}{expr} = static_cast<{self.parent.generate_type(expr_type)}>(tmp);\n'
                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'
                return out
            elif expr_type.identity in {TypeIdentity.STRING, TypeIdentity.ARRAY}:
                out = f'{self.parent.indent}{{\n'
                self.parent.enter_indent()
                out += f'{self.parent.indent}uint64_t size;\n'
                out += self.parent.emit_stmt_checked(f'de.read_varint(rd, size)')

                target_size = 'size'

                if expr_type.identity is TypeIdentity.ARRAY and expr_type.n_elements:
                    target_size = expr_type.n_elements

                if expr_type.subtype.dynamic and self.parent.stdlib_traits.needs_allocator():
                    out += f'{self.parent.indent}{expr}.resize({target_size}, allocator);\n'
                else:
                    out += f'{self.parent.indent}{expr}.resize({target_size});\n'
                out += f'{self.parent.indent}for (size_t i{array_depth} = 0; i{array_depth} < {target_size}; i{array_depth}++)\n'
                if target_size != 'size':
                    self.parent.enter_indent()
                    out += f'{self.parent.indent}if (i{array_depth} < size)\n'

                self.parent.enter_indent()
                out += self.emit_decode_dynamic_internal(f'{expr}[i{array_depth}]', expr_type.subtype, array_depth + 1)
                self.parent.leave_indent()

                if target_size != 'size':
                    self.parent.leave_indent()

                self.parent.leave_indent()
                out += f'{self.parent.indent}}}\n'

                return out
            elif expr_type.identity is TypeIdentity.STRUCT:
                return self.parent.emit_stmt_checked(f'{expr}.decode_body(rd, de)')
            else:
                raise RuntimeError('unexpected variable type')

    def emit_part_decoder(self, what, parent, members):
        out = f'{self.indent}template <typename Reader>\n'
        out += f'{self.indent}bool decode_{what}(Reader &rd) {{\n'
        self.enter_indent()

        out += f'{self.indent}bragi::deserializer de; (void)de;\n'

        if members:
            ptr_type = self.determine_pointer_type(what, parent.head.size if what == 'head' else None)
            out += f'{self.indent}{ptr_type} ptr; (void)ptr;\n'

        if what == 'head':
            out += f'{self.indent}{{\n'
            self.enter_indent()
            out += f'{self.indent}uint32_t tmp;\n'
            out += f'{self.indent}// Decode and check ID\n'
            out += self.emit_stmt_checked(f'de.read_integer<uint32_t>(rd, tmp)')
            out += self.emit_stmt_checked('(tmp == message_id)')
            out += '\n'

            out += f'{self.indent}// Decode and ignore tail size\n'
            out += self.emit_stmt_checked(f'de.read_integer<uint32_t>(rd, tmp)')
            self.leave_indent()
            out += f'{self.indent}}}\n'
            out += '\n'

        dec = self.Decoder(self)

        if members:
            ptr_type = self.determine_pointer_type(what, parent.head.size if what == 'head' else None)

            for m in members:
                out += dec.emit_decode_member(m, ptr_type)
                out += '\n'

        out += f'{self.indent}return true;\n'
        self.leave_indent()
        out += f'{self.indent}}}\n\n'

        return out

    def emit_struct_decoder(self, parent, members):
        out = f'{self.indent}template <typename Reader>\n'
        out += f'{self.indent}bool decode_body(Reader &rd, bragi::deserializer &de) {{\n'
        self.enter_indent()

        out += f'{self.indent}(void)de;'
        out += '\n'

        dec = self.Decoder(self)

        for m in members:
            out += dec.emit_decode_dynamic(m)
            out += '\n'

        out += f'{self.indent}return true;\n'
        self.leave_indent()
        out += f'{self.indent}}}\n\n'

        return out

    # Protobuf compatibilty code
    def emit_serialize_as_string(self, parent):
        out = ''

        if type(self.stdlib_traits) is FriggTraits:
            out = f'{self.indent}void SerializeToString(frg::string<Allocator> *str) {{\n'
            self.enter_indent()

            out += f'{self.indent}str->resize({parent.head.size});\n'
            out += f'{self.indent}bragi::limited_writer wr{{str->data(), str->size()}};\n\n'
            out += self.emit_assert_that('encode_head(wr)')

            self.leave_indent()
            out += f'{self.indent}}}\n\n'
        else:
            out = f'{self.indent}std::string SerializeAsString() {{\n'
            self.enter_indent()

            out += f'{self.indent}std::string str(size_t({parent.head.size}), \'\\0\');\n'
            out += f'{self.indent}bragi::limited_writer wr{{str.data(), str.size()}};\n\n'
            out += self.emit_assert_that('encode_head(wr)') + '\n'
            out += f'{self.indent}return str;\n'
            self.leave_indent()

            out += f'{self.indent}}}\n\n'

        return out

    # Protobuf compatibilty code
    def emit_parse_from_array(self, parent):
        out = f'{self.indent}bool ParseFromArray(const void *data, size_t size) {{\n'
        self.enter_indent()

        out += f'{self.indent}bragi::limited_reader rd{{data, size}};\n\n'
        out += f'{self.indent}return decode_head(rd);\n'

        self.leave_indent()

        out += f'{self.indent}}}\n\n'

        return out

    def emit_accessors(self, members):
        out = ''

        for m in members:
            # getters
            ref = '&' if m.type.identity not in {TypeIdentity.INTEGER, TypeIdentity.CONSTS, TypeIdentity.ENUM} else ''

            out += f'{self.indent}{self.generate_type(m.type)} {ref}{m.name}() {{\n'
            self.enter_indent()
            out += f'{self.indent}return m_{m.name};\n'
            self.leave_indent()
            out += f'{self.indent}}}\n\n'

            if m.type.identity is TypeIdentity.ARRAY:
                ref = '&' if m.type.subtype.identity not in {TypeIdentity.INTEGER, TypeIdentity.CONSTS, TypeIdentity.ENUM} else ''

                out += f'{self.indent}{self.generate_type(m.type.subtype)} {ref}{m.name}(size_t i) {{\n'
                self.enter_indent()
                out += f'{self.indent}return m_{m.name}[i];\n'
                self.leave_indent()
                out += f'{self.indent}}}\n\n'

                out += f'{self.indent}size_t {m.name}_size() {{\n'
                self.enter_indent()
                out += f'{self.indent}return m_{m.name}.size();\n'
                self.leave_indent()
                out += f'{self.indent}}}\n\n'

            # setters
            out += f'{self.indent}void set_{m.name}({self.generate_type(m.type)} val) {{\n'
            self.enter_indent()
            out += f'{self.indent}p_{m.name} = true;\n'
            out += f'{self.indent}m_{m.name} = val;\n'
            self.leave_indent()
            out += f'{self.indent}}}\n\n'

            if m.type.identity is TypeIdentity.ARRAY:
                out += f'{self.indent}void set_{m.name}(size_t i, {self.generate_type(m.type.subtype)} val) {{\n'
                self.enter_indent()
                out += f'{self.indent}p_{m.name} = true;\n'
                out += f'{self.indent}m_{m.name}[i] = val;\n'
                self.leave_indent()
                out += f'{self.indent}}}\n\n'

                out += f'{self.indent}void add_{m.name}({self.generate_type(m.type.subtype)} v) {{\n'
                self.enter_indent()
                out += f'{self.indent}p_{m.name} = true;\n'
                out += f'{self.indent}m_{m.name}.push_back(v);\n'
                self.leave_indent()
                out += f'{self.indent}}}\n\n'

        return out

    def emit_constructor(self, name, members):
        out = f'{self.indent}{name}({self.stdlib_traits.allocator_argument()})'

        if len(members) > 0 or self.stdlib_traits.needs_allocator():
            out += f'\n{self.indent}: '
            for i, m in enumerate(members):
                alloc = self.stdlib_traits.allocator_parameter() if m.type.dynamic else ''
                out += f'm_{m.name}{{{alloc}}}, p_{m.name}{{false}}'

                if i < len(members) - 1 or self.stdlib_traits.needs_allocator():
                    out += f', \n{self.indent}  '

        if self.stdlib_traits.needs_allocator():
            out += f'allocator{{{self.stdlib_traits.allocator_parameter()}}}'

        out += ' { }\n\n'

        return out

    def emit_class_members(self, members):
        out = ''

        if len(members):
            self.leave_indent()
            out += f'{self.indent}private:\n'
            self.enter_indent()
            for m in members:
                out += f'{self.indent}{self.generate_type(m.type)} m_{m.name}; bool p_{m.name};\n'

        if self.stdlib_traits.needs_allocator():
            out += f'{self.indent}Allocator allocator;'

        return out

    def generate_message(self, message):
        all_members = flatten([
            flatten((m.members if type(m) is TagsBlock else [m] for m in message.head.members) if message.head is not None else []),
            flatten((m.members if type(m) is TagsBlock else [m] for m in message.tail.members) if message.tail is not None else [])
        ])

        out = ''
        if self.stdlib_traits.needs_allocator():
            out += f'{self.indent}template <typename Allocator>\n'

        out += f'{self.indent}struct {message.name} {{\n'
        self.enter_indent()
        out += f'{self.indent}static constexpr uint32_t message_id = {message.id};\n'
        out += f'{self.indent}static constexpr size_t head_size = {message.head.size};\n\n'

        out += self.emit_constructor(message.name, all_members)
        out += self.emit_accessors(all_members)

        if message.head:
            out += self.emit_calculate_size_of('head', message.head.members, message)
            out += self.emit_part_encoder('head', message, message.head.members)
            out += self.emit_part_decoder('head', message, message.head.members)
        else:
            out += self.emit_stub_calculate_size_of('head')
            out += self.emit_part_encoder('head', None, None)
            out += self.emit_part_decoder('head', None, None)
        if message.tail:
            out += self.emit_calculate_size_of('tail', message.tail.members, message)
            out += self.emit_part_encoder('tail', message, message.tail.members)
            out += self.emit_part_decoder('tail', message, message.tail.members)
        else:
            out += self.emit_stub_calculate_size_of('tail')
            out += self.emit_part_encoder('tail', None, None)
            out += self.emit_part_decoder('tail', None, None)

        if self.protobuf_compat:
            out += self.emit_serialize_as_string(message)
            out += self.emit_parse_from_array(message)

        out += self.emit_class_members(all_members)

        self.leave_indent()

        return out + f'{self.indent}}}; // struct {message.name}\n\n'

    def generate_struct(self, struct):
        all_members = flatten([
            flatten((m.members if type(m) is TagsBlock else [m] for m in struct.members))
        ])

        out = ''
        if self.stdlib_traits.needs_allocator():
            out += f'{self.indent}template <typename Allocator>\n'

        out += f'{self.indent}struct {struct.name} {{\n'
        self.enter_indent()

        out += self.emit_constructor(struct.name, all_members)
        out += self.emit_accessors(all_members)

        out += self.emit_struct_calculate_size_of(struct.members, struct)
        out += self.emit_struct_encoder(struct, struct.members)
        out += self.emit_struct_decoder(struct, struct.members)

        out += self.emit_class_members(all_members)

        self.leave_indent()

        return out + f'{self.indent}}}; // struct {struct.name}\n\n'
