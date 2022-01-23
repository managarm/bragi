exe_std = executable('empty-std',
	'empty.cpp',
	bragi_std_gen.process('empty.bragi'),
	include_directories: bragi_inc)

exe_frg = executable('empty-frg',
	'empty.cpp',
	bragi_frg_gen.process('empty.bragi'),
	include_directories: bragi_inc,
	cpp_args: '-DTEST_FRIGG',
	dependencies: frigg_dep)

test('empty-std', exe_std)
test('empty-frg', exe_frg)
