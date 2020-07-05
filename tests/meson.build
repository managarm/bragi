project('bragi-tests', 'cpp', default_options: ['cpp_std=c++2a'])

bragi = find_program('bragi')

bragi_gen = generator(bragi,
	arguments: [
		'-l', 'stdc++',
		'@INPUT@',
		'@OUTPUT@'
	],
	output: '@BASENAME@.bragi.hpp')

bragi_inc = include_directories('../include')

subdir('basic')
subdir('enums')
subdir('empty')
subdir('arrays')
subdir('preamble')
subdir('struct')
