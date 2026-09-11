/*
 * KaniScript Standard Library (std.h)
 * C11ベースの軽量・高性能・2層アリーナランタイム
 */

#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <errno.h>

static inline double zp_time_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* ===== パニック機構 (未定義動作の排除) ===== */

static inline void zp_panic(const char* msg) {
    fprintf(stderr, "\n[KaniScript PANIC] %s\n", msg);
    abort();
}

/* ゼロ除算・剰余の明示的防止 */
static inline int64_t zp_div_i64(int64_t a, int64_t b) {
    if (b == 0) zp_panic("division by zero");
    return a / b;
}

static inline int64_t zp_mod_i64(int64_t a, int64_t b) {
    if (b == 0) zp_panic("modulo by zero");
    return a % b;
}

/* ===== 2層アリーナアロケータ (Persistent & Scratch) ===== */

typedef struct {
    char*  buffer;
    size_t capacity;
    size_t offset;
} zp_arena_t;

static zp_arena_t g_zp_perm    = { NULL, 0, 0 }; // 永続領域 (変数・structフィールド・戻り値)
static zp_arena_t g_zp_scratch = { NULL, 0, 0 }; // 一時領域 (ループ内演算・式の中間値)

static inline void zp_arena_init(size_t perm_cap, size_t scratch_cap) {
    if (g_zp_perm.buffer == NULL) {
        g_zp_perm.buffer = (char*)malloc(perm_cap);
        if (!g_zp_perm.buffer) zp_panic("Out of memory for Perm Arena");
        g_zp_perm.capacity = perm_cap;
        g_zp_perm.offset = 0;
    }
    if (g_zp_scratch.buffer == NULL) {
        g_zp_scratch.buffer = (char*)malloc(scratch_cap);
        if (!g_zp_scratch.buffer) zp_panic("Out of memory for Scratch Arena");
        g_zp_scratch.capacity = scratch_cap;
        g_zp_scratch.offset = 0;
    }
}

static inline void* zp_alloc_scratch(size_t size) {
    size_t aligned = (size + 7) & ~7;
    if (__builtin_expect(g_zp_scratch.buffer == NULL, 0)) {
        zp_arena_init(32 * 1024 * 1024, 32 * 1024 * 1024);
    }
    if (__builtin_expect(g_zp_scratch.offset + aligned > g_zp_scratch.capacity, 0)) {
        // 動的倍増リサイズ
        size_t new_cap = g_zp_scratch.capacity ? g_zp_scratch.capacity * 2 : (32 * 1024 * 1024);
        while (new_cap < g_zp_scratch.offset + aligned) new_cap *= 2;
        char* new_buf = (char*)realloc(g_zp_scratch.buffer, new_cap);
        if (!new_buf) zp_panic("Scratch Arena out of memory");
        g_zp_scratch.buffer = new_buf;
        g_zp_scratch.capacity = new_cap;
    }
    void* ptr = g_zp_scratch.buffer + g_zp_scratch.offset;
    g_zp_scratch.offset += aligned;
    return ptr;
}

static inline void* zp_alloc_perm(size_t size) {
    size_t aligned = (size + 7) & ~7;
    if (__builtin_expect(g_zp_perm.buffer == NULL, 0)) {
        zp_arena_init(32 * 1024 * 1024, 32 * 1024 * 1024);
    }
    if (__builtin_expect(g_zp_perm.offset + aligned > g_zp_perm.capacity, 0)) {
        size_t new_cap = g_zp_perm.capacity ? g_zp_perm.capacity * 2 : (32 * 1024 * 1024);
        while (new_cap < g_zp_perm.offset + aligned) new_cap *= 2;
        char* new_buf = (char*)realloc(g_zp_perm.buffer, new_cap);
        if (!new_buf) zp_panic("Perm Arena out of memory");
        g_zp_perm.buffer = new_buf;
        g_zp_perm.capacity = new_cap;
    }
    void* ptr = g_zp_perm.buffer + g_zp_perm.offset;
    g_zp_perm.offset += aligned;
    return ptr;
}

/* Scratch アリーナの LIFO 巻き戻し */
static inline size_t zp_scratch_mark(void) {
    return g_zp_scratch.offset;
}

static inline void zp_scratch_reset(size_t mark) {
    if (mark <= g_zp_scratch.offset) {
        g_zp_scratch.offset = mark;
    }
}

