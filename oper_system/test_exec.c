#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
int main() {
	pid_t pid=fork();

	if (pid==0){
		printf("子进程：我是PID %d,马上变身成ls\n",getpid());
		execlp("ls","ls","-l","/tmp/",NULL);
		//如果exec成功，下面这行不会执行
		printf("这行不应该出现");
	} else {
		waitpid(pid,NULL,0);
		printf("父进程:子进程(已变身成ls)执行完毕\n");
	}
	return 0;
}
