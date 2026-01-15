from .tokens import *
from .types import *

import hashlib

flatten = lambda l: [item for sublist in l for item in sublist]

class CodeGenerator:
    def __init__(self, units):
        self.units = units
        self.indent_depth = 0
        self.indent = ''
        self.enums = {}
        self.messages = {}
        self.namespace_tag = None
        self.protocols = {}

    def enter_indent(self):
        self.indent_depth += 1
        self.indent = '\t' * self.indent_depth
        return self.indent

    def leave_indent(self):
        self.indent_depth -= 1
        self.indent = '\t' * self.indent_depth
        return self.indent

    def generate_header(self):
        '''
        Generate the output file header
        '''

        out = f'{self.indent}function parse_varint(varint)\n'
        self.enter_indent()
        out += f'{self.indent}local nbytes = 9\n'
        out += f'{self.indent}local ret = 0\n'
        out += f'{self.indent}if varint(0, 1):uint() ~= 0 then\n'
        self.enter_indent()
        out += f'{self.indent}for i=1,8 do\n'
        self.enter_indent()
        out += f'{self.indent}if bit.band(bit.rshift(varint(0, 1):uint(), i - 1), 1) ~= 0 then\n'
        self.enter_indent()
        out += f'{self.indent}nbytes = i\n'
        out += f'{self.indent}break\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        out += f'{self.indent}for i=1,nbytes-1 do\n'
        self.enter_indent()
        out += f'{self.indent}ret = bit.bor(ret, bit.lshift(varint(i, 1):uint(), (i - 1) * 8))\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        out += f'{self.indent}local shift = 0\n'
        out += f'{self.indent}if nbytes < 9 then\n'
        self.enter_indent()
        out += f'{self.indent}shift = 8 - (nbytes % 8)\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        out += f'{self.indent}ret = bit.lshift(ret, shift)\n'
        out += f'{self.indent}ret = bit.bor(ret, bit.rshift(varint(0, 1):uint(), nbytes))\n'
        out += f'{self.indent}return nbytes, ret\n'
        self.leave_indent()
        out += f'{self.indent}end\n\n'
        return out

    def generate_footer(self):
        '''
        Generate the output file footer
        '''

        out = f'{self.indent}bragi_protocol = Proto("bragi", "bragi request")\n\n'
        out += f'{self.indent}protocol_id = ProtoField.uint32("bragi.protocol", "Encapsulated protocol", base.HEX, protocol_mappings)\n'
        out += f'{self.indent}message_id = ProtoField.int32("bragi.message_id", "message ID", base.DEC)\n'
        out += f'{self.indent}tail_size = ProtoField.int32("bragi.tail_size", "tail size", base.DEC)\n'
        out += f'{self.indent}pid = ProtoField.uint32("bragi.pid", "PID", base.DEC)\n'
        out += f'{self.indent}request_of = ProtoField.framenum("bragi.request_of", "Response in", base.NONE, frametype.RESPONSE)\n'
        out += f'{self.indent}response_to = ProtoField.framenum("bragi.reply_to", "Reply to", base.NONE, frametype.REQUEST)\n'
        out += f'{self.indent}convo_time = ProtoField.relative_time("bragi.convo_time", "Handling time")\n\n'
        out += f'{self.indent}bragi_protocol.fields = {{protocol_id, message_id, tail_size, pid, request_of, response_to, convo_time}}\n\n'
        out += f'{self.indent}function bragi_protocol.dissector(tvb, pinfo, tree)\n'
        self.enter_indent()
        out += f'{self.indent}if tvb:len() == 0 then return end\n\n'
        out += f'{self.indent}local subtree = tree:add(bragi_protocol, tvb(0, 40), "Bragi Protocol Data")\n'
        out += f'{self.indent}local proto_id = tvb(0, 4)\n'
        out += f'{self.indent}local pid_val = tvb(4, 4)\n'
        out += f'{self.indent}local req_num = tvb(8, 8)\n'
        out += f'{self.indent}local resp_num = tvb(16, 8)\n'
        out += f'{self.indent}local req_time = tvb(24, 8)\n'
        out += f'{self.indent}local request = tvb(32, 4)\n\n'
        out += f'{self.indent}if protocol_mappings[proto_id:le_uint()] ~= nil then\n'
        self.enter_indent()
        out += f'{self.indent}pinfo.cols.protocol = protocol_mappings[proto_id:le_uint()]\n'
        self.leave_indent()
        out += f'{self.indent}else\n'
        self.enter_indent()
        out += f'{self.indent}pinfo.cols.protocol = "bragi"\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        out += f'{self.indent}subtree:add_le(protocol_id, proto_id)\n'
        out += f'{self.indent}subtree:add_le(pid, pid_val)\n'
        out += f'{self.indent}if req_num:le_uint64():tonumber() == pinfo.number and resp_num:le_uint64():tonumber() ~= 0 then\n'
        self.enter_indent()
        out += f'{self.indent}subtree:add(request_of, resp_num, resp_num:le_uint64():tonumber())\n'
        self.leave_indent()
        out += f'{self.indent}elseif resp_num:le_uint64():tonumber() == pinfo.number and req_num:le_uint64():tonumber() ~= 0 then\n'
        self.enter_indent()
        out += f'{self.indent}subtree:add(response_to, req_num, req_num:le_uint64():tonumber())\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        out += f'{self.indent}if req_time:le_uint64():tonumber() ~= 0 then\n'
        self.enter_indent()
        out += f'{self.indent}subtree:add(convo_time, req_time, NSTime.new(req_time:le_uint64():tonumber() // 1000000000, req_time:le_uint64():tonumber() % 1000000000))\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        out += f'{self.indent}if protocols[proto_id:le_uint()] ~= nil then\n'
        self.enter_indent()
        out += f'{self.indent}local proto = protocols[proto_id:le_uint()]\n'
        out += f'{self.indent}if proto[request:le_uint()] ~= nil then\n'
        self.enter_indent()
        out += f'{self.indent}local msg_ids = protocol_message_ids[proto_id:le_uint()]\n'
        out += f'{self.indent}pinfo.cols.info:set("PID " .. pid_val:le_uint() .. " " .. msg_ids[request:le_uint()])\n'
        out += f'{self.indent}subtree:add_le(message_id, request, request:le_uint(), "message:", msg_ids[request:le_uint()])\n'
        out += f'{self.indent}local prototree = tree:add(proto[request:le_uint()], tvb(40, tvb:len() - 40))\n'
        out += f'{self.indent}proto[request:le_uint()].dissector(tvb(40, tvb:len() - 40):tvb(), pinfo, prototree)\n'
        self.leave_indent()
        out += f'{self.indent}end\n'
        self.leave_indent()
        out += f'{self.indent}end\n\n'
        out += f'{self.indent}subtree:add_le(tail_size, tvb(36, 4))\n'
        self.leave_indent()
        out += 'end\n\n'
        out += 'local tab = DissectorTable.get("wtap_encap")\n'
        out += 'tab:add(wtap.USER0, bragi_protocol)\n'
        return out

    def generate_integer_parsing(self, m: MessageMember, msg: Message | Struct, tree_name: str = 'tree', tvb_name: str = 'tvb') -> str:
        '''
        Generates the code to parse an integer field

        Parameters:
            m (MessageMember): The member to generate the parsing code for
            msg (Message | Struct): The message the member belongs to
            tree_name (str): The name of the wireshark tree to add the field to
            tvb_name (str): The name of the tvb to read the field from

        Returns:
            str: The generated code excluding increasing the offset (this needs to be done by the caller). The varint size is accessible via the local `varint_size`.
        '''
        if self.proto_field_type(m.type) in ('uint8', 'char'):
            out = f'{self.indent}local varint_size = 1\n'
            out += f'{self.indent}local {m.name}_item = {tree_name}:add_le({self.proto_field_member_name(msg, m)}, {tvb_name}(offset, varint_size))\n'
        else:
            out = f'{self.indent}local varint_size, value = parse_varint({tvb_name}(offset))\n'
            if m.format and m.format.value == "ipv4":
                out += f'{self.indent}local {m.name}_item = {tree_name}:add_le({self.proto_field_member_name(msg, m)}, {tvb_name}(offset, varint_size), ByteArray.new(string.format("%08x", value)):tvb():range():ipv4())\n'
            else:
                type_prefix, type_suffix = self.wireshark_lua_type(m.type)
                out += f'{self.indent}local {m.name}_item = {tree_name}:add_le({self.proto_field_member_name(msg, m)}, {tvb_name}(offset, varint_size), {type_prefix}value{type_suffix})\n'

        return out

    def generate_string_parsing(self, m: MessageMember, msg: Message | Struct, tree_name: str = 'tree', tvb_name: str = 'tvb', tvb_offset: str = '0') -> str:
        '''
        Generates the code to parse a string field

        Parameters:
            m (MessageMember): The member to generate the parsing code for
            msg (Message | Struct): The message the member belongs to
            tree_name (str): The name of the wireshark tree to add the field to
            tvb_name (str): The name of the tvb to read the field from
            tvb_offset (str): The offset in the tvb to start reading from

        Returns:
            str: The generated code excluding increasing the offset (this needs to be done by the caller). The varint and string length are accessible via the locals `len_size` and `len`.
        '''
        out = f'{self.indent}local len_size, len = parse_varint({tvb_name}({tvb_offset}))\n'
        out += f'{self.indent}local {m.name}_item = {tree_name}:add({self.proto_field_member_name(msg, m)}, {tvb_name}({tvb_offset} + len_size, len))\n'
        return out

    def generate_array_parsing(self, m, message: Message | Struct, loc: str, tree_name: str = 'tree', tvb_name: str = 'tvb', member_offset: str = 'value_size') -> str:
        '''
        Generates the code to parse an array

        Parameters:
            m (MessageMember): The member to generate the parsing code for
            message (Message | Struct): The message the member belongs to
            loc (str): the location information to use in error messages
            tree_name (str): The name of the wireshark tree to add the field to
            tvb_name (str): The name of the tvb to read the field from
            member_offset (str): The variable keeping track of the current offset into the tvb; this variable is increased by the size of the array

        Returns:
            str: The generated code including increasing the offset of 'member_offset' by the real size of the array
        '''
        out = f'{self.indent}local members_size, members = parse_varint({tvb_name})\n'
        out += f'{self.indent}{member_offset} = {member_offset} + members_size\n'
        out += f'{self.indent}for i=1,members do\n'
        self.enter_indent()

        if m.type.subtype.identity == TypeIdentity.STRING:
            out += self.generate_string_parsing(m, message, tree_name, tvb_name, tvb_offset=member_offset)
            out += f'{self.indent}{member_offset} = {member_offset} + len_size + len\n'
        elif self.is_simple_integer(self.proto_field_type(m.type.subtype)) and m.type.subtype.identity != TypeIdentity.ARRAY:
            out += f'{self.indent}local member_size, member = parse_varint({tvb_name}({member_offset}))\n'

            type_prefix, type_suffix = self.wireshark_lua_type(m.type)
            out += f'{self.indent}local {m.name}_item = {tree_name}:add_le({self.proto_field_member_name(message, m)}, {tvb_name}({member_offset}, member_size), {type_prefix}member{type_suffix})\n'
            if m.type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS) and "format" in m.type.attributes:
                format_attr = m.type.attributes['format'].value
                if format_attr == "bitfield":
                    for em in self.enums[m.type.name].members:
                        out += f"{self.indent}{m.name}_item:add_le({self.proto_field_member_name(message, m)}_{em.name}, {tvb_name}({member_offset}, member_size), {type_prefix}member{type_suffix})\n"
                        message.fields.append(f"{m.name}_{em.name}")

            out += f'{self.indent}{member_offset} = {member_offset} + member_size\n'
        elif m.type.subtype.identity == TypeIdentity.STRUCT:
            struct_def = self.structs[m.type.subtype.name]
            out += f'{self.indent}local struct_size = {self.proto_name(struct_def)}_struct_size({tvb_name}({member_offset}))\n'
            out += f'{self.indent}{self.proto_name(struct_def)}.dissector({tvb_name}({member_offset}, struct_size):tvb(), pinfo, {tree_name})\n'
            out += f'{self.indent}{member_offset} = {member_offset} + struct_size\n'
        else:
            print(f"unhandled {loc} member {m.type.subtype}[] {m.name} ({m.type})")
        self.leave_indent()
        out += f'{self.indent}end\n'

        return out

    def generate(self):
        '''
        Main code generation function
        '''

        out = '-- This file has been autogenerated, changes *will* be lost eventually...\n'
        out += self.generate_header()

        for unit in self.units:
            self.enums = {}
            self.messages = {}
            self.structs = {}

            for thing in unit.tokens:
                if type(thing) == Enum:
                    self.enums[thing.name] = thing
                    out += self.generate_consts(thing)
                elif type(thing) == Message:
                    out += self.generate_message(thing)
                elif type(thing) == NamespaceTag:
                    self.protohash = hashlib.shake_128(thing.name.encode('ascii')).hexdigest(4)
                    self.shortprotoname = thing.name.rsplit('::', 1)[-1]
                    self.protoname = thing.name
                    self.protocols[self.protohash] = self.protoname
                elif type(thing) == Struct:
                    out += self.generate_struct(thing)
                else:
                    print(f"unhandled type {str(type(thing))}")

            out += self.generate_protocol_metadata()

        out += self.generate_global_protocol_metadata()
        out += self.generate_footer()

        return out

    def generate_consts(self, enum):
        '''
        Generate enum value -> name lookup table
        '''

        i = 0
        out = f'local dis_{self.protohash}_{enum.name} = {{\n'
        self.enter_indent()

        for m in enum.members:
            if m.value is not None:
                i = m.value

            out += f'{self.indent}[{i}] = "{m.name}",\n'

            i += 1

        self.leave_indent()
        out += '}\n\n'

        return out

    def is_simple_integer(self, t):
        return t in ['byte', 'char', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']

    def bits_in_integer(self, t):
        if t.name in ['char', 'int8', 'uint8']:
            return 8
        elif t.name in ['int16', 'uint16']:
            return 16
        elif t.name in ['int32', 'uint32']:
            return 32
        elif t.name in ['int64', 'uint64']:
            return 64

    def is_dyn_pointer(self, m):
        return type(m) is TagsBlock or m.type.dynamic

    def count_dynamic(self, members):
        i = 0

        for m in members:
            if self.is_dyn_pointer(m): i += 1

        return i

    def wireshark_lua_type(self, t):
        '''
        Generate wireshark conversion for a given type
        '''

        if t.identity == TypeIdentity.INTEGER:
            if str(t) in ['byte', 'char', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32']:
                return '', ''
            elif str(t) == 'uint64':
                return 'UInt64(', ')'
            elif str(t) == 'int64':
                return 'Int64(', ')'
        elif t.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            return self.wireshark_lua_type(self.enums[t.name].type.subtype)
        elif t.identity == TypeIdentity.ARRAY:
            return self.wireshark_lua_type(t.subtype)

        raise Exception(f'Unhandled type {t.identity} for {t.name}')

    def proto_field_member_name(self, message: Message | Struct, member):
        '''
        Generates the name of the ProtoField object for a given message member
        '''
        return self.proto_field_name(message, member.name)

    def proto_field_name(self, message: Message | Struct, name: str):
        '''
        Generates the name of the ProtoField object for a given message and field name
        '''
        return f'{self.proto_name(message)}_{name}'

    def proto_name(self, message: Message | Struct):
        '''
        Genereates the name of the Proto object for a given message
        '''
        return f'dis_{self.protohash}_{message.name}'

    def proto_field_type(self, t):
        '''
        Generates the ProtoField type for a given type
        '''

        if t.identity == TypeIdentity.INTEGER:
            if t.name == "byte":
                return 'uint8'
            return t.name
        elif t.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
            return self.proto_field_type(self.enums[t.name].type.subtype)
        elif t.identity == TypeIdentity.STRING:
            return 'string'
        elif t.identity == TypeIdentity.ARRAY:
            if t.subtype.identity == TypeIdentity.INTEGER and t.subtype.name in ('uint8', 'byte', 'char'):
                return 'bytes'
            else:
                return self.proto_field_type(t.subtype)
        elif t.identity == TypeIdentity.STRUCT:
            return 'none'

        return f'UNKNOWN {t.identity}'

    def generate_protofield(self, message: Message | Struct, m: MessageMember) -> str:
        '''
        Generates the ProtoField definition for a given message member

        Parameters:
            message (Message): The message the member belongs to
            m (MessageMember): The member to generate the ProtoField definition for

        Returns:
            str: The generated ProtoField definition
        '''
        field_type = self.proto_field_type(m.type)
        out = ""

        extra_arg = ''

        if self.is_simple_integer(field_type) and m.type.identity != TypeIdentity.ARRAY:
            int_format = "base.DEC"

            if field_type == 'char':
                int_format = "base.HEX"

            if m.format and m.format.value == "hex":
                int_format = "base.HEX"
            elif m.format and m.format.value == "octal":
                int_format = "base.OCT"
            elif m.format and m.format.value == "ipv4":
                return f'{self.proto_field_member_name(message, m)} = ProtoField.ipv4("{self.shortprotoname}_{message.name}.{m.name}", "{m.name}")\n'

            if m.type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS):
                if "format" in m.type.attributes and m.type.attributes["format"].value == "bitfield":
                    for em in self.enums[m.type.name].members:
                        out += f'{self.indent}{self.proto_field_member_name(message, m)}_{em.name} = ProtoField.new("{em.name}", "{em.name}", ftypes.BOOLEAN, nil, {self.bits_in_integer(m.type.subtype)}, {em.value})\n'
                else:
                    extra_arg += f', dis_{self.protohash}_{m.type.name}'

            return f'{out}{self.proto_field_member_name(message, m)} = ProtoField.{field_type}("{self.shortprotoname}_{message.name}.{m.name}", "{m.name}", {int_format}{extra_arg})\n'
        else:
            return f'{out}{self.proto_field_member_name(message, m)} = ProtoField.{field_type}("{self.shortprotoname}_{message.name}.{m.name}", "{m.name}"{extra_arg})\n'

    def generate_message(self, message):
        message.fields = []
        tag_members = {}

        out = f'{self.proto_name(message)} = Proto("{self.shortprotoname}_{message.name}", "{self.protoname} {message.name} request")\n\n'

        head_members = flatten((m.members if type(m) is TagsBlock else [m] for m in message.head.members) if message.head is not None else [])
        tail_members = flatten((m.members if type(m) is TagsBlock else [m] for m in message.tail.members) if message.tail is not None else [])
        all_members = flatten([ head_members, tail_members ])

        for m in all_members:
            if m.tag:
                tag_members[m.tag] = m

            message.fields.append(m.name)

            out += self.generate_protofield(message, m)

        out += f'\n{self.indent}{self.proto_name(message)}_tags = {{\n'
        self.enter_indent()
        for tag, m in tag_members.items():
            out += f'{self.indent}[{tag.value}] = {self.proto_field_member_name(message, m)},\n'

        self.leave_indent()
        out += f'{self.indent}}}\n\n'

        out += f'{self.indent}function {self.proto_name(message)}.dissector(tvb, pinfo, tree)\n'
        self.enter_indent()

        member_offset = 0
        for m in head_members:
            if m.tag:
                continue

            out += f'{self.indent}local {m.name}_item = tree:add_le({self.proto_field_member_name(message, m)}, tvb({member_offset}, {m.type.fixed_size}))\n'
            if m.type.identity in (TypeIdentity.ENUM, TypeIdentity.CONSTS) and "format" in m.type.attributes:
                format_attr = m.type.attributes['format'].value
                if format_attr == "bitfield":
                    for em in self.enums[m.type.name].members:
                        out += f"{self.indent}{m.name}_item:add_le({self.proto_field_member_name(message, m)}_{em.name}, tvb:range({member_offset}, {m.type.fixed_size}))\n"
                        message.fields.append(f"{m.name}_{em.name}")

            member_offset += m.type.fixed_size

        out += self.generate_message_tag_members(message, tag_members)
        out += self.generate_message_tail_members(message, tail_members)

        self.leave_indent()
        out += 'end\n\n'

        fields_str = ", ".join([self.proto_field_name(message, f) for f in message.fields])
        out += f'{self.proto_name(message)}.fields = {{{fields_str}}}\n\n'

        self.messages[message.id] = message

        return out

    def generate_message_tag_members(self, message, tag_members):
        if not tag_members:
            return ''

        first_tag = True
        tags_offset = self.calculate_fixed_part_size('head', message.head.members, message) - 8
        out = f'{self.indent}local tags = tvb({tags_offset}, tvb:len() - {tags_offset}):tvb()\n'
        out += f'{self.indent}local size, tag = parse_varint(tags)\n'
        out += f'{self.indent}tags = tags(size, tags:len() - size):tvb()\n'
        out += f'{self.indent}while tag ~= 0 do\n'
        self.enter_indent()
        out += f'{self.indent}local value_size = 0\n'
        for tag, m in tag_members.items():
            if first_tag:
                first_tag = False
                out += f'{self.indent}if tag == {tag.value} then\n'
            else:
                out += f'{self.indent}elseif tag == {tag.value} then\n'
            self.enter_indent()

            if self.is_simple_integer(self.proto_field_type(m.type)) and m.type.identity != TypeIdentity.ARRAY:
                out += self.generate_integer_parsing(m, message, tvb_name='tags')
                out += f'{self.indent}value_size = varint_size\n'
            elif m.type.identity == TypeIdentity.STRING:
                out += self.generate_string_parsing(m, message, tvb_name='tags')
                out += f'{self.indent}value_size = len_size + len\n'
            elif m.type.identity == TypeIdentity.ARRAY:
                out += self.generate_array_parsing(m, message, 'tag', tvb_name='tags')
            else:
                print(f'unhandled type {m.type}')

            self.leave_indent()
        out += f'{self.indent}end\n'

        out += f'{self.indent}size, tag = parse_varint(tags(value_size))\n'
        out += f'{self.indent}tags = tags(value_size + size, tags:len() - size - value_size):tvb()\n'

        self.leave_indent()
        out += f'{self.indent}end\n'

        return out

    def generate_message_tail_members(self, message, tail_members):
        if not tail_members:
            return ''

        out = ''
        head_size = self.calculate_fixed_part_size('head', message.head.members, message) - 8
        tail_member_num = 0
        for m in tail_members:
            out += f'{self.indent}local dynoff{tail_member_num} = tvb({head_size + (tail_member_num * 8)}, 4):le_uint()\n'
            out += f'{self.indent}local tail = tvb({head_size} + dynoff{tail_member_num}, tvb:len() - ({head_size} + dynoff{tail_member_num}))\n'
            out += f'{self.indent}local value_size = 0\n'
            if m.type.identity == TypeIdentity.STRING:
                out += f'{self.indent}local len_size, len = parse_varint(tail)\n'
                out += f'{self.indent}if len_size < tail:len() then\n'
                self.enter_indent()
                out += f'{self.indent}tree:add({self.proto_field_member_name(message, m)}, tail(len_size, len), tail(len_size, len):string())\n'
                self.leave_indent()
                out += f'{self.indent}else\n'
                self.enter_indent()
                out += f'{self.indent}tree:add({self.proto_field_member_name(message, m)}, tail(0, len_size + len), "<empty>")\n'
                self.leave_indent()
                out += f'{self.indent}end\n'
            elif m.type.identity == TypeIdentity.ARRAY:
                out += self.generate_array_parsing(m, message, 'tail', tvb_name='tail')

                out += f'{self.indent}len = value_size\n'
            elif self.is_simple_integer(self.proto_field_type(m.type)):
                out += f'{self.indent}if len_size < tail:len() then\n'
                self.enter_indent()
                out += f'{self.indent}tree:add({self.proto_field_member_name(message, m)}, tail(len_size, len), parse_varint(tail(len_size, len)))\n'
                self.leave_indent()
                out += f'{self.indent}else\n'
                self.enter_indent()
                out += f'{self.indent}tree:add({self.proto_field_member_name(message, m)}, tail(0, len_size + len), "<empty>")\n'
                self.leave_indent()
                out += f'{self.indent}end\n'
            else:
                print(f"unhandled tail member {m.type} {m.name}")
            tail_member_num += 1

        return out

    def generate_struct(self, struct: Struct):
        '''
        Generates the Proto and dissector for a given struct
        '''

        self.structs[struct.name] = struct
        out = f'{self.indent}{self.proto_name(struct)} = Proto("{self.shortprotoname}_{struct.name}", "{struct.name}")\n'

        members = []
        for item in struct.members:
            out += self.generate_protofield(struct, item)
            members.append(item.name)

        fields_str = ", ".join([self.proto_field_name(struct, f) for f in members])
        out += f'{self.indent}{self.proto_name(struct)}.fields = {{{fields_str}}}\n'
        out += f'{self.indent}function {self.proto_name(struct)}.dissector(tvb, pinfo, tree)\n'
        self.enter_indent()
        out += f'{self.indent}local subtree = tree:add({self.proto_name(struct)}, tvb(0))\n'
        out += f'{self.indent}local offset = 0\n'
        for m in struct.members:
            if m.type.identity == TypeIdentity.STRING:
                out += self.generate_string_parsing(m, struct, tree_name='subtree', tvb_offset='offset')
                out += f'{self.indent}offset = offset + len_size + len\n'
            elif self.is_simple_integer(self.proto_field_type(m.type)) and m.type.identity != TypeIdentity.ARRAY:
                out += self.generate_integer_parsing(m, struct, tree_name='subtree')
                out += f'{self.indent}offset = offset + varint_size\n'
            else:
                print(f'unhandled struct member {m.type} {m.name}')
        self.leave_indent()
        out += 'end\n\n'

        # generate a function to calculate the struct's size
        out += f'{self.indent}function {self.proto_name(struct)}_struct_size(tvb)\n'
        self.enter_indent()
        out += f'{self.indent}local offset = 0\n'
        for m in struct.members:
            if m.type.identity == TypeIdentity.STRING:
                out += f'{self.indent}local len_size, len = parse_varint(tvb(offset))\n'
                out += f'{self.indent}offset = offset + len_size + len\n'
            elif self.is_simple_integer(self.proto_field_type(m.type)) and m.type.identity != TypeIdentity.ARRAY:
                if self.proto_field_type(m.type) in ('uint8', 'char'):
                    out += f'{self.indent}offset = offset + 1\n'
                else:
                    out += f'{self.indent}local varint_size, value = parse_varint(tvb(offset))\n'
                    out += f'{self.indent}offset = offset + varint_size\n'
            else:
                print(f'unhandled struct member {m.type} {m.name}')
        out += f'{self.indent}return offset\n'
        self.leave_indent()
        out += 'end\n\n'

        return out

    def generate_protocol_metadata(self):
        '''
        Generates the protocol metadata for the current bragi protocol dissector
        '''

        out = f'local dis_{self.protohash}_msgs = {{\n'
        self.enter_indent()

        for m in self.messages:
            out += f'{self.indent}[{m}] = {self.proto_name(self.messages[m])},\n'

        self.leave_indent()
        out += '}\n\n'

        out += f'local dis_{self.protohash}_message_ids = {{\n'
        self.enter_indent()

        for m in self.messages:
            out += f'{self.indent}[{m}] = "{self.messages[m].name}",\n'

        self.leave_indent()
        out += '}\n\n'

        return out

    def generate_global_protocol_metadata(self):
        '''
        Generates the global protocol metadata for the generated bragi protocol dissectors
        '''

        out = f'local protocol_mappings = {{\n'
        self.enter_indent()
        for p in self.protocols:
            out += f'{self.indent}[0x{p}] = "{self.protocols[p]}",\n'
        self.leave_indent()
        out += '}\n\n'

        out += f'local protocol_message_ids = {{\n'
        self.enter_indent()
        for p in self.protocols:
            out += f'{self.indent}[0x{p}] = dis_{p}_message_ids,\n'
        self.leave_indent()
        out += '}\n\n'

        out += f'local protocols = {{\n'
        self.enter_indent()
        for p in self.protocols:
            out += f'{self.indent}[0x{p}] = dis_{p}_msgs,\n'
        self.leave_indent()
        out += '}\n\n'

        return out

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
                i += ptr_size if ptr_size else 0

        return i
