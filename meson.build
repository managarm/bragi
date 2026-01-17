project('bragi', default_options: ['cpp_std=c++2a'], meson_version: '>=1.3.0')

bragi_inc = include_directories('include')
bragi_dep = declare_dependency(include_directories: bragi_inc)

if get_option('install_headers')
	pkgconfig = import('pkgconfig')

	install_headers(
		'include/bragi/internals.hpp',
		'include/bragi/helpers-all.hpp',
		'include/bragi/helpers-std.hpp',
		'include/bragi/helpers-frigg.hpp',
		subdir: 'bragi/')

	pkgconfig.generate(
		name: 'bragi',
		description: 'A small and efficient IDL language',
		version: meson.project_version(),
	)
endif

if get_option('build_tests')
	add_languages('cpp')
	subdir('tests')
endif
