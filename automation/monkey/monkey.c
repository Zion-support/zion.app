// monkey.c — injeta caracteres aleatórios via write(2) no master fd do PTY
// Compilar Linux: gcc -o monkey monkey.c -lrt
// Compilar macOS: gcc -o monkey monkey.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <signal.h>
#include <errno.h>
#include <stdarg.h>
#include <util.h>

#define SHM_NAME  "/monkey_shm"
#define SHM_SIZE  4096
#define BUF_SIZE  256
#define DEFAULT_DELAY_US 50000

static volatile sig_atomic_t running = 1;
static int  master_fd = -1;
static char *shm_ptr  = NULL;

static void handle_sigint(int sig)  { (void)sig; running = 0; }
static void handle_sigterm(int sig) { (void)sig; running = 0; }

static int shm_init(void) {
    shm_unlink(SHM_NAME);  // garantir objeto limpo (evita ftruncate: Invalid argument)
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    if (fd < 0) { perror("shm_open"); return -1; }
    if (ftruncate(fd, SHM_SIZE) < 0) { perror("ftruncate"); close(fd); return -1; }
    char *ptr = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) { perror("mmap"); close(fd); return -1; }
    close(fd);
    memset(ptr, 0, SHM_SIZE);
    shm_ptr = ptr;
    return 0;
}

static char slave_path_shm[256] = {0};

static void shm_write_status(const char *fmt, ...) {
    if (!shm_ptr) return;
    // Preservar linha do slave_path (primeira linha do shm) se existir
    char slave_line[256] = {0};
    char *nl = strchr(shm_ptr, '\n');
    if (nl && nl - shm_ptr < (int)sizeof(slave_line)) {
        size_t len = nl - shm_ptr;
        if (len > 0 && strncmp(shm_ptr, "slave=", 6) == 0) {
            memcpy(slave_line, shm_ptr, len);
            slave_line[len] = '\0';
        }
    }
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(shm_ptr, SHM_SIZE, fmt, ap);
    va_end(ap);
    // Restaurar linha do slave_path se estava presente
    if (slave_line[0]) {
        // Inserir slave_line no início do buffer, mantendo o status após
        int status_len = strlen(shm_ptr);
        if (status_len + (int)strlen(slave_line) + 1 < SHM_SIZE) {
            memmove(shm_ptr + strlen(slave_line) + 1, shm_ptr, status_len + 1);
            memcpy(shm_ptr, slave_line, strlen(slave_line));
            shm_ptr[strlen(slave_line)] = '\n';
        }
    }
}

static void shm_write_slave(const char *path) {
    if (!shm_ptr || !path) return;
    // Manter slave_path sempre visível no shm, separado do status de execução
    int len = snprintf(shm_ptr, SHM_SIZE, "slave=%s\n", path);
    if (len > 0 && len < SHM_SIZE) {
        // Preencher o restante com null para garantir terminação
        memset(shm_ptr + len, 0, SHM_SIZE - len);
    }
}

static int open_pty_master(const char *path) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) {
        fprintf(stderr, "Erro ao abrir %s: %s\n", path, strerror(errno));
        return -1;
    }
    return fd;
}

static void monkey_run(int fd, int delay_us) {
    static const char charset[] =
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "!@#$%^&*()-_=+[]{}|;:',.<>?/`~"
        "\n\r\t ";
    const size_t nchars = sizeof(charset) - 1;
    char buf[BUF_SIZE];
    ssize_t written = 0;
    int count = 0;

    // Injetar TEST_MESSAGE logo no início para garantir visibilidade imediata ao worker
    // (evita race condition com worker que pode começar a ler antes do count>=20)
    const char *test_msg = "MONKEY_INTEGRATION_TEST_STRING_12345\n";
    {
        ssize_t n = write(fd, test_msg, strlen(test_msg));
        if (n > 0) {
            written += n;
            shm_write_status("status:running, fd:%d, delay:%dus, TEST_MESSAGE injected at start", fd, delay_us);
        }
    }

    while (running) {
        for (int i = 0; i < (int)(sizeof(buf) - 1); i++)
            buf[i] = charset[rand() % nchars];
        buf[sizeof(buf) - 1] = '\0';

        ssize_t n = write(fd, buf, sizeof(buf) - 1);
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                usleep(delay_us * 2);
                continue;
            }
            perror("write");
            shm_write_status("status:error, write failed: %s", strerror(errno));
            break;
        }
        written += n;
        count++;
        if (count % 1000 == 0)
            shm_write_status("status:running, chars:%zd, writes:%d", written, count);
        usleep(delay_us);
    }

    shm_write_status("status:stopped, chars:%zd, writes:%d", written, count);
}

int main(int argc, char *argv[]) {
    int delay_us = (argc >= 2) ? atoi(argv[1]) : DEFAULT_DELAY_US;

    srand((unsigned)time(NULL) ^ (unsigned)getpid());
    signal(SIGINT,  handle_sigint);
    signal(SIGTERM, handle_sigterm);

    if (shm_init() < 0) {
        fprintf(stderr, "Falha shm_init\n");
        return 1;
    }

    int slave_fd = -1;
    char slave_name[256] = {0};
    if (openpty(&master_fd, &slave_fd, slave_name, NULL, NULL) < 0) {
        perror("openpty");
        shm_write_status("status:error, openpty failed");
        munmap(shm_ptr, SHM_SIZE);
        shm_unlink(SHM_NAME);
        return 1;
    }

    const char *slave_path = ttyname(slave_fd);
    if (!slave_path) {
        slave_path = slave_name[0] ? slave_name : "unknown";
    }
    shm_write_slave(slave_path);
    shm_write_status("status:ready, fd=%d, delay=%dus", master_fd, delay_us);

    monkey_run(master_fd, delay_us);

    close(master_fd);
    if (slave_fd >= 0) close(slave_fd);
    munmap(shm_ptr, SHM_SIZE);
    shm_unlink(SHM_NAME);
    return 0;
}
