#!/usr/bin/env python3

import argparse

from bragi.parser import CompilationUnit
from bragi.cpp_generator import CodeGenerator as CppCodeGenerator
from bragi.wireshark_generator import CodeGenerator as WiresharkCodeGenerator
from bragi.rust_generator import CodeGenerator as RustCodeGenerator

parser = argparse.ArgumentParser(prog = 'bragi', description = 'Bragi IDL to C++ compiler')
parser.add_argument('input', nargs='+', help='input file', type=argparse.FileType('r'))
parser.add_argument('-o', '--output', help='output file', type=str)
subparsers = parser.add_subparsers(required=True, dest='language')

cpp_parser = subparsers.add_parser('cpp')
cpp_parser.add_argument('-l', '--lib', nargs=1, help='C++ library to use', choices=['frigg', 'stdc++'], default='libc++')
cpp_parser.add_argument('--protobuf', help='Generate protobuf compatibilty methods (SerializeAsString/ParseFromArray)', action='store_true')

ws_parser = subparsers.add_parser('wireshark')

rust_parser = subparsers.add_parser('rust')

def main():
	args = parser.parse_args()

	inputs = []
	output = args.output

	for source in args.input:
		code = source.read()
		unit = CompilationUnit(source.name, code)
		unit.process()
		unit.verify()
		inputs.append(unit)

	if args.language == 'cpp':
		lib = args.lib[0]
		generator = CppCodeGenerator(inputs, lib, protobuf_compat = args.protobuf)
	elif args.language == 'wireshark':
		generator = WiresharkCodeGenerator(inputs)
	elif args.language == 'rust':
		generator = RustCodeGenerator(inputs)

	with open(output, "w") as o:
		o.write(generator.generate())
