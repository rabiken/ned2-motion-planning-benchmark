cmake_minimum_required(VERSION 3.0.2)
project(record_experiment)

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS
  roscpp
  std_srvs
  niryo_robot_msgs
  std_msgs
  message_generation

)

## Generate services in the 'srv' folder
add_service_files(
  DIRECTORY srv
  FILES
  SetFilename.srv
)


## Generate added messages and services with any dependencies listed here
generate_messages(
  DEPENDENCIES
  std_msgs  # Or other packages containing msgs
)



###################################
## catkin specific configuration ##
###################################
## The catkin_package macro generates cmake config files for your package
## Declare things to be passed to dependent projects
## INCLUDE_DIRS: uncomment this if your package contains header files
## LIBRARIES: libraries you create in this project that dependent projects also need
## CATKIN_DEPENDS: catkin_packages dependent projects also need
## DEPENDS: system dependencies of this project that dependent projects also need
catkin_package(
#  INCLUDE_DIRS include
 LIBRARIES record_experiment
 CATKIN_DEPENDS roscpp std_srvs message_runtime std_msgs control_msgs actionlib_msgs niryo_robot_msgs
#  DEPENDS system_lib
)

###########
## Build ##
###########

message(STATUS "catkin_INCLUDE_DIRS: ${catkin_INCLUDE_DIRS}")
## Specify additional locations of header files
## Your package locations should be listed before other locations
include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)


## Declare a C++ executable
## With catkin_make all packages are built within a single CMake context
## The recommended prefix ensures that target names across packages don't collide
# add_executable(${PROJECT_NAME}_node src/record_experiment_node.cpp)
add_executable(stopwatch_node src/stopwatch.cpp)
add_executable(trajectory_logger_node src/trajectory_logger.cpp)


## Add cmake target dependencies of the executable
## same as for the library above
# add_dependencies(${PROJECT_NAME}_node ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
add_dependencies(trajectory_logger_node ${${PROJECT_NAME}_EXPORTED_TARGETS} record_experiment_gencpp)


## Specify libraries to link a library or executable target against
# target_link_libraries(${PROJECT_NAME}_node
#   ${catkin_LIBRARIES}
# )
target_link_libraries(stopwatch_node ${catkin_LIBRARIES})
target_link_libraries(trajectory_logger_node ${catkin_LIBRARIES})

