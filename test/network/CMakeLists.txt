
add_executable(simple_tcp_server
    simple_tcp_server.cpp
)


# Install executables
install(TARGETS simple_tcp_server

    RUNTIME DESTINATION bin/tests
)
