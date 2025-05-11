from .tokens import *
from .types import *


IO_RESULT = "std::io::Result<()>"
WRTIER_GENERIC = "std::io::Write"
READER_GENERIC = "std::io::Read + std::io::Seek"


def flatten(l):
    return [item for sublist in l for item in sublist]


def snake_case(name: str, ) -> str:
    if not any(c.isupper() for c in name):
        result = name
    else:
        result = "".join("_" + c.lower() if c.isupper()
                         else c for c in name).lstrip("_")

    return result


def escape_keyword(name: str) -> str:
    if name in ("type", "struct", "enum", "impl", "const"):
        return f"{name}_"

    return name


def camel_case(name: str) -> str:
    if "_" not in name:
        return name.capitalize()

    return "".join(word.capitalize() for word in name.split("_"))


class DynamicEncoder:
    def __init__(self, parent):
        self.parent = parent

    def generate_encode_in_dynamic(self, expr, member):
        if isinstance(member, TagsBlock):
            out = ""

            for child in member.members:
                child_name = snake_case(child.name)
                child_name = escape_keyword(child_name)

                expr = f"self.{child_name}"

                if child.type.identity in (
                    TypeIdentity.STRING,
                    TypeIdentity.ARRAY,
                    TypeIdentity.STRUCT,
                ):
                    expr = f"{expr}.as_ref()"

                out += self.parent.line(f"if let Some(value) = {expr} {{")

                self.parent.indent()

                out += self.parent.line(
                    f"writer.write_varint({child.tag.value}u64)?;")

                out += self.generate_encode_in_dynamic(f"value", child, False)

                self.parent.dedent()

                out += self.parent.line("}")

            return out + self.parent.line(f"writer.write_varint(0u64)?;")
        else:
            return self.generate_encode_in_dynamic_internal(expr, member.type)

    def generate_encode_in_dynamic_internal(self, expr, expr_type):
        if expr_type.identity == TypeIdentity.INTEGER:
            return self.parent.line(
                f"writer.write_integer::<{self.parent.generate_type(expr_type)}>({expr})?;")
        elif expr_type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            format_attr = expr_type.attributes.get("format")
            is_bitfield = format_attr and format_attr.value == "bitfield"

            if is_bitfield:
                return self.parent.line(
                    f"writer.write_varint({expr}.bits() as u64)?;")

            is_signed = expr_type.subtype.signed
            subtype_size = expr_type.subtype.fixed_size
            value_expr = f"{expr}"

            if expr_type.identity == TypeIdentity.CONSTS:
                value_expr = f"{value_expr}.value()"

            if subtype_size < 8:
                type_prefix = "i" if is_signed else "u"
                value_expr = f"{value_expr} as {type_prefix}64"

            if is_signed:
                value_expr = f"{value_expr} as u64"

            return self.parent.line(f"writer.write_varint({value_expr})?;")
        elif expr_type.identity is TypeIdentity.STRING:
            if expr.startswith("self."):
                expr = f"&{expr}"

            return self.parent.line(f"writer.write_string({expr})?;")
        elif expr_type.identity is TypeIdentity.ARRAY:
            out = self.parent.line("{")

            self.parent.indent()

            out += self.parent.line(
                f"writer.write_varint({expr}.len() as u64)?;")

            out += self.parent.line(f"for item in {expr}.iter() {{")

            self.parent.indent()

            item_expr = f"item"

            if expr_type.subtype.identity in (
                TypeIdentity.ENUM,
                TypeIdentity.CONSTS,
                TypeIdentity.INTEGER,
            ):
                item_expr = f"*{item_expr}"

            out += self.generate_encode_in_dynamic_internal(
                item_expr, expr_type.subtype)

            self.parent.dedent()

            out += self.parent.line("}")

            self.parent.dedent()

            return out + self.parent.line("}")
        elif expr_type.identity is TypeIdentity.STRUCT:
            if expr.startswith("self."):
                expr = f"&{expr}"

            return self.parent.line(f"writer.write_struct({expr})?;")
        else:
            raise RuntimeError(
                f"Unexpected variable type identity: {expr_type.identity}")


