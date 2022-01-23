exe_std = executable('using-std',
	'using.cpp',
	bragi_std_gen.process('using.bragi'),
	include_directories: bragi_inc)

using_frg = executable('using-frg',
	'using.cpp',
	bragi_frg_gen.process('using.bragi'),
	include_directories: bragi_inc,
	cpp_args: '-DTEST_FRIGG',
	dependencies: frigg_dep)

test('using-std', exe_std)
test('using-frg', exe_frg)
