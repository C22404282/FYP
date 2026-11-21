#include <stdint.h>
#include <stdio.h>
#include "../mlkem/mlkem_native.h" 
#include "../mlkem/src/kem.h"
#include "pico/rand.h"
#include "pico/stdlib.h"
#include "hardware/structs/systick.h"
#include <inttypes.h>

#ifndef ITERATION_COUNT
#define ITERATION_COUNT 1000
#endif

#ifndef BASELINE_AVERAGE_FREQ
#define BASELINE_AVERAGE_FREQ 250
#endif

//PICO-SDK Linker Symbol - Found in .map files
extern uint32_t __StackBottom;
extern uint32_t __StackTop;

#define KNOWN_PATTERN 0xDEADBEEFu


void paint_stack(void) {
    uint32_t *p = &__StackBottom;
    uint32_t *sp;

    //Assembly to copy stack pointer register value into sp variable
    __asm volatile ("mov %0, sp" : "=r" (sp));

    // Paint from the bottom limit up to just below the current stack pointer
    while (p < (sp - 8)) {
        *p++ = KNOWN_PATTERN;
    }
}

size_t max_stack_used(void) {
    //Start from bottom
    uint32_t *stack = &__StackBottom;
    //Word = 32 bits (4-bytes)
    size_t total_words = 0x8000 / sizeof(uint32_t); // 8,192 words (32 KB)
    size_t unused_words = 0;

    // Count number of unused words from bottom to top using the known pattern
    while (unused_words < total_words && stack[unused_words] == KNOWN_PATTERN) {
        unused_words++;
    }

    size_t total_words_used = total_words - unused_words;

    //Multiply by 4 to convert to bytes
    return total_words_used * sizeof(uint32_t);
}


void enable_systick() {
    systick_hw->csr = 0x5;        // Enable SysTick with CPU clock
    systick_hw->rvr = 0x00FFFFFF; 
}


int randombytes(uint8_t *out, size_t outlen) {
    while (outlen >= 4) {
        uint32_t r = get_rand_32();
        memcpy(out, &r, 4);
        out += 4;
        outlen -= 4;
    }
    if (outlen > 0) {
        uint32_t r = get_rand_32();
        memcpy(out, &r, outlen);
    }
    return 0;
}

void main(){

    enable_systick();

    //Setup GPIO PINS
    uint8_t decSignal = 28;
    uint8_t testSignal = 2;
    uint8_t baselineSignal = 3;

    gpio_init(decSignal);
    gpio_set_dir(decSignal, GPIO_OUT);

    gpio_init(testSignal);
    gpio_set_dir(testSignal, GPIO_OUT);

    gpio_init(baselineSignal);
    gpio_set_dir(baselineSignal, GPIO_OUT);

    //Initialize UART
    uart_init(uart0, 115200);
    gpio_set_function(0, GPIO_FUNC_UART);

    // uint8_t publicKey[MLKEM512_PUBLICKEYBYTES];
    // uint8_t secretKey[MLKEM512_SECRETKEYBYTES];
    // uint8_t cipherText[MLKEM512_CIPHERTEXTBYTES];
    // uint8_t shared_secret_sender[MLKEM512_BYTES];
    // uint8_t shared_secret_recv[MLKEM512_BYTES];


    uint8_t publicKey[MLKEM_PUBLICKEYBYTES(MLK_CONFIG_PARAMETER_SET)];
    uint8_t secretKey[MLKEM_SECRETKEYBYTES(MLK_CONFIG_PARAMETER_SET)];
    uint8_t cipherText[MLKEM_CIPHERTEXTBYTES(MLK_CONFIG_PARAMETER_SET)];
    uint8_t shared_secret_sender[MLKEM_BYTES];
    uint8_t shared_secret_recv[MLKEM_BYTES];
    
    //Calculate timer overhead
    uint32_t empty_start = systick_hw->cvr;
    __asm volatile ("" ::: "memory");
    gpio_put(testSignal, true);
    gpio_put(testSignal, false);
    __asm volatile ("" ::: "memory");
    uint32_t empty_end = systick_hw->cvr;
    uint32_t timer_overhead = (empty_start - empty_end) & 0x00FFFFFF;
    

    mlk_kem_keypair(publicKey, secretKey, NULL);
    mlk_kem_enc(cipherText, shared_secret_sender, publicKey, NULL);


    size_t baseline;


    for(uint16_t i = 0;i < ITERATION_COUNT;i++){
        paint_stack();
        baseline = max_stack_used();
        uint32_t dec_start = systick_hw->cvr;
        __asm volatile ("" ::: "memory");
        gpio_put(decSignal, true);  // SIGNAL DEC HIGH
        if (mlk_kem_dec(shared_secret_recv, cipherText, secretKey, NULL) == 0) {
            gpio_put(decSignal, false);  // SIGNAL DEC LOW
        }
        else{
            while(true){};
        }
        __asm volatile ("" ::: "memory");
        uint32_t dec_cycles = (dec_start - systick_hw->cvr) & 0x00FFFFFF;
        size_t dec_stack = max_stack_used() - baseline;
        printf("{%" PRIu32 ",%" PRIu32 "}\n", dec_cycles, timer_overhead);


        if((i % BASELINE_AVERAGE_FREQ) == 0){
            gpio_put(baselineSignal, true);
            busy_wait_us_32(15);
            gpio_put(baselineSignal, false);
        }
        
    }
    return;
}

