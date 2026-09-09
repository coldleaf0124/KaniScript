#include "std.h"

// 汎用 2桁LUT itoa (prefix特化ではなく、純粋な int64 -> 文字列)
static const char DIGITS_LUT[200] =
    "0001020304050607080910111213141516171819"
    "2021222324252627282930313233343536373839"
    "4041424344454647484950515253545556575859"
    "6061626364656667686970717273747576777879"
    "8081828384858687888990919293949596979899";

static inline char* zp_fast_int_to_str_generic(int64_t n) {
    char* buf = (char*)zp_alloc_scratch(24);
    char temp[24];
    int p = 0;
    bool neg = false;
    uint64_t val;
    if (n < 0) {
        neg = true;
        val = (uint64_t)(-n);
    } else {
        val = (uint64_t)n;
    }
    
    while (val >= 100) {
        uint64_t q = val / 100;
        uint64_t r = val - (q * 100);
        val = q;
        temp[p++] = DIGITS_LUT[r * 2 + 1];
        temp[p++] = DIGITS_LUT[r * 2];
    }
    if (val < 10) {
        temp[p++] = (char)('0' + val);
    } else {
        temp[p++] = DIGITS_LUT[val * 2 + 1];
        temp[p++] = DIGITS_LUT[val * 2];
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
    const char* last = "";
    
    for (int64_t i = 1; i <= 1000000; i++) {
        size_t mark = zp_scratch_mark();
        // 汎用的な結合 (特化結合 zp_concat_prefix_int は使わない!)
        // 1. 汎用高速 itoa (Scratch確保)
        // 2. 汎用 str_concat (strlen x 2 + Scratch確保)
        const char* s = zp_str_concat("item_id_", zp_fast_int_to_str_generic(i));
        
        if (i == 1000000) {
            last = zp_promote(s);
        }
        zp_scratch_reset(mark);
    }
    
    puts("last=");
    puts(last);
    printf("Perm offset: %zu bytes\n", g_zp_perm.offset);
    printf("Scratch offset: %zu bytes\n", g_zp_scratch.offset);
    return 0;
}