class Decoder:
    def __init__(self, parent):
        self.parent = parent

    def generate_decode_member(self, expr, member, ptr_type):
        out = ""

        if isinstance(member, TagsBlock) or member.type.dynamic:
            out += self.parent.line("{")

            self.parent.indent()

            out += self.parent.line(
                f"let ptr = reader.read_integer::<{ptr_type}>()?;")
            out += self.parent.line(f"let prev_offset = reader.offset()?;")
            out += self.parent.line(
                f"reader.seek(ptr{' as u64' if ptr_type != 'u64' else ''})?;")
            out += self.generate_decode_dynamic(expr, member)
            out += self.parent.line(f"reader.seek(prev_offset)?;")

            self.parent.dedent()

            out += self.parent.line("}")
        else:
            member_name = snake_case(member.name)
            out = self.generate_decode_fixed_internal(
                f"self.set_{member_name}", member.type)

        return out

    def generate_decode_fixed_internal(self, setter, expr_type, by_index=False):
        if expr_type.dynamic:
            raise RuntimeError("Unexpected dynamic variable type")

        def set_value(value):
            if by_index:
                return f"{setter} = {value};"

            return f"{setter}({value});"

        if expr_type.identity == TypeIdentity.INTEGER:
            return self.parent.line(set_value(
                f"reader.read_integer::<{self.parent.generate_type(expr_type)}>()?"))
        elif expr_type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            out = ""

            subtype = self.parent.generate_type(expr_type.subtype)
            format_attr = expr_type.attributes.get("format")
            is_bitfield = format_attr and format_attr.value == "bitfield"

            out += self.parent.line(
                f"let tmp = reader.read_integer::<{subtype}>()?;")

            if is_bitfield:
                out += self.parent.line(set_value(
                    f"unsafe {{ {expr_type.name}::new(tmp) }}"))
            elif expr_type.identity == TypeIdentity.CONSTS:
                out += self.parent.line(
                    set_value(f"{expr_type.name}::from(tmp)"))
            else:
                out += self.parent.line(set_value(
                    f"{expr_type.name}::try_from(tmp).unwrap()"))

            return out
        elif expr_type.identity is TypeIdentity.STRING:
            return self.parent.line(set_value(f"reader.read_string()?"))
        elif expr_type.identity is TypeIdentity.ARRAY:
            if not expr_type.n_elements:
                raise RuntimeError("Unexpected dynamic variable type")

            if expr_type.subtype.dynamic:
                raise RuntimeError("Unexpected dynamic variable type")

            out = self.parent.line("{")

            self.parent.indent()

            array_type = f"[{self.parent.generate_type(expr_type.subtype)}; {expr_type.n_elements}]"

            out += self.parent.line(
                f"let mut tmp: {array_type} = bragi::array_init(|_| Default::default());")

            out += self.parent.line(f"for item in tmp.iter_mut() {{")

            self.parent.indent()

            out += self.generate_decode_fixed_internal(
                "*item", expr_type.subtype, True)

            self.parent.dedent()

            out += self.parent.line("}")
            out += self.parent.line(set_value("tmp"))

            self.parent.dedent()

            return out + self.parent.line("}")
        else:
            raise RuntimeError("Unexpected variable type")

    def generate_decode_dynamic(self, expr, member):
        out = ""

        if isinstance(member, TagsBlock):
            out += self.parent.line("loop {")

            self.parent.indent()

            out += self.parent.line(f"match reader.read_varint()? {{")

            self.parent.indent()

            out += self.parent.line("0 => break,")

            for child in member.members:
                out += self.parent.line(
                    f"{child.tag.value} => {{")

                self.parent.indent()

                child_name = snake_case(child.name)

                out += self.generate_decode_dynamic_internal(
                    f"self.set_{child_name}", child.type, 0)

                self.parent.dedent()

                out += self.parent.line("}")

            out += self.parent.line(
                "_ => return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, \"Unknown tag\")),")

            self.parent.dedent()

            out += self.parent.line("}")

            self.parent.dedent()

            return out + self.parent.line("}")
        else:
            member_name = snake_case(member.name)

            return self.generate_decode_dynamic_internal(
                f'self.set_{member_name}', member.type, 0)

    def generate_decode_dynamic_internal(self, setter, expr_type, array_depth, by_index=False):
        def set_value(value):
            if by_index:
                return f"{setter} = {value};"

            return f"{setter}({value});"

        if expr_type.identity == TypeIdentity.INTEGER:
            if expr_type.fixed_size == 1:
                return self.parent.line(set_value(
                    f"reader.read_integer::<u8>()?"))

            is_signed = expr_type.signed
            subtype_size = expr_type.fixed_size
            value_expr = f"reader.read_varint()?"

            if is_signed:
                value_expr = f"{value_expr} as i64"

            if subtype_size < 8:
                type_prefix = "i" if is_signed else "u"
                value_expr = f"{value_expr} as {type_prefix}{subtype_size * 8}"

            return self.parent.line(set_value(value_expr))
        elif expr_type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            is_signed = expr_type.subtype.signed
            subtype_size = expr_type.subtype.fixed_size
            value_expr = f"reader.read_varint()?"

            if is_signed:
                value_expr = f"{value_expr} as i64"

            if subtype_size < 8:
                type_prefix = "i" if is_signed else "u"
                value_expr = f"{value_expr} as {type_prefix}{subtype_size * 8}"

            format_attr = expr_type.attributes.get("format")
            is_bitfield = format_attr and format_attr.value == "bitfield"

            if is_bitfield:
                return self.parent.line(set_value(
                    f"unsafe {{ {expr_type.name}::new({value_expr}) }}"))
            else:
                return self.parent.line(set_value(
                    f"{expr_type.name}::try_from({value_expr}).unwrap()"))
        elif expr_type.identity is TypeIdentity.STRING:
            return self.parent.line(set_value(f"reader.read_string()?"))
        elif expr_type.identity is TypeIdentity.ARRAY:
            out = self.parent.line("{")

            self.parent.indent()

            out += self.parent.line(
                f"let size = reader.read_varint()? as usize;")

            items_var = f"items{array_depth if array_depth > 0 else ''}"

            if expr_type.n_elements:
                array_type = f"[{self.parent.generate_type(expr_type.subtype)}; {expr_type.n_elements}]"

                out += self.parent.line(
                    f"let mut {items_var}: {array_type} = bragi::array_init(|_| Default::default());")
            else:
                out += self.parent.line(
                    f"let mut {items_var} = Vec::with_capacity(size);")

            index = "i" if expr_type.n_elements else "_"
            out += self.parent.line(f"for {index} in 0..size {{")

            self.parent.indent()

            if expr_type.n_elements:
                out += self.generate_decode_dynamic_internal(
                    f"{items_var}[{index}]", expr_type.subtype, array_depth + 1, True)
            else:
                out += self.generate_decode_dynamic_internal(
                    f"{items_var}.push", expr_type.subtype, array_depth + 1)

            self.parent.dedent()

            out += self.parent.line("}")

            out += self.parent.line(set_value(items_var))

            self.parent.dedent()

            return out + self.parent.line("}")
        elif expr_type.identity is TypeIdentity.STRUCT:
            out = self.parent.line("{")

            self.parent.indent()

            out += self.parent.line(
                f"let mut tmp = {expr_type.name}::default();")
            out += self.parent.line(f"reader.read_struct(&mut tmp)?;")
            out += self.parent.line(set_value(f"tmp"))

            self.parent.dedent()

            return out + self.parent.line("}")
        else:
            raise RuntimeError(
                f"Unexpected variable type identity: {expr_type.identity}")