static inline int64_t zp_perm_used(void) {
    return (int64_t)g_zp_perm.offset;
}

static inline int64_t zp_scratch_used(void) {
    return (int64_t)g_zp_scratch.offset;
}

/* ===== プロモーション (Scratch から Perm への安全退避) ===== */

static inline const char* zp_promote(const char* s) {
    if (!s) return NULL;
    // s が Scratch アリーナ内にある場合のみ、Perm へ退避コピー
    if (g_zp_scratch.buffer &&
        s >= g_zp_scratch.buffer &&
        s < g_zp_scratch.buffer + g_zp_scratch.capacity) {
        size_t len = strlen(s);
        char* p = (char*)zp_alloc_perm(len + 1);
        memcpy(p, s, len + 1);
        return p;
    }
    return s; // リテラルや既に Perm にある文字列はそのまま即座に返す (O(1))
}

/* ===== 文字列操作 (中間計算はすべて Scratch から高速確保) ===== */

/* 2桁ルックアップテーブル (除算回数を半減させる高速 itoa) */
static const char ZP_DIGITS_LUT[200] =
    "0001020304050607080910111213141516171819"
    "2021222324252627282930313233343536373839"
    "4041424344454647484950515253545556575859"
    "6061626364656667686970717273747576777879"
    "8081828384858687888990919293949596979899";

static inline char* zp_int_to_str(int64_t n) {
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
        temp[p++] = ZP_DIGITS_LUT[r * 2 + 1];
        temp[p++] = ZP_DIGITS_LUT[r * 2];
    }
    if (val < 10) {
        temp[p++] = (char)('0' + val);
    } else {
        temp[p++] = ZP_DIGITS_LUT[val * 2 + 1];
        temp[p++] = ZP_DIGITS_LUT[val * 2];
    }
    int out_p = 0;
    if (neg) buf[out_p++] = '-';
    for (int i = p - 1; i >= 0; i--) {
        buf[out_p++] = temp[i];
    }
    buf[out_p] = '\0';
    return buf;
}

static inline char* zp_float_to_str(double n) {
    char* buf = (char*)zp_alloc_scratch(64);
    snprintf(buf, 64, "%g", n);
    return buf;
}

static inline char* zp_str_concat(const char* a, const char* b) {
    size_t la = strlen(a), lb = strlen(b);
    char* buf = (char*)zp_alloc_scratch(la + lb + 1);
    memcpy(buf, a, la);
    memcpy(buf + la, b, lb);
    buf[la + lb] = '\0';
    return buf;
}

/* ===== Result型 (MVP: エラーは const char*) ===== */

typedef struct {
    bool ok;
    int64_t val;
    const char* err;
} zp_result_i64_t;

typedef struct {
    bool ok;
    const char* val;
    const char* err;
} zp_result_str_t;

static inline zp_result_i64_t zp_ok_i64(int64_t val) {
    zp_result_i64_t r = { true, val, NULL };
    return r;
}

static inline zp_result_i64_t zp_err_i64(const char* err) {
    zp_result_i64_t r = { false, 0, err };
    return r;
}

/* ===== 数学関数 ===== */

static inline double  zp_sqrt(double x)           { return sqrt(x); }
static inline double  zp_pow(double x, double y)  { return pow(x, y); }
static inline double  zp_abs_f64(double x)        { return fabs(x); }
static inline int64_t zp_abs_i64(int64_t x)       { return x < 0 ? -x : x; }

/* ===== 動的スライス / リスト (Lists & Slices) ===== */

typedef struct {
    const char** data;
    size_t len;
    size_t cap;
} zp_list_str_t;

typedef struct {
    int64_t* data;
    size_t len;
    size_t cap;
} zp_list_i64_t;

static inline zp_list_str_t zp_list_str_promote(zp_list_str_t l) {
    if (l.len == 0 || !l.data) return l;
    const char** new_data = (const char**)zp_alloc_perm(l.len * sizeof(const char*));
    for (size_t i = 0; i < l.len; i++) {
        new_data[i] = zp_promote(l.data[i]);
    }
    l.data = new_data;
    l.cap = l.len;
    return l;
}

/* ===== ファイル I/O ===== */

static inline const char* zp_read_file(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) return "";
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz < 0) { fclose(f); return ""; }
    char* buf = (char*)zp_alloc_scratch((size_t)sz + 1);
    size_t read_bytes = fread(buf, 1, (size_t)sz, f);
    buf[read_bytes] = '\0';
    fclose(f);
    return buf;
}

