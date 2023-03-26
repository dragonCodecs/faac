# SPDX-FileCopyrightText: 2023 Amyspark <amy@amyspark.me>
# SPDX-License-Identifier: BSD-3-Clause

project(
	'FAAC',
	'c', 'cpp',
	version: '1.30',
	license: 'LGPL-2.1-or-later',
	default_options: [
		'c_std=c99',
		'warning_level=1',
	]
)

compiler = meson.get_compiler('c')

dependencies = []
cdata = configuration_data()

m = compiler.find_library('m', required: false)
dependencies += m

if compiler.get_argument_syntax() == 'msvc'
	add_project_arguments(
		'-EHs',
		language: ['c', 'cpp']
	)
else
	add_project_arguments(
		'-fexceptions',
		language: ['c', 'cpp']
	)
endif

have_getopt_h = compiler.has_header('getopt.h')
have_immintrin_h = compiler.has_header('immintrin.h')

have_getopt_long = compiler.has_function('getopt_long')

use_drm = get_option('drm')

mingw = target_machine.system() ==  'windows' and (compiler.get_id() == 'gcc' or compiler.get_id() == 'clang')

cpusse = target_machine.cpu() ==  'i386' or target_machine.cpu() == 'x86_64'

# include/Makefile

faac_headers = files(
	'include/faac.h',
	'include/faaccfg.h'
)

install_headers(faac_headers)

# libfaac/Makefile

faac_srcs = files(
	'libfaac/bitstream.c',
	'libfaac/fft.c',
	'libfaac/frame.c',
	'libfaac/blockswitch.c',
	'libfaac/util.c',
	'libfaac/channels.c',
	'libfaac/filtbank.c',
	'libfaac/tns.c',
	'libfaac/quantize.c',
	'libfaac/huff2.c',
	'libfaac/huffdata.c',
	'libfaac/stereo.c',
)

faac_includes = [
	include_directories('include'),
	include_directories('libfaac'),
]

faac_args = [
	'-DPACKAGE_VERSION="@0@"'.format(meson.project_version())
]
faac_link_args = []

if cpusse
	if compiler.get_argument_syntax() == 'msvc'
		faac_link_args += compiler.get_supported_arguments('-arch:SSE2')
	else
		faac_link_args += compiler.get_supported_arguments('-msse2')
	endif
endif

if have_immintrin_h
	faac_args += '-DHAVE_IMMINTRIN_H'
endif

faac_link_args += compiler.get_supported_link_arguments('no-undefined')
if mingw
	faac_link_args += compiler.get_supported_link_arguments('-Wl,--add-stdcall-alias')
endif

makedef = find_program('packaging/makedef.py')
makedef_args = [makedef]
if compiler.get_argument_syntax() == 'msvc'
  dumpbin = find_program('dumpbin', required: true)
  makedef_args += ['--dumpbin', dumpbin]
else
  nm = find_program('nm', 'llvm-nm', required: true)
  makedef_args += ['--nm', nm]
endif
extern_prefix = compiler.symbols_have_underscore_prefix() ? '_' : ''
if target_machine.system() == 'windows'
	makedef_args += ['--prefix', extern_prefix]
	makedef_args += ['--format', 'msvc']
elif target_machine.system() == 'darwin'
	makedef_args += ['--format', 'darwin']
else
	makedef_args += ['--prefix', extern_prefix]
	makedef_args += ['--format', 'gcc']
endif

if use_drm
	faac_srcs += files(
		'libfaac/kiss_fft/kiss_fftr.c',
		'libfaac/kiss_fft/kiss_fft.c',
	)
	faac_includes += include_directories('libfaac/kiss_fft')
	faac_args += '-DDRM'

	faac_static = static_library(
		'faac_drm_static',
		faac_srcs,
		c_args: faac_args,
		include_directories: faac_includes,
		dependencies: m,
		link_args: faac_link_args,
		install: false,
	)

	vs_module_def = custom_target(
		'faac_drm_def',
		output: 'faac_drm.def',
		command: [makedef_args, faac_static],
		capture: true
	)

	faac_link_deps = []
	if target_machine.system() == 'darwin'
		faac_link_args += '-Wl,-exported_symbols_list,@0@'.format(meson.current_build_dir() / 'faac_drm.def')
		faac_link_deps += vs_module_def
	elif target_machine.system() != 'windows' and target_machine.system() != 'cygwin'
		faac_link_args += '-Wl,--version-script=@0@'.format(meson.current_build_dir() / 'faac_drm.def')
		faac_link_deps += vs_module_def
	endif

	faac = library(
		'faac_drm',
		link_whole: faac_static,
		link_args: faac_link_args,
		link_depends: faac_link_deps,
		vs_module_defs: vs_module_def,
		install: true,
	)
else
	faac_static = static_library(
		'faac_static',
		faac_srcs,
		c_args: faac_args,
		include_directories: faac_includes,
		dependencies: m,
		link_args: faac_link_args,
		install: false,
	)

	vs_module_def = custom_target(
		'faac_def',
		output: 'faac.def',
		command: [makedef_args, faac_static],
		capture: true
	)

	faac_link_deps = []
	if target_machine.system() == 'darwin'
		faac_link_args += '-Wl,-exported_symbols_list,@0@'.format(meson.current_build_dir() / 'faac.def')
		faac_link_deps += vs_module_def
	elif target_machine.system() != 'windows' and target_machine.system() != 'cygwin'
		faac_link_args += '-Wl,--version-script=@0@'.format(meson.current_build_dir() / 'faac.def')
		faac_link_deps += vs_module_def
	endif

	faac = library(
		'faac',
		link_whole: faac_static,
		link_args: faac_link_args,
		link_depends: faac_link_deps,
		vs_module_defs: vs_module_def,
		install: true,
	)
endif

faac_dep = declare_dependency(
	link_with: faac,
	dependencies: m,
	include_directories: faac_includes,
)

# common/Makefile

# frontend/Makefile

windows = import('windows')

if not use_drm
	install_man(files('docs/faac.1'))

	faac_bin_srcs = files(
		'frontend/main.c',
		'frontend/input.c',
		'frontend/mp4write.c',
	)

	if not have_getopt_h or not have_getopt_long
		faac_bin_srcs += files(
			'frontend/getopt.c',
		)
	endif

	faac_bin_deps = [
		faac_dep,
		m,
	]

	if target_machine.system() ==  'windows'
		faac_bin_deps += [
			compiler.find_library('ws2_32', required: true),
		]
	endif

	faac_bin_includes = [
		include_directories('include'),
		include_directories('frontend'),
	]

	faac_bin = executable(
		'faac',
		c_args: '-DHAVE_GETOPT_H',
		faac_bin_srcs,
		include_directories: faac_bin_includes,
		dependencies: faac_bin_deps,
		install: true,
	)
	
	if target_machine.system() ==  'windows'
		faac_gui_srcs = files(
			'frontend/maingui.c',
			'frontend/input.c',
		)

		faac_gui_deps = faac_bin_deps + compiler.find_library('comdlg32', required: true)

		faac_gui_srcs += [
			windows.compile_resources('frontend/faacgui.rc'),
			windows.compile_resources('frontend/icon.rc',
				depend_files: files('frontend/faac.ico')
			),
		]

		faacgui = executable(
			'faacgui',
			faac_gui_srcs,
			include_directories: faac_bin_includes,
			dependencies: faac_gui_deps,
			install: true,
		)
	endif
endif

pkg = import('pkgconfig')

pkg.generate(
	faac,
	description: 'Freeware Advanced Audio Coder' 
)