class FixedEncoder:
    def __init__(self, parent):
        self.parent = parent
        self.nth_dynamic = 0

    def generate_encode_in_fixed(self, member, ptr_type):
        is_tags = isinstance(member, TagsBlock)
        expr = ""

        if not is_tags:
            member_name = snake_case(member.name)
            member_name = escape_keyword(member_name)

            expr = f"self.{member_name}"

            if self.parent.is_type_optional(member.type):
                expr = f"{expr}.unwrap()"

        return self.generate_encode_in_fixed_internal(
            expr, member.type if not is_tags else None, is_tags, ptr_type)

    def generate_encode_in_fixed_default(self, expr_type):
        if expr_type.identity in (TypeIdentity.INTEGER, TypeIdentity.CONSTS):
            return self.parent.line(f"writer.write_integer::<{self.parent.generate_type(expr_type)}>(0)?;")
        elif expr_type.identity is TypeIdentity.ENUM:
            return self.parent.line(f"writer.write_integer::<i32>(0)?;")
        elif expr_type.identity is TypeIdentity.ARRAY:
            out = self.parent.line(f"for _ in 0..{expr_type.n_elements} {{")

            self.parent.indent()

            out += self.generate_encode_in_fixed_default(expr_type.subtype)

            self.parent.dedent()

            return out + self.parent.line("}")
        else:
            raise RuntimeError("Unexpected variable type")

    def generate_encode_in_fixed_internal(self, expr, expr_type, is_tags, ptr_type):
        if is_tags or expr_type.dynamic:
            out = self.parent.line(
                f"writer.write_integer::<{ptr_type}>(dyn_offsets[{self.nth_dynamic}])?;")

            self.nth_dynamic += 1

            return out
        elif expr_type.identity == TypeIdentity.INTEGER:
            return self.parent.line(
                f"writer.write_integer::<{self.parent.generate_type(expr_type)}>({expr})?;")
        elif expr_type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            format_attr = expr_type.attributes.get("format")
            is_bitfield = format_attr and format_attr.value == "bitfield"
            is_signed = expr_type.subtype.signed

            if is_bitfield:
                return self.parent.line(f"writer.write_integer(({expr}).bits())?;")

            subtype = self.parent.generate_type(expr_type.subtype)
            expr = f"{expr}"

            if expr_type.identity == TypeIdentity.CONSTS:
                expr = f"({expr}).value()"

            return self.parent.line(
                f"writer.write_integer::<{subtype}>({expr} as {subtype})?;")
        elif expr_type.identity is TypeIdentity.ARRAY:
            out = self.parent.line(f"for item in {expr}.iter() {{")

            self.parent.indent()

            item_expr = f"item"

            if expr_type.subtype.identity in (
                TypeIdentity.ENUM,
                TypeIdentity.CONSTS,
                TypeIdentity.INTEGER,
            ):
                item_expr = f"*{item_expr}"

            out += self.generate_encode_in_fixed_internal(
                item_expr, expr_type.subtype, False, None)

            self.parent.dedent()

            return out + self.parent.line("}")
        else:
            raise RuntimeError('unexpected variable type')


