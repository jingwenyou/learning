#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main() {
	pid_t pid =fork();

	if (pid==0) {
		printf("子进程：我的PID是%d\n",getpid());
		printf("子进程：fork返回值是%d\n",pid);
		printf("子进程：父进程的PID是%d\n",getppid());
		return 0;
	} else {
		printf("父进程：fork返回值是%d(=子进程PID)\n",pid);
		printf("父进程：我的PID是%d\n",getpid());
		waitpid(pid,NULL,0);
		printf("父进程：子进程已退出，已回收\n");
	}
	return 0;
}
