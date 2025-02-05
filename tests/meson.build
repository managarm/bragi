bragi = find_program('bragi')

frigg_dep = subproject('frigg').get_variable('frigg_dep')

bragi_gen = generator(bragi,
	arguments: [
		'-o', '@OUTPUT@',
		'@INPUT@',
		'-l', 'stdc++',
	],
	output: '@BASENAME@.bragi.hpp')

bragi_std_gen = generator(bragi,
	arguments: [
		'-o', '@OUTPUT@',
		'@INPUT@',
		'-l', 'stdc++',
	],
	output: '@BASENAME@.bragi.std.hpp')

bragi_frg_gen = generator(bragi,
	arguments: [
		'-o', '@OUTPUT@',
		'@INPUT@',
		'-l', 'frigg',
	],
	output: '@BASENAME@.bragi.frg.hpp')

tests = [
	'basic',
	'enums',
	'empty',
	'arrays',
	'preamble',
	'struct',
	'using',
	'group'
]

foreach t : tests
	exe_std = executable(t + '-std',
		t / t + '.cpp',
		bragi_std_gen.process(t / t + '.bragi'),
		include_directories: bragi_inc)

	exe_frg = executable(t + '-frg',
		t / t + '.cpp',
		bragi_frg_gen.process(t / t + '.bragi'),
		include_directories: bragi_inc,
		cpp_args: '-DTEST_FRIGG',
		dependencies: frigg_dep)

	test(t + '-std', exe_std)
	test(t + '-frg', exe_frg)
endforeach