class DynamicEncoder:
    def __init__(self, parent):
        self.parent = parent

    def generate_encode_in_dynamic(self, expr, member, is_option):
        if isinstance(member, TagsBlock):
            out = ""

            for child in member.members:
                child_name = snake_case(child.name)
                child_name = escape_keyword(child_name)

                expr = f"self.{child_name}"

                if child.type.identity in (
                    TypeIdentity.STRING,
                    TypeIdentity.ARRAY,
                    TypeIdentity.STRUCT,
                ):
                    expr = f"{expr}.as_ref()"

                out += self.parent.line(
                    f"if let Some(value) = {expr} {{")

                self.parent.indent()

                out += self.parent.line(
                    f"writer.write_varint({child.tag.value}u64)?;")

                out += self.generate_encode_in_dynamic("value", child, False)

                self.parent.dedent()

                out += self.parent.line("}")

            return out + self.parent.line(f"writer.write_varint(0u64)?;")
        else:
            if is_option:
                expr = f"{expr}.unwrap()"

            return self.generate_encode_in_dynamic_internal(expr, member.type)

    def generate_encode_in_dynamic_internal(self, expr, expr_type):
        if expr_type.identity == TypeIdentity.INTEGER:
            if expr_type.fixed_size == 1:
                return self.parent.line(f"writer.write_integer::<u8>({expr})?;")

            is_signed = expr_type.signed
            subtype_size = expr_type.fixed_size

            if subtype_size < 8:
                type_prefix = "i" if is_signed else "u"
                expr = f"{expr} as {type_prefix}64"

            if is_signed:
                expr = f"{expr} as u64"

            return self.parent.line(f"writer.write_varint({expr})?;")
        elif expr_type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            format_attr = expr_type.attributes.get("format")
            is_bitfield = format_attr and format_attr.value == "bitfield"

            if is_bitfield:
                return self.parent.line(f"writer.write_varint({expr}.bits() as u64)?;")

            is_signed = expr_type.subtype.signed
            subtype_size = expr_type.subtype.fixed_size
            value_expr = f"{expr}"

            if expr_type.identity == TypeIdentity.CONSTS:
                value_expr = f"{value_expr}.value()"

            if subtype_size < 8:
                type_prefix = "i" if is_signed else "u"
                value_expr = f"{value_expr} as {type_prefix}64"

            if is_signed:
                value_expr = f"{value_expr} as u64"

            return self.parent.line(f"writer.write_varint({value_expr})?;")
        elif expr_type.identity is TypeIdentity.STRING:
            if expr.startswith("self."):
                expr = f"&{expr}"

            return self.parent.line(f"writer.write_string({expr})?;")
        elif expr_type.identity is TypeIdentity.ARRAY:
            out = self.parent.line(
                f"writer.write_varint({expr}.len() as u64)?;")

            out += self.parent.line(f"for item in {expr}.iter() {{")

            self.parent.indent()

            item_expr = f"item"

            if expr_type.subtype.identity in (
                TypeIdentity.ENUM,
                TypeIdentity.CONSTS,
                TypeIdentity.INTEGER,
            ):
                item_expr = f"*{item_expr}"

            out += self.generate_encode_in_dynamic_internal(
                item_expr, expr_type.subtype)

            self.parent.dedent()

            return out + self.parent.line("}")
        elif expr_type.identity is TypeIdentity.STRUCT:
            if expr.startswith("self."):
                expr = f"&{expr}"

            return self.parent.line(f"writer.write_struct({expr})?;")
        else:
            raise RuntimeError("Unexpected variable type")


