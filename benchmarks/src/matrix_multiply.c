#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static long
parse_long_arg(const char *value, const char *name)
{
    char *end = NULL;
    errno = 0;
    long parsed = strtol(value, &end, 10);

    if (errno != 0 || end == value || *end != '\0' || parsed <= 0) {
        fprintf(stderr, "Invalid %s: %s\n", name, value);
        exit(1);
    }

    return parsed;
}

int
main(int argc, char **argv)
{
    const long n = argc > 1 ? parse_long_arg(argv[1], "matrix size") : 96;
    const long repetitions =
        argc > 2 ? parse_long_arg(argv[2], "repetitions") : 4;
    const size_t count = (size_t)n * (size_t)n;
    int32_t *a = NULL;
    int32_t *bt = NULL;
    int32_t *c = NULL;
    uint64_t checksum = 0;
    volatile uint64_t sink = 0;

    a = (int32_t *)malloc(count * sizeof(*a));
    bt = (int32_t *)malloc(count * sizeof(*bt));
    c = (int32_t *)malloc(count * sizeof(*c));

    if (a == NULL || bt == NULL || c == NULL) {
        fprintf(stderr, "Failed to allocate matrices for n=%ld\n", n);
        free(a);
        free(bt);
        free(c);
        return 1;
    }

    for (long i = 0; i < n; ++i) {
        for (long j = 0; j < n; ++j) {
            a[(size_t)i * (size_t)n + (size_t)j] =
                (int32_t)(((i * 17) + (j * 13) + 1) % 97);
            bt[(size_t)j * (size_t)n + (size_t)i] =
                (int32_t)(((i * 7) + (j * 11) + 3) % 89);
        }
    }

    for (long rep = 0; rep < repetitions; ++rep) {
        for (size_t idx = 0; idx < count; ++idx) {
            c[idx] = 0;
        }

        for (long i = 0; i < n; ++i) {
            for (long j = 0; j < n; ++j) {
                int64_t sum = 0;

                for (long k = 0; k < n; ++k) {
                    sum += (int64_t)a[(size_t)i * (size_t)n + (size_t)k] *
                           (int64_t)bt[(size_t)j * (size_t)n + (size_t)k];
                }

                c[(size_t)i * (size_t)n + (size_t)j] = (int32_t)sum;
            }
        }
    }

    for (size_t idx = 0; idx < count; ++idx) {
        checksum += (uint64_t)(uint32_t)c[idx];
    }

    printf(
        "matrix_multiply n=%ld repetitions=%ld checksum=%" PRIu64 "\n",
        n,
        repetitions,
        checksum
    );
    sink = checksum;

    free(a);
    free(bt);
    free(c);
    return sink == 0;
}
