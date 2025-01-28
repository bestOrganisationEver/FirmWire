#include "time.h"

#include "qemu/osdep.h"
#include "sysemu/sysemu.h"

#include "hw/avatar/avatar_posix.h"

static void error_exit(const char *msg)
{
    fprintf(stderr, "qemu: %s\n", msg);
    abort();
}

static void errno_exit(int err, const char *msg)
{
    fprintf(stderr, "qemu: %s: %s\n", msg, strerror(err));
    abort();
}

void qemu_avatar_sem_open(QemuAvatarSemaphore *sem, const char *name)
{
#if defined(__NetBSD__)
#else
    sem_unlink(name);
    sem_t *rc = sem_open(name, O_CREAT, S_IRUSR | S_IWUSR, 1);

    if(rc == SEM_FAILED) {
        errno_exit(errno, __func__);
    }

    sem->sem = rc;
#endif
}

void qemu_avatar_sem_wait(QemuAvatarSemaphore *sem) {
#if defined(__NetBSD__)
#else
  int rc = sem_wait(sem->sem);
  if (rc < 0) {
    errno_exit(errno, __func__);
  }
#endif
}

void qemu_avatar_sem_post(QemuAvatarSemaphore *sem) {
#if defined(__NetBSD__)
#else
  int rc = sem_post(sem->sem);
  if (rc < 0) {
    errno_exit(errno, __func__);
  }
#endif
}

void qemu_avatar_mq_open_read(QemuAvatarMessageQueue *mq, const char *name,
                              size_t msg_size) {
    int ret;
    char filename[256];

    if (name[0] == '/') {
        name++;
    }

    int needed =
        snprintf(filename, sizeof(filename), "/tmp/avatar2.sockmq.%s.sock", name);

    if (!(needed >= 0 && needed < sizeof(filename))) {
        error_exit("needed message queue name is too long!");
    }

    unlink(filename);

    int sock_fd = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (sock_fd == -1) {
        errno_exit(errno, "Could not create Avatar mq socket!");
    }

    int flags = fcntl(sock_fd, F_GETFL, 0);
    ret = fcntl(sock_fd, F_SETFL, flags | O_NONBLOCK);
    if (ret == -1) {
        errno_exit(errno, "Could not set options on the mq socket!");
    }

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, filename, sizeof(addr.sun_path) - 1);

    ret = bind(sock_fd, (const struct sockaddr *)&addr, sizeof(addr));
    if (ret == -1) {
        errno_exit(errno, "Could not bind to Avatar mq socket!");
    }

    // if (listen(sock_fd, 10) == -1) {
    //     error_exit(errno, "Could not listen on Avatar mq socket!");
    // }

    mq->sock_fd = sock_fd;
}

void qemu_avatar_mq_open_write(QemuAvatarMessageQueue *mq, const char *name,
                               size_t msg_size) {
    int ret;
    int tries;

    char filename[256];

    if (name[0] == '/') {
        name++;
    }

    int needed =
        snprintf(filename, sizeof(filename), "/tmp/avatar2.sockmq.%s.sock", name);

    if (!(needed >= 0 && needed < sizeof(filename))) {
        error_exit("needed message queue name is too long!");
    }

    unlink(filename);

    int sock_fd = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (sock_fd == -1) {
        errno_exit(errno, "Could not create Avatar mq socket!");
    }

    // int flags = fcntl(sock_fd, F_GETFL, 0);
    // ret = fcntl(sock_fd, F_SETFL, flags | O_NONBLOCK);
    // if (ret == -1) {
    //     error_exit(errno, "Could not set options on the mq socket!");
    // }

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, filename, sizeof(addr.sun_path) - 1);

    ret = -1;
    tries = 0;

    const struct timespec rqtp = {.tv_sec = 0, .tv_nsec = 2e8};
    while (ret == -1 && tries < 50) {
        ret = connect(sock_fd, (const struct sockaddr *)&addr, sizeof(addr));
        nanosleep(&rqtp, NULL);
        tries++;
    }

    if (ret == -1) {
        errno_exit(errno, "Could not connect to Avatar mq socket!");
    }

  // if (listen(sock_fd, 10) == -1) {
  //     error_exit(errno, "Could not listen on Avatar mq socket!");
  // }

  // struct mq_attr attr;
  // attr.mq_msgsize = msg_size;
  // attr.mq_maxmsg = 10;
  // attr.mq_curmsgs = 0;

  // mqd_t m = mq_open(name, O_CREAT | O_EXCL | O_WRONLY, 0600, &attr);

  // if(m == -1)
  // {
  //     error_exit(errno, __func__);
  // }

  mq->sock_fd = sock_fd;
  // #endif
}

void qemu_avatar_mq_send(QemuAvatarMessageQueue *mq, void *msg, size_t len) {
  // #if defined(__APPLE__) || defined(__NetBSD__)
  // #else
  // while (!mq->is_connected) {
  //     connect(int, const struct sockaddr *, socklen_t)
  // }

  int rc = send(mq->sock_fd, msg, len, /* flags */ 0);

  if (rc < 0) {
    errno_exit(errno, __func__);
  }
  // #endif
}

int qemu_avatar_mq_receive(QemuAvatarMessageQueue *mq, void *buffer,
                           size_t len) {
  // #if defined(__APPLE__) || defined(__NetBSD__)
  // #else
  int rc = -1;
  struct timeval tv;
  tv.tv_sec = 1;
  tv.tv_usec = 0;
  setsockopt(mq->sock_fd, SOL_SOCKET, SO_RCVTIMEO, (const char *)&tv,
             sizeof tv);

  /* In corner cases, a shutdown of qemu is requested while an mq_receive
   * would block. Hence, the repeated mq_timedreceive */
  while (!qemu_shutdown_requested_get()) {
    rc = recv(mq->sock_fd, buffer, len, 0);

    if (rc > 0) {
      break;
    }

    if (rc < 0 && errno == ETIMEDOUT) {
      continue;
    } else if (rc < 0 && errno != EAGAIN) {
      errno_exit(errno, __func__);
    }
  }

  return rc;
  // #endif
}

int qemu_avatar_mq_get_fd(QemuAvatarMessageQueue *mq) { return mq->sock_fd; }

