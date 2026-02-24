#include <stdio.h>
#include "main_functions.h"

extern "C" void app_main(void) {
    setup();
    while (true) {
        loop();
    }
}