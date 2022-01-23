exe_std = executable('enums-std',
	'enums.cpp',
	bragi_std_gen.process('enums.bragi'),
	include_directories: bragi_inc)

exe_frg = executable('enums-frg',
	'enums.cpp',
	bragi_frg_gen.process('enums.bragi'),
	include_directories: bragi_inc,
	cpp_args: '-DTEST_FRIGG',
	dependencies: frigg_dep)

test('enums-std', exe_std)
test('enums-frg', exe_frg)
