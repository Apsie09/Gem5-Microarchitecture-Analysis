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

static uint32_t
xorshift32(uint32_t *state)
{
    uint32_t x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

int
main(int argc, char **argv)
{
    const long nodes = argc > 1 ? parse_long_arg(argv[1], "nodes") : 262144;
    const long steps_per_node =
        argc > 2 ? parse_long_arg(argv[2], "steps_per_node") : 2;
    uint32_t seed = argc > 3 ? (uint32_t)parse_long_arg(argv[3], "seed") : 12345u;
    const uint32_t initial_seed = seed;
    uint32_t *order = NULL;
    uint32_t *next = NULL;
    uint64_t checksum = 0;
    uint32_t index = 0;
    volatile uint64_t sink = 0;

    if (seed == 0) {
        seed = 1;
    }

    order = (uint32_t *)malloc((size_t)nodes * sizeof(*order));
    next = (uint32_t *)malloc((size_t)nodes * sizeof(*next));

    if (order == NULL || next == NULL) {
        fprintf(stderr, "Failed to allocate pointer chasing arrays.\n");
        free(order);
        free(next);
        return 1;
    }

    for (long i = 0; i < nodes; ++i) {
        order[i] = (uint32_t)i;
    }

    for (long i = nodes - 1; i > 0; --i) {
        long swap_idx = (long)(xorshift32(&seed) % (uint32_t)(i + 1));
        uint32_t tmp = order[i];
        order[i] = order[swap_idx];
        order[swap_idx] = tmp;
    }

    for (long i = 0; i < nodes; ++i) {
        long next_i = (i + 1) % nodes;
        next[order[i]] = order[next_i];
    }

    index = order[0];

    for (uint64_t step = 0; step < (uint64_t)nodes * (uint64_t)steps_per_node;
         ++step) {
        index = next[index];
        checksum += (uint64_t)index;
    }

    printf(
        "pointer_chase nodes=%ld steps_per_node=%ld seed=%u final_index=%u checksum=%" PRIu64 "\n",
        nodes,
        steps_per_node,
        initial_seed,
        index,
        checksum
    );
    sink = checksum;

    free(order);
    free(next);
    return sink == 0;
}
