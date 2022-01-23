exe_std = executable('preamble-std',
	'preamble.cpp',
	bragi_std_gen.process('preamble.bragi'),
	include_directories: bragi_inc)

exe_frg = executable('preamble-frg',
	'preamble.cpp',
	bragi_frg_gen.process('preamble.bragi'),
	include_directories: bragi_inc,
	cpp_args: '-DTEST_FRIGG',
	dependencies: frigg_dep)

test('preamble-std', exe_std)
test('preamble-frg', exe_frg)
