#include "std.h"

static inline char* zp_fast_int_to_str(int64_t n) {
    char* buf = (char*)zp_alloc_scratch(32);
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
    zp_arena_init(16 * 1024 * 1024, 4 * 1024 * 1024);
    const char* last = zp_promote("");
    for (int64_t i = 1; i < 1000001; i++) {
        size_t __zp_tmp1 = zp_scratch_mark();
        const char* s = zp_str_concat("item_id_", zp_fast_int_to_str(i));
        if (i == 1000000) {
            last = zp_promote(s);
        }
        zp_scratch_reset(__zp_tmp1);
    }
    puts("last=");
    puts(last);
    return 0;
}