class CodeGenerator:
    def __init__(self, units):
        if len(units) != 1:
            raise ValueError(
                "Rust code generator only supports one input file at a time")

        self.units = units
        self.indent_level = 0
        self.indent_str = ""

    def indent(self, level=1):
        self.indent_level += level
        self.indent_str = self.indent_level * "    "

        if self.indent_level < 0:
            raise RuntimeError("Indent level cannot be negative")

    def dedent(self):
        self.indent(-1)

    def line(self, text):
        return f"{self.indent_str}{text}\n"

    def lines(self, lines):
        return "".join([self.line(line) for line in lines])

    def generate_type(self, type_):
        if type_.identity == TypeIdentity.INTEGER:
            signed_prefix = "i" if type_.signed else "u"

            return f'{signed_prefix}{type_.fixed_size * 8}'
        elif type_.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            return f"{type_.name}"
        elif type_.identity == TypeIdentity.STRING:
            return f"String"
        elif type_.identity == TypeIdentity.ARRAY:
            subtype = self.generate_type(type_.subtype)

            if type_.n_elements:
                return f"[{subtype}; {type_.n_elements}]"

            return f"Vec<{subtype}>"
        elif type_.identity == TypeIdentity.STRUCT:
            return f"{type_.name}"
        else:
            raise ValueError(f"Unsupported type identity: {type_.identity}")

    def determine_pointer_size(self, what, size):
        if what != "head":
            return 8

        if size <= 0xFF:
            return 1
        elif size <= 0xFFFF:
            return 2
        elif size <= 0xFFFFFFFF:
            return 4
        elif size <= 0xFFFFFFFFFFFFFFFF:
            return 8

        return None

    def determine_pointer_type(self, what, size):
        size = self.determine_pointer_size(what, size)

        if size:
            return f"u{size * 8}"

        return None

    def calculate_fixed_part_size(self, what, members, parent):
        result = 8 if what == "head" else 0

        ptr_size = self.determine_pointer_size(
            what, parent.head.size if what == "head" else None)

        for member in members:
            if isinstance(member, TagsBlock) or member.type.dynamic:
                result += ptr_size
            else:
                result += member.type.fixed_size

        return result

    def generate_calculate_dynamic_size_of_member(self, into, expr, member, as_type, is_option):
        conv = ""

        if as_type:
            conv = f" as {as_type}"

        if isinstance(member, TagsBlock):
            out = ""

            for child in member.members:
                child_name = snake_case(child.name)
                child_name = escape_keyword(child_name)

                expr = f"self.{child_name}"

                if child.type.identity in (
                    TypeIdentity.STRING,
                    TypeIdentity.ARRAY,
                    TypeIdentity.STRUCT,
                ):
                    expr = f"{expr}.as_ref()"

                out += self.line(f"if let Some(value) = {expr} {{")

                self.indent()

                out += self.line(
                    f"{into} += bragi::size_of_varint({child.tag.value}u64){conv};")
                out += self.generate_calculate_dynamic_size_of_member(
                    into, "value", child, as_type, False)

                self.dedent()

                out += self.line("}")

            return out + self.line(f"{into} += bragi::size_of_varint(0u64){conv};")
        else:
            if is_option:
                expr = f"{expr}.unwrap()"

            return self.generate_calculate_dynamic_size_of_member_internal(into, expr, member.type, as_type)

    def generate_calculate_dynamic_size_of_member_internal(self, into, expr, expr_type, as_type):
        conv = ""

        if as_type:
            conv = f" as {as_type}"

        if expr_type.identity == TypeIdentity.INTEGER:
            if expr_type.fixed_size == 1:
                return self.line(f"{into} += 1;")

            is_signed = expr_type.signed
            subtype_size = expr_type.fixed_size

            if expr_type.identity == TypeIdentity.CONSTS:
                value_expr = f"{value_expr}.value()"

            if subtype_size < 8:
                type_prefix = "i" if is_signed else "u"
                expr = f"{expr} as {type_prefix}64"

            if is_signed:
                expr = f"{expr} as u64"

            return self.line(f"{into} += bragi::size_of_varint({expr}){conv};")
        elif expr_type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            format_attr = expr_type.attributes.get("format")
            is_bitfield = format_attr and format_attr.value == "bitfield"

            if is_bitfield:
                return self.line(f"{into} += bragi::size_of_varint({expr}.bits() as u64){conv};")

            is_signed = expr_type.subtype.signed
            subtype_size = expr_type.subtype.fixed_size
            value_expr = f"{expr}"

            if expr_type.identity == TypeIdentity.CONSTS:
                value_expr = f"{value_expr}.value()"

            if subtype_size < 8:
                type_prefix = "i" if is_signed else "u"
                value_expr = f"{value_expr} as {type_prefix}64"

            if is_signed:
                value_expr = f"{value_expr} as u64"

            return self.line(f"{into} += bragi::size_of_varint({value_expr}){conv};")
        elif expr_type.identity is TypeIdentity.STRING:
            out = self.line("{")

            self.indent()

            out += self.line(f"let bytes = {expr}.as_bytes();")
            out += self.line(f"{into} += bragi::size_of_varint(bytes.len() as u64){conv};")
            out += self.line(f"{into} += bytes.len(){conv};")

            self.dedent()

            return out + self.line("}")
        elif expr_type.identity is TypeIdentity.ARRAY:
            out = self.line("{")

            self.indent()

            out += self.line(
                f"{into} += bragi::size_of_varint({expr}.len() as u64){conv};")

            out += self.line(f"for item in {expr}.iter() {{")

            self.indent()

            item_expr = f"item"

            if expr_type.subtype.identity in (
                TypeIdentity.ENUM,
                TypeIdentity.CONSTS,
                TypeIdentity.INTEGER,
            ):
                item_expr = f"*{item_expr}"

            out += self.generate_calculate_dynamic_size_of_member_internal(
                into, item_expr, expr_type.subtype, as_type)

            self.dedent()

            out += self.line("}")

            self.dedent()

            return out + self.line("}")
        elif expr_type.identity is TypeIdentity.STRUCT:
            if expr.startswith("self."):
                expr = f"&{expr}"

            return self.line(f"{into} += {expr}.size_of_body();")
        else:
            raise RuntimeError(
                f"Unexpected member type identity: {expr_type.identity}")

    def generate_part_encoder(self, what, parent, members):
        out = self.line(
            f"fn encode_{what}<W: {WRTIER_GENERIC}>(&self, writer: &mut W) -> {IO_RESULT} {{")

        self.indent()

        out += self.line(f"let mut writer = bragi::Writer::new(writer);")

        if what == "head":
            out += self.line(f"writer.write_integer::<u32>(Self::MESSAGE_ID)?;")
            out += self.line(f"writer.write_integer::<u32>(self.size_of_tail() as u32)?;")

        fixed_size = self.calculate_fixed_part_size(
            what, members, parent) if members else None

        ptrs = [
            i for i in members if isinstance(i, TagsBlock) or i.type.dynamic
        ] if members else None

        ptr_type = self.determine_pointer_type(
            what, parent.head.size if what == "head" else None) if parent else None

        if ptrs:
            out += self.line(
                f"let mut dyn_offsets = [0{ptr_type}; {len(ptrs)}];")

            for i, member in enumerate(ptrs):
                out += self.generate_determine_dyn_offset_for(
                    fixed_size, ptrs[i - 1] if i > 0 else None, member, i, ptr_type)

        if members:
            fixed_enc = FixedEncoder(self)
            dyn_enc = DynamicEncoder(self)

            for member in members:
                out += fixed_enc.generate_encode_in_fixed(member, ptr_type)

            for member in ptrs:
                expr = ""
                is_option = False

                if not isinstance(member, TagsBlock):
                    member_name = snake_case(member.name)
                    member_name = escape_keyword(member_name)

                    expr = f"self.{member_name}"
                    is_option = self.is_type_optional(member.type)

                out += dyn_enc.generate_encode_in_dynamic(
                    expr, member, is_option)

        out += self.line(f"Ok(())")

        self.dedent()

        return out + self.line("}")

    def generate_struct_encoder(self, parent, members):
        out = self.line(
            f"fn encode_body<W: {WRTIER_GENERIC}>(&self, writer: &mut W) -> {IO_RESULT} {{")

        self.indent()

        out += self.line(f"let mut writer = bragi::Writer::new(writer);")
        dyn_enc = DynamicEncoder(self)

        for member in members:
            expr = ""
            is_option = False

            if not isinstance(member, TagsBlock):
                member_name = snake_case(member.name)
                member_name = escape_keyword(member_name)

                expr = f"self.{member_name}"
                is_option = self.is_type_optional(member.type)

            out += dyn_enc.generate_encode_in_dynamic(expr, member, is_option)

        out += self.line("Ok(())")

        self.dedent()

        return out + self.line("}")

    def generate_part_decoder(self, what, parent, members):
        out = self.line(
            f"fn decode_{what}<R: {READER_GENERIC}>(&mut self, reader: &mut R) -> {IO_RESULT} {{")

        self.indent()

        out += self.line(f"let mut reader = bragi::Reader::new(reader);")

        if what == "head":
            out += self.line(f"let id = reader.read_integer::<u32>()?;")
            out += self.line(f"let _tail_size = reader.read_integer::<u32>()?;")
            out += self.line(f"if id != Self::MESSAGE_ID {{")

            self.indent()

            out += self.line(
                f"return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, \"Invalid message ID\"));")

            self.dedent()

            out += self.line("}")

        dec = Decoder(self)

        if members:
            ptr_type = self.determine_pointer_type(
                what, parent.head.size if what == "head" else None)

            for member in members:
                expr = ""

                if not isinstance(member, TagsBlock):
                    member_name = snake_case(member.name)
                    member_name = escape_keyword(member_name)

                    expr = f"self.{member_name}"

                out += dec.generate_decode_member(expr, member, ptr_type)

        out += self.line(f"Ok(())")

        self.dedent()

        return out + self.line("}")

    def generate_struct_decoder(self, parent, members):
        out = self.line(
            f"fn decode_body<R: {READER_GENERIC}>(&mut self, reader: &mut R) -> {IO_RESULT} {{")

        self.indent()

        out += self.line(f"let mut reader = bragi::Reader::new(reader);")
        dec = Decoder(self)

        for member in members:
            expr = ""

            if not isinstance(member, TagsBlock):
                member_name = snake_case(member.name)
                member_name = escape_keyword(member_name)

                expr = f"self.{member_name}"

            out += dec.generate_decode_dynamic(expr, member)

        out += self.line("Ok(())")

        self.dedent()

        return out + self.line("}")

    def generate_enum(self, enum):
        out = ""
        underlying_type = self.generate_type(enum.type.subtype)

        format_attr = enum.attributes.get("format")
        is_bitfield = format_attr and format_attr.value == "bitfield"

        if is_bitfield:
            out += self.line("bragi::generate_bitfield_enum! {")
        elif enum.mode == "consts":
            out += self.line(f"bragi::generate_consts! {{")
        else:
            out += self.line(f"bragi::generate_enum! {{")

        self.indent()

        out += self.line(f"pub enum {enum.name} : {underlying_type} {{")

        self.indent()

        value = 0

        for member in enum.members:
            if member.value is not None:
                value = member.value

            member_name = member.name

            if is_bitfield or enum.mode == "consts":
                member_name = snake_case(member_name.lower())
                member_name = member_name.upper()
            else:
                member_name = camel_case(member_name)

            out += self.line(f"{member_name} = {value},")
            value = value + 1

        self.dedent()

        out += self.line("}")

        self.dedent()

        return out + self.line("}")

    def is_type_optional(self, type_):
        return type_.identity in (TypeIdentity.CONSTS, TypeIdentity.ENUM)

    def generate_fields(self, members, is_tag_block):
        out = ""

        for member in members:
            if isinstance(member, TagsBlock):
                out += self.generate_fields(member.members, True)
            else:
                member_name = snake_case(member.name)
                member_name = escape_keyword(member_name)
                member_type = self.generate_type(member.type)

                if is_tag_block or self.is_type_optional(member.type):
                    member_type = f"Option<{member_type}>"

                out += self.line(f"{member_name}: {member_type},")

        return out

    def generate_accessors(self, members, is_tag_block):
        out = ""

        for member in members:
            if isinstance(member, TagsBlock):
                out += self.generate_accessors(member.members, True)
                continue

            member_name = snake_case(member.name)
            member_name_esc = escape_keyword(member_name)

            member_type = self.generate_type(member.type)
            member_type_ref = member_type

            if member.type.identity == TypeIdentity.STRUCT:
                member_type_ref = f"&{member_type}"
            elif member.type.identity == TypeIdentity.STRING:
                member_type_ref = f"&str"
            elif member.type.identity == TypeIdentity.ARRAY:
                array_size = ""

                if member.type.fixed_size:
                    array_size = f"; {member.type.n_elements}"

                member_type_ref = f"&[{self.generate_type(member.type.subtype)}{array_size}]"

            if is_tag_block:
                out += self.line(
                    f"pub fn {member_name_esc}(&self) -> Option<{member_type_ref}> {{")
            else:
                out += self.line(
                    f"pub fn {member_name_esc}(&self) -> {member_type_ref} {{")

            self.indent()

            if is_tag_block:
                if member.type.identity in (TypeIdentity.STRING, TypeIdentity.ARRAY) and not member.type.fixed_size:
                    out += self.line(f"self.{member_name_esc}.as_deref()")
                elif member.type.identity in (TypeIdentity.STRUCT, TypeIdentity.ARRAY):
                    out += self.line(f"self.{member_name_esc}.as_ref()")
                else:
                    out += self.line(f"self.{member_name_esc}")
            elif member.type.identity in (
                TypeIdentity.STRUCT,
                TypeIdentity.STRING,
                TypeIdentity.ARRAY,
            ):
                out += self.line(f"&self.{member_name_esc}")
            else:
                if member.type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
                    out += self.line(f"self.{member_name_esc}.unwrap()")
                else:
                    out += self.line(f"self.{member_name_esc}")

            self.dedent()

            out += self.line(f"}}")
            out += self.line(
                f"pub fn set_{member_name}(&mut self, value: {member_type}) {{")

            self.indent()

            if is_tag_block or self.is_type_optional(member.type):
                out += self.line(f"self.{member_name_esc} = Some(value);")
            else:
                out += self.line(f"self.{member_name_esc} = value;")

            self.dedent()

            out += self.line(f"}}")

        return out

    def generate_determine_dyn_offset_for(self, skip, prev, member, n, as_type):
        out = ""
        into = f"dyn_offsets[{n}]"

        if n > 0:
            out += self.line(f"{into} = dyn_offsets[{n - 1}];")
        else:
            out += self.line(f"{into} = {skip};")

        if prev:
            member_name = snake_case(prev.name)
            member_name = escape_keyword(member_name)

            out += self.generate_calculate_dynamic_size_of_member(
                into, f"self.{member_name}", prev, as_type, False)

        return out

    def generate_calculate_size_of(self, what, members, parent):
        out = self.line(f"fn size_of_{what}(&self) -> usize {{")

        self.indent()

        fixed_part_size = self.calculate_fixed_part_size(what, members, parent)

        out += self.line(f"let mut size = {fixed_part_size};")

        dyn_members = [
            member for member in members if isinstance(member, TagsBlock) or member.type.dynamic
        ]

        for member in dyn_members:
            expr = ""
            is_option = False

            if not isinstance(member, TagsBlock):
                member_name = snake_case(member.name)
                member_name = escape_keyword(member_name)

                expr = f"self.{member_name}"
                is_option = self.is_type_optional(member.type)

            out += self.generate_calculate_dynamic_size_of_member(
                "size", expr, member, False, is_option)

        out += self.line("size")

        self.dedent()

        return out + self.line("}")

    def generate_stub_calculate_size_of(self, what):
        out = self.line(f"fn size_of_{what}(&self) -> usize {{")

        self.indent()

        out += self.line(f"{8 if what == 'head' else 0}")

        self.dedent()

        return out + self.line("}")

    def generate_struct_calculate_size_of(self, members, parent):
        out = self.line(f"fn size_of_body(&self) -> usize {{")

        self.indent()

        out += self.line(f"let mut size = 0;")

        for member in members:
            expr = ""
            is_option = False

            if not isinstance(member, TagsBlock):
                member_name = snake_case(member.name)
                member_name = escape_keyword(member_name)

                expr = f"self.{member_name}"
                is_option = self.is_type_optional(member.type)

            out += self.generate_calculate_dynamic_size_of_member(
                "size", expr, member, False, is_option)

        out += self.line("size")

        self.dedent()

        return out + self.line("}")

    def generate_constructor(self, members):
        ctor_members = list(
            filter(lambda m: not isinstance(m, TagsBlock), members))

        args = []

        for member in ctor_members:
            member_name = snake_case(member.name)
            member_name = escape_keyword(member_name)

            args.append(f"{member_name}: {self.generate_type(member.type)}")

        out = self.line(f"pub fn new({', '.join(args)}) -> Self {{")

        self.indent()

        out += self.line(f"Self {{")

        self.indent()

        for member in ctor_members:
            member_name = snake_case(member.name)
            member_name = escape_keyword(member_name)

            if self.is_type_optional(member.type):
                out += self.line(f"{member_name}: Some({member_name}),")
            else:
                out += self.line(f"{member_name},")

        if len(ctor_members) != len(members):
            out += self.line(f"..Default::default()")

        self.dedent()

        out += self.line("}")

        self.dedent()

        return out + self.line("}")

    def generate_struct(self, struct):
        out = ""
        all_members = flatten([
            flatten((
                m.members if isinstance(m, TagsBlock) else [m] for m in struct.members
            ))
        ])

        out += self.line(f"#[derive(Default, Debug, Clone)]")
        out += self.line(f"pub struct {struct.name} {{")

        self.indent()

        out += self.generate_fields(struct.members, False)

        self.dedent()

        out += self.line("}")
        out += self.line(f"impl {struct.name} {{")

        self.indent()

        out += self.generate_constructor(struct.members)
        out += self.generate_accessors(struct.members, False)

        self.dedent()

        out += self.line("}")
        out += self.line(f"impl bragi::Struct for {struct.name} {{")

        self.indent()

        out += self.generate_struct_calculate_size_of(struct.members, struct)
        out += self.generate_struct_encoder(struct, struct.members)
        out += self.generate_struct_decoder(struct, struct.members)

        self.dedent()

        return out + self.line("}")

    def generate_message(self, message):
        out = ""
        all_members = flatten([
            flatten((m.members if isinstance(m, TagsBlock) else [
                    m] for m in message.head.members) if message.head is not None else []),
            flatten((m.members if isinstance(m, TagsBlock) else [
                    m] for m in message.tail.members) if message.tail is not None else [])
        ])

        out += self.line(f"#[derive(Default, Debug, Clone)]")
        out += self.line(f"pub struct {message.name} {{")

        self.indent()

        if message.head:
            out += self.generate_fields(message.head.members, False)

        if message.tail:
            out += self.generate_fields(message.tail.members, False)

        self.dedent()

        out += self.line("}")
        out += self.line(f"impl {message.name} {{")

        self.indent()

        out += self.generate_constructor(flatten([
            flatten([message.head.members]) if message.head else [],
            flatten([message.tail.members]) if message.tail else []
        ]))

        if message.head:
            out += self.generate_accessors(message.head.members, False)

        if message.tail:
            out += self.generate_accessors(message.tail.members, False)

        self.dedent()

        out += self.line("}")
        out += self.line(f"impl bragi::Message for {message.name} {{")

        self.indent()

        out += self.line(f"const MESSAGE_ID: u32 = {message.id};")
        out += self.line(f"const HEAD_SIZE: usize = {message.head.size};")

        head_size_of = ""
        head_encode = ""
        head_decode = ""

        tail_size_of = ""
        tail_encode = ""
        tail_decode = ""

        if message.head:
            head_size_of = self.generate_calculate_size_of(
                "head", message.head.members, message)

            head_encode = self.generate_part_encoder(
                "head", message, message.head.members)

            head_decode = self.generate_part_decoder(
                "head", message, message.head.members)
        else:
            head_size_of = self.generate_stub_calculate_size_of("head")
            head_encode = self.generate_part_encoder("head", None, None)
            head_decode = self.generate_part_decoder("head", None, None)

        if message.tail:
            tail_size_of = self.generate_calculate_size_of(
                "tail", message.tail.members, message)

            tail_encode = self.generate_part_encoder(
                "tail", message, message.tail.members)

            tail_decode = self.generate_part_decoder(
                "tail", message, message.tail.members)
        else:
            tail_size_of = self.generate_stub_calculate_size_of("tail")
            tail_encode = self.generate_part_encoder("tail", None, None)
            tail_decode = self.generate_part_decoder("tail", None, None)

        out += head_size_of
        out += tail_size_of

        out += head_encode
        out += tail_encode

        out += head_decode
        out += tail_decode

        self.dedent()

        return out + self.line("}")

    def generate(self):
        output = [
            "// This file is generated by bragi. Any changes will be overwritten.\n",
            "use bragi::Struct;\n"
        ]

        for token in self.units[0].tokens:
            if isinstance(token, Enum):
                output.append(self.generate_enum(token))
            elif isinstance(token, Struct):
                output.append(self.generate_struct(token))
            elif isinstance(token, Message):
                output.append(self.generate_message(token))
            elif isinstance(token, Group):
                for member in token.members:
                    output.append(self.generate_message(member))
            else:
                output.append(f"// Unknown token: {type(token).__name__}\n")

        return "".join(output)
