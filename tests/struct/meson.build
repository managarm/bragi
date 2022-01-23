exe_std = executable('struct-std',
	'struct.cpp',
	bragi_std_gen.process('struct.bragi'),
	include_directories: bragi_inc)

exe_frg = executable('struct-frg',
	'struct.cpp',
	bragi_frg_gen.process('struct.bragi'),
	include_directories: bragi_inc,
	cpp_args: '-DTEST_FRIGG',
	dependencies: frigg_dep)

test('struct-std', exe_std)
test('struct-frg', exe_frg)
