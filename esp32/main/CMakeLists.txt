idf_component_register(
    SRCS "model_data.cc"  "main.cpp" "main_functions.cc" 
    INCLUDE_DIRS "."
    PRIV_REQUIRES 
        mqtt
        esp_wifi
        esp_event
        esp_netif
        nvs_flash
        log
        espressif__esp-tflite-micro
)