static inline bool zp_write_file(const char* path, const char* content) {
    FILE* f = fopen(path, "wb");
    if (!f) return false;
    size_t len = strlen(content);
    size_t written = fwrite(content, 1, len, f);
    fclose(f);
    return written == len;
}

/* ===== 実用文字列ユーティリティ ===== */

static inline const char* zp_trim(const char* s) {
    if (!s) return "";
    while (*s == ' ' || *s == '\t' || *s == '\r' || *s == '\n') {
        s++;
    }
    if (*s == '\0') return "";
    const char* end = s + strlen(s) - 1;
    while (end > s && (*end == ' ' || *end == '\t' || *end == '\r' || *end == '\n')) {
        end--;
    }
    size_t len = (size_t)(end - s + 1);
    char* buf = (char*)zp_alloc_scratch(len + 1);
    memcpy(buf, s, len);
    buf[len] = '\0';
    return buf;
}

static inline int64_t zp_parse_i64(const char* s) {
    if (!s) return 0;
    while (*s == ' ' || *s == '\t' || *s == '\r' || *s == '\n') s++;
    int64_t sign = 1;
    if (*s == '-') { sign = -1; s++; }
    else if (*s == '+') { s++; }
    int64_t val = 0;
    while (*s >= '0' && *s <= '9') {
        val = val * 10 + (*s - '0');
        s++;
    }
    return val * sign;
}

static inline double zp_parse_f64(const char* s) {
    if (!s) return 0.0;
    return strtod(s, NULL);
}

static inline zp_list_str_t zp_split(const char* s, const char* sep) {
    zp_list_str_t list = { NULL, 0, 0 };
    if (!s || !sep) return list;
    size_t sep_len = strlen(sep);
    if (sep_len == 0) return list;

    size_t cap = 16;
    list.data = (const char**)zp_alloc_scratch(cap * sizeof(const char*));
    list.cap = cap;
    list.len = 0;

    const char* p = s;
    while (*p) {
        const char* next = (sep_len == 1) ? strchr(p, sep[0]) : strstr(p, sep);
        size_t tok_len = next ? (size_t)(next - p) : strlen(p);

        char* tok = (char*)zp_alloc_scratch(tok_len + 1);
        memcpy(tok, p, tok_len);
        tok[tok_len] = '\0';

        if (__builtin_expect(list.len >= list.cap, 0)) {
            size_t new_cap = list.cap * 2;
            const char** new_data = (const char**)zp_alloc_scratch(new_cap * sizeof(const char*));
            memcpy(new_data, list.data, list.len * sizeof(const char*));
            list.data = new_data;
            list.cap = new_cap;
        }
        list.data[list.len++] = tok;

        if (!next) break;
        p = next + sep_len;
    }
    return list;
}

static inline const char* zp_read_line(void) {
    char buf[512];
    if (!fgets(buf, sizeof(buf), stdin)) {
        return "";
    }
    size_t len = strlen(buf);
    while (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r')) {
        buf[--len] = '\0';
    }
    char* res = (char*)zp_alloc_scratch(len + 1);
    memcpy(res, buf, len + 1);
    return res;
}

/* ===== 文字列検索・スライス ===== */
static inline const char* zp_substr(const char* s, int64_t start, int64_t len) {
    if (!s) return "";
    size_t s_len = strlen(s);
    if (start < 0 || (size_t)start >= s_len || len <= 0) return "";
    size_t actual_len = (size_t)len;
    if ((size_t)start + actual_len > s_len) {
        actual_len = s_len - (size_t)start;
    }
    char* buf = (char*)zp_alloc_scratch(actual_len + 1);
    memcpy(buf, s + start, actual_len);
    buf[actual_len] = '\0';
    return buf;
}

static inline bool zp_str_contains(const char* s, const char* sub) {
    if (!s || !sub) return false;
    return strstr(s, sub) != NULL;
}

/* ===== TCP ソケット / ネットワークプリミティブ ===== */
static inline int64_t zp_tcp_listen(int64_t port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons((uint16_t)port);

    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(fd);
        return -1;
    }

    if (listen(fd, 128) < 0) {
        close(fd);
        return -1;
    }

    return (int64_t)fd;
}

