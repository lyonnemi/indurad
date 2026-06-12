if( NOT ANDROID )
    set( BUILD_TESTING ON )
else()
    # the monolith test suite is currently not compatible with libc++.
    set( BUILD_TESTING OFF )
endif()

set( IFRAMEWORK_ENABLE_COREDUMP ON )
set( IFRAMEWORK_ENABLE_CRASH_HANDLER ON )
