cmake_minimum_required(VERSION 2.8)
 
project(libTac3D-example)


# set(CMAKE_BUILD_TYPE "Debug")
SET(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -O0 -Wall -g2 -ggdb")
# SET(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -DNODEBUG -O3 -Wall")

find_package(OpenCV REQUIRED)
find_package(Yaml-cpp REQUIRED)
find_package(Threads)

message(STATUS ${OpenCV_INCLUDE_DIRS})
INCLUDE_DIRECTORIES(
                     ${YAML_CPP_INCLUDE_DIR}
                     ${OpenCV_INCLUDE_DIRS}
                     ${PROJECT_SOURCE_DIR}/inc
                     )

add_executable( libTac3D-example
                ${PROJECT_SOURCE_DIR}/main-example.cpp
                ${PROJECT_SOURCE_DIR}/src/libTac3D.cpp
                )

target_link_libraries(libTac3D-example
    ${OpenCV_LIBS}
    yaml-cpp
    ${CMAKE_THREAD_LIBS_INIT})