static inline int64_t zp_tcp_accept(int64_t server_fd) {
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    int client_fd = accept((int)server_fd, (struct sockaddr*)&client_addr, &client_len);
    return (int64_t)client_fd;
}

static inline const char* zp_tcp_recv(int64_t client_fd) {
    char buf[16384];
    ssize_t n = recv((int)client_fd, buf, sizeof(buf) - 1, 0);
    if (n <= 0) return "";
    buf[n] = '\0';
    char* res = (char*)zp_alloc_scratch((size_t)n + 1);
    memcpy(res, buf, (size_t)n + 1);
    return res;
}

static inline void zp_tcp_send(int64_t client_fd, const char* data) {
    if (!data) return;
    size_t len = strlen(data);
    size_t total = 0;
    while (total < len) {
        ssize_t n = send((int)client_fd, data + total, len - total, 0);
        if (n <= 0) break;
        total += (size_t)n;
    }
}

static inline void zp_tcp_close(int64_t fd) {
    if (fd >= 0) {
        close((int)fd);
    }
}

/* ===== HTTP サーバー (POSIX Sockets) ===== */

typedef struct {
    int64_t client_id;
    const char* method;
    const char* path;
    const char* body;
} HttpRequest;

static inline HttpRequest HttpRequest_promote(HttpRequest r) {
    r.method = zp_promote(r.method);
    r.path = zp_promote(r.path);
    r.body = zp_promote(r.body);
    return r;
}

static inline int64_t zp_http_listen(int64_t port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;
    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((uint16_t)port);

    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(fd);
        return -1;
    }
    if (listen(fd, 128) < 0) {
        close(fd);
        return -1;
    }
    return (int64_t)fd;
}

static inline HttpRequest zp_http_accept(int64_t server_fd) {
    HttpRequest req = { -1, "", "", "" };
    if (server_fd < 0) return req;

    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    int client_fd = accept((int)server_fd, (struct sockaddr*)&client_addr, &client_len);
    if (client_fd < 0) return req;

    req.client_id = (int64_t)client_fd;

    // リクエスト読み込み (最大 64KB)
    size_t buf_cap = 65536;
    char* raw = (char*)zp_alloc_scratch(buf_cap);
    ssize_t n = recv(client_fd, raw, buf_cap - 1, 0);
    if (n <= 0) {
        return req;
    }
    raw[n] = '\0';

    // ボディ抽出 (\r\n\r\n または \n\n) を先に実行
    char* body_sep = strstr(raw, "\r\n\r\n");
    if (body_sep) {
        req.body = body_sep + 4;
    } else {
        body_sep = strstr(raw, "\n\n");
        if (body_sep) {
            req.body = body_sep + 2;
        } else {
            req.body = "";
        }
    }

    // HTTPリクエストパース: "METHOD /path HTTP/1.1"
    char* p = raw;
    while (*p == ' ') p++;
    char* method_start = p;
    while (*p && *p != ' ') p++;
    if (!*p) return req;
    *p = '\0';
    req.method = method_start;

    p++;
    while (*p == ' ') p++;
    char* path_start = p;
    while (*p && *p != ' ' && *p != '\r' && *p != '\n') p++;
    *p = '\0';
    req.path = path_start;

    return req;
}

static inline bool zp_http_respond(int64_t client_id, int64_t status, const char* content_type, const char* body) {
    if (client_id < 0) return false;
    int fd = (int)client_id;
    if (!body) body = "";
    if (!content_type) content_type = "text/plain";
    size_t body_len = strlen(body);

    const char* status_text = "OK";
    if (status == 200) status_text = "OK";
    else if (status == 201) status_text = "Created";
    else if (status == 204) status_text = "No Content";
    else if (status == 400) status_text = "Bad Request";
    else if (status == 403) status_text = "Forbidden";
    else if (status == 404) status_text = "Not Found";
    else if (status == 500) status_text = "Internal Server Error";

    char header[512];
    int header_len = snprintf(header, sizeof(header),
        "HTTP/1.1 %lld %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "\r\n",
        (long long)status, status_text, content_type, body_len);

    ssize_t hw = send(fd, header, (size_t)header_len, 0);
    ssize_t bw = 0;
    if (body_len > 0) {
        bw = send(fd, body, body_len, 0);
    }
    close(fd);
    return (hw > 0);
}

static inline void zp_http_close(int64_t server_fd) {
    if (server_fd >= 0) {
        close((int)server_fd);
    }
}

