cmake_minimum_required(VERSION 2.8 FATAL_ERROR)
project(light_sensor)

find_package(gazebo REQUIRED)
include_directories(${GAZEBO_INCLUDE_DIRS})
link_directories(${GAZEBO_LIBRARY_DIRS})
list(APPEND CMAKE_CXX_FLAGS "${GAZEBO_CXX_FLAGS}")

add_library(color_change_plugin SHARED ColorChangeEMQXPlugin.cc)
target_link_libraries(color_change_plugin ${GAZEBO_LIBRARIES} paho-mqtt3c)

set(CMAKE_CXX_FLAGS "-std=c++11 ${CMAKE_CXX_FLAGS}")
