cmake_minimum_required(VERSION 3.5)

project(toptek VERSION 1.0.0)

find_package(Python REQUIRED)

install(DIRECTORY toptek
	DESTINATION ${Python_SITELIB})

set(CPACK_PACKAGE_CONTACT "Reid Sox-Harris <reidsox1@gmail.com>")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "python3-serial")
set(CPACK_RPM_PACKAGE_REQUIRES "python3-pyserial")
set(CPACK_PACKAGE_FILE_NAME "${PROJECT_NAME}-${PROJECT_VERSION}")
include(CPack)
