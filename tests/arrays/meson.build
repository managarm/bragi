exe_std = executable('arrays-std',
	'arrays.cpp',
	bragi_std_gen.process('arrays.bragi'),
	include_directories: bragi_inc)

exe_frg = executable('arrays-frg',
	'arrays.cpp',
	bragi_frg_gen.process('arrays.bragi'),
	include_directories: bragi_inc,
	cpp_args: '-DTEST_FRIGG',
	dependencies: frigg_dep)

test('arrays-std', exe_std)
test('arrays-frg', exe_frg)
