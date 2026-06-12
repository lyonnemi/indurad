cmake_minimum_required( VERSION "${CMAKE_VERSION}" )
project( test-project )

# import C++ standard from environment variable
set( CMAKE_CXX_STANDARD $ENV{TOOLCHAIN_CI_CMAKE_CXX_STANDARD} )

if( NOT CMAKE_CXX_STANDARD )
	message( FATAL_ERROR "TOOLCHAIN_CI_CMAKE_CXX_STANDARD must be set via environment variable." )
endif()

set( TOOLCHAIN_CI_MONOLITH_REVISION $ENV{TOOLCHAIN_CI_MONOLITH_REVISION} )
if( NOT TOOLCHAIN_CI_MONOLITH_REVISION )
	message( FATAL_ERROR "TOOLCHAIN_CI_MONOLITH_REVISION must be set." )
endif()

include( defaults.cmake )
include( ${MONOLITH_DIR}/project_defaults.cmake )
add_subdirectory( ${MONOLITH_DIR} monolith )

# Generate 'project.version'
# Its content will be used by calvin to generate artifact name when compiling
# the SOFTFS image output.
string( REPLACE "." "_" CLEAN_TOOLCHAIN_CI_MONOLITH_REVISION "${TOOLCHAIN_CI_MONOLITH_REVISION}" )
string( REPLACE "/" "_" CLEAN_TOOLCHAIN_CI_MONOLITH_REVISION "${CLEAN_TOOLCHAIN_CI_MONOLITH_REVISION}" )
configure_file( project.version.in project.version )
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/project.version DESTINATION . )
