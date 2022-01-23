exe_std = executable('basic-std',
	'basic.cpp',
	bragi_std_gen.process('basic.bragi'),
	include_directories: bragi_inc)

exe_frg = executable('basic-frg',
	'basic.cpp',
	bragi_frg_gen.process('basic.bragi'),
	include_directories: bragi_inc,
	cpp_args: '-DTEST_FRIGG',
	dependencies: frigg_dep)

test('basic-std', exe_std)
test('basic-frg', exe_frg)
