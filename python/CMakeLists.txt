cmake_minimum_required(VERSION 3.5)

project(toptek_control VERSION 1.0.0)

find_package(Python REQUIRED)
execute_process(
	COMMAND ${Python_EXECUTABLE} -c
	"from distutils import sysconfig as sc; print(sc.get_python_lib(prefix='', plat_specific=True))"
	OUTPUT_VARIABLE PYTHON_SITE
	OUTPUT_STRIP_TRAILING_WHITESPACE
)

install(FILES __init__.py toptek.py
	DESTINATION ${PYTHON_SITE}/${PROJECT_NAME})

set(CPACK_PACKAGE_CONTACT "Reid Sox-Harris <reidsox1@gmail.com>")
include(CPack)
