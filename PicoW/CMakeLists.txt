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

add_executable(entropy_restart_test entropy_restart_test.c)
add_executable(entropy_sequential_test entropy_sequential_test.c)
set(ALL_TARGETS entropy_restart_test entropy_sequential_test)



set(MLKEM_LEVELS 512 768 1024)
set(MLKEM_OPS all gen enc dec)

foreach(LEVEL ${MLKEM_LEVELS})
    foreach(OP ${MLKEM_OPS})

        if(OP STREQUAL "all")
            set(TARGET_NAME "MLKEM${LEVEL}")
        else()
            set(TARGET_NAME "MLKEM${LEVEL}_${OP}")
        endif()

        add_executable(${TARGET_NAME} mlkem_${OP}.c ${MLKEM_SOURCES})

        #Set mlkem security level and stack size to 32KB 
        target_compile_definitions(${TARGET_NAME} PRIVATE 
            MLK_CONFIG_PARAMETER_SET=${LEVEL} 
            PICO_STACK_SIZE=0x8000 
        )
        if(DEFINED ITERATION_COUNT)
            target_compile_definitions(${TARGET_NAME} PRIVATE
                ITERATION_COUNT=${ITERATION_COUNT}
            )
        endif()
        if(DEFINED BASELINE_AVERAGE_FREQ)
            target_compile_definitions(${TARGET_NAME} PRIVATE
                BASELINE_AVERAGE_FREQ=${BASELINE_AVERAGE_FREQ}
            )
        endif()

        #Use custom linker where stack_dummy lives in RAM
        pico_add_linker_script_override_path(${TARGET_NAME} ${CMAKE_CURRENT_LIST_DIR})
        pico_set_binary_type(${TARGET_NAME} copy_to_ram)
        list(APPEND ALL_TARGETS ${TARGET_NAME})
    endforeach()
endforeach()


foreach(TARGET_NAME ${ALL_TARGETS})
    pico_set_program_name(${TARGET_NAME} "${TARGET_NAME}")
    pico_set_program_version(${TARGET_NAME} "0.1")

    pico_enable_stdio_usb(${TARGET_NAME} 0)
    pico_enable_stdio_uart(${TARGET_NAME} 1)

    target_link_libraries(${TARGET_NAME}
        pico_stdlib
        pico_rand
        hardware_rosc   
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

#Unset to remove from next builds
#unset(ITERATION_COUNT CACHE)
#unset(BASELINE_AVERAGE_FREQ CACHE)

