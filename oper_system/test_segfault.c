#include <stdio.h>
int main(){
	int *p=NULL;
	printf("准备访问NULL指针...\n");
	*p=42;
	printf("这行不会被执行\n");
	return 0;
}
