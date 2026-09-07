// monkey_ctrl.c — controlador via /dev/shm
// Compilar: gcc -o monkey_ctrl monkey_ctrl.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>

#define SHM_NAME "/monkey_shm"
#define SHM_SIZE 4096

int main(int argc, char *argv[]) {
    int fd = shm_open(SHM_NAME, O_RDWR, 0666);
    if (fd < 0) { perror("shm_open"); return 1; }
    char *ptr = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) { perror("mmap"); close(fd); return 1; }
    close(fd);

    if (argc >= 2) {
        snprintf(ptr, SHM_SIZE, "%s", argv[1]);
        printf("Escrito: %s\n", argv[1]);
    } else {
        printf("Estado: %s\n", ptr);
    }

    munmap(ptr, SHM_SIZE);
    return 0;
}
