// simple_tcp_server.cpp
// Minimal TCP echo server (IPv4, POSIX sockets)
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>

constexpr int PORT = 12345;
constexpr int BACKLOG = 5;
constexpr int BUF_SIZE = 1024;

int main() {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return 1;
    }

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    if (bind(server_fd, (sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return 1;
    }

    if (listen(server_fd, BACKLOG) < 0) {
        perror("listen");
        close(server_fd);
        return 1;
    }

    std::cout << "Echo server listening on port " << PORT << std::endl;
    while (true) {
        sockaddr_in client_addr{};
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (sockaddr*)&client_addr, &client_len);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }
        char buf[BUF_SIZE];
        ssize_t n = read(client_fd, buf, BUF_SIZE);
        if (n > 0) {
            write(client_fd, buf, n); // Echo back
        }
        close(client_fd);
    }
    close(server_fd);
    return 0;
}
