CXX = g++
CXXFLAGS = -std=c++11 -I./tf_micro -I./modelos -O3 -Wall -Wextra

# Fontes dos modelos convertidos em C
MODEL_SRCS = $(wildcard modelos/*.cc) $(wildcard modelos/*.cpp)
MODEL_OBJS = $(MODEL_SRCS:.cc=.o)
MODEL_OBJS := $(MODEL_OBJS:.cpp=.o)

# Código principal
APP_SRC = measure_all_models.cpp
APP_OBJ = $(APP_SRC:.cpp=.o)

# Biblioteca estática gerada pelo TFLM
TFLM_LIB = ./tf_micro/tensorflow/lite/micro/tools/make/gen/linux_x86_64/lib/libtensorflow-microlite.a

TARGET = measure_models

all: $(TARGET)

$(TARGET): $(APP_OBJ) $(MODEL_OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(TFLM_LIB)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

%.o: %.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(APP_OBJ) $(MODEL_OBJS) $(TARGET) arena_results.csv
