#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

static inline char* fast_i64_to_str(char* buf, int64_t n) {
    char temp[24];
    int p = 0;
    bool neg = false;
    if (n < 0) { neg = true; n = -n; }
    if (n == 0) { temp[p++] = '0'; }
    else {
        while (n > 0) {
            temp[p++] = '0' + (char)(n % 10);
            n /= 10;
        }
    }
    int out_p = 0;
    if (neg) buf[out_p++] = '-';
    for (int i = p - 1; i >= 0; i--) {
        buf[out_p++] = temp[i];
    }
    buf[out_p] = '\0';
    return buf;
}

int main() {
    char buf[32];
    fast_i64_to_str(buf, 1000000);
    printf("res=%s\n", buf);
    return 0;
}
