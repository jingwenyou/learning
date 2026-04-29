#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int global_init = 42;
int global_uninit;

int main(){
	int local = 0;
	void *heap = malloc(64);
	printf("代码段(main函数)： %p\n",(void*)main);
	printf("数据段(global_init): %p\n",(void*)&global_init);
	printf("BSS段(global_uninit): %p\n",(void*)&global_uninit);
	printf("栈(local变量)：%p\n",(void*)&local);
	printf("堆(malloc): %p\n",heap);
	free(heap);
	return 0;
}
