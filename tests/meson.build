bragi = find_program('bragi')

frigg_dep = subproject('frigg').get_variable('frigg_dep')

bragi_gen = generator(bragi,
	arguments: [
		'-l', 'stdc++',
		'@INPUT@',
		'@OUTPUT@'
	],
	output: '@BASENAME@.bragi.hpp')

bragi_std_gen = generator(bragi,
	arguments: [
		'-l', 'stdc++',
		'@INPUT@',
		'@OUTPUT@'
	],
	output: '@BASENAME@.bragi.std.hpp')

bragi_frg_gen = generator(bragi,
	arguments: [
		'-l', 'frigg',
		'@INPUT@',
		'@OUTPUT@'
	],
	output: '@BASENAME@.bragi.frg.hpp')

subdir('basic')
subdir('enums')
subdir('empty')
subdir('arrays')
subdir('preamble')
subdir('struct')
subdir('using')
