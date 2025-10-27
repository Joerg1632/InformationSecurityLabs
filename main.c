#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint32_t a = 9301;
static const uint32_t c = 49297;
static const uint32_t m = 233280;

static uint32_t state = 0;

void lcg_seed(uint32_t seed) {
    state = seed;
}

static inline uint32_t lcg_next32(void) {
    state = (a * state + c) % m;
    return state;
}

void lcg_stream_xor(uint8_t *dst, const uint8_t *src, size_t len) {
    for (size_t i = 0; i < len; ) {
        uint32_t rnd = lcg_next32();
        uint8_t k[4] = { rnd & 0xFF, (rnd>>8) & 0xFF, (rnd>>16) & 0xFF, (rnd>>24) & 0xFF };
        for (int j = 0; j < 4 && i < len; j++, i++)
            dst[i] = src[i] ^ k[j];
    }
}

int main(void) {
    const char *plaintext = "The quick brown fox jumps over the lazy dog";
    size_t len = strlen(plaintext);

    uint8_t *ciphertext = malloc(len);
    uint8_t *recovered  = malloc(len + 1);
    if (!ciphertext || !recovered) return 1;

    lcg_seed(232);

    lcg_stream_xor(ciphertext, (const uint8_t*)plaintext, len);

    lcg_seed(232);
    lcg_stream_xor(recovered, ciphertext, len);
    recovered[len] = '\0';

    printf("Plain:  %s\n", plaintext);
    printf("Cipher: ");
    for (size_t i=0; i<len; i++) printf("%02X ", ciphertext[i]);
    printf("\n");
    printf("Recover: %s\n", recovered);

    free(ciphertext);
    free(recovered);
    return 0;
}
