cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

set(PICO_SDK_PATH "/home/seanh/College/FYP/PicoW/pico-sdk")
set(PICO_BOARD pico_w CACHE STRING "Board type")

include(pico_sdk_import.cmake)

if (PICO_SDK_VERSION_STRING VERSION_LESS "1.4.0")
  message(FATAL_ERROR "Raspberry Pi Pico SDK version 1.4.0 (or later) required. Your version is ${PICO_SDK_VERSION_STRING}")
endif()

project(picoW C CXX ASM)

# Initialise the Raspberry Pi Pico SDK
pico_sdk_init()

file(GLOB MLKEM_SOURCES 
    "../mlkem/src/*.c"
    "../mlkem/src/fips202/*.c"
)

add_executable(RNG_restart_test RNG_restart_test.c)
add_executable(MLKEM512 mlkem512_main.c ${MLKEM_SOURCES})
add_executable(MLKEM768 mlkem768_main.c ${MLKEM_SOURCES})
add_executable(MLKEM1024 mlkem1024_main.c ${MLKEM_SOURCES})


target_compile_definitions(RNG_restart_test PRIVATE)
target_compile_definitions(MLKEM512 PRIVATE MLK_CONFIG_PARAMETER_SET=512 PICO_STACK_SIZE=0x8000)
target_compile_definitions(MLKEM768 PRIVATE MLK_CONFIG_PARAMETER_SET=768 PICO_STACK_SIZE=0x8000)
target_compile_definitions(MLKEM1024 PRIVATE MLK_CONFIG_PARAMETER_SET=1024 PICO_STACK_SIZE=0x8000)

foreach(TARGET_NAME RNG_restart_test MLKEM512 MLKEM768 MLKEM1024)
    pico_set_program_name(${TARGET_NAME} "${TARGET_NAME}")
    pico_set_program_version(${TARGET_NAME} "0.1")

    pico_enable_stdio_usb(${TARGET_NAME} 0)
    pico_enable_stdio_uart(${TARGET_NAME} 1)

    target_link_libraries(${TARGET_NAME}
        pico_stdlib
        pico_cyw43_arch_none
        pico_rand
    )

    target_include_directories(${TARGET_NAME} PRIVATE
        ${CMAKE_CURRENT_LIST_DIR}
        ${CMAKE_CURRENT_LIST_DIR}/../mlkem
        ${CMAKE_CURRENT_LIST_DIR}/../mlkem/src
        ${CMAKE_CURRENT_LIST_DIR}/../mlkem/src/fips202
        ${CMAKE_CURRENT_LIST_DIR}/../mlkem/src/native
    )
    pico_add_extra_outputs(${TARGET_NAME})
endforeach()


target_link_libraries(RNG_restart_test 
  pico_cyw43_arch_none
  pico_rand
)



#Override path to use custom linker with 32KB Stack in RAM.
pico_add_linker_script_override_path(MLKEM512 ${CMAKE_CURRENT_LIST_DIR})
pico_add_linker_script_override_path(MLKEM768 ${CMAKE_CURRENT_LIST_DIR})
pico_add_linker_script_override_path(MLKEM1024 ${CMAKE_CURRENT_LIST_DIR})



