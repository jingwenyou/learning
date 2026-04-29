/* week01: 基本数据类型实验
 * 目标：理解各类型的大小、范围、格式化输出
 * 编译: gcc -Wall -Wextra -o types types.c
 */
#include <stdio.h>
#include <limits.h>   /* INT_MAX, CHAR_MAX 等常量 */
#include <float.h>    /* FLT_MAX, DBL_MAX 等常量 */

int main(void) {
    /* 整数类型 */
    char   c = 'A';
    int    i = 42;
    long   l = 1234567890L;

    /* 浮点类型 */
    float  f = 3.14f;
    double d = 3.14159265358979;

    /* 无符号类型 */
    unsigned int u = 4294967295U;   /* UINT_MAX */

    printf("=== 类型大小 ===\n");
    printf("char:          %zu 字节\n", sizeof(char));
    printf("int:           %zu 字节\n", sizeof(int));
    printf("long:          %zu 字节\n", sizeof(long));
    printf("float:         %zu 字节\n", sizeof(float));
    printf("double:        %zu 字节\n", sizeof(double));
    printf("unsigned int:  %zu 字节\n", sizeof(unsigned int));

    printf("\n=== 值与范围 ===\n");
    printf("char   c = '%c'  (ASCII %d)\n", c, c);
    printf("int    i = %d    (最大 %d)\n", i, INT_MAX);
    printf("long   l = %ld\n", l);
    printf("float  f = %.2f  (最大 %.2e)\n", f, FLT_MAX);
    printf("double d = %.15f\n", d);
    printf("uint   u = %u    (最大 %u)\n", u, UINT_MAX);

    printf("\n=== 类型转换陷阱 ===\n");
    int overflow = INT_MAX + 1;   /* 有符号溢出，未定义行为，观察实际输出 */
    printf("INT_MAX + 1 = %d  (溢出了！)\n", overflow);

    unsigned int wrap = 0u - 1u;  /* 无符号回绕，行为定义良好 */
    printf("0u - 1u     = %u  (无符号回绕)\n", wrap);

    return 0;
}
