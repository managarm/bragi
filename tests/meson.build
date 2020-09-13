bragi = find_program('bragi')

bragi_gen = generator(bragi,
	arguments: [
		'-l', 'stdc++',
		'@INPUT@',
		'@OUTPUT@'
	],
	output: '@BASENAME@.bragi.hpp')

subdir('basic')
subdir('enums')
subdir('empty')
subdir('arrays')
subdir('preamble')
subdir('struct')
subdir('using')
