project('bragi', 'cpp', default_options: ['cpp_std=c++2a'])

bragi_inc = include_directories('include')
bragi_dep = declare_dependency(include_directories: bragi_inc)

if get_option('install_headers')
	install_headers(
		'bragi/internals.hpp',
		'bragi/helpers-all.hpp',
		'bragi/helpers-std.hpp',
		'bragi/helpers-frigg.hpp',
		subdir: 'bragi/')
endif

if get_option('build_tests')
	subdir('tests')
endif
