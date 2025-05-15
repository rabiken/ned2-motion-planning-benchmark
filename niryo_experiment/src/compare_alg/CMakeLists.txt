cmake_minimum_required(VERSION 3.0.2)
project(compare_alg)

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  # moveit_core
  # moveit_ros_planning
  moveit_ros_planning_interface
  niryo_robot_sound
  # record_experiment
  std_srvs
  # moveit_ros_visualization
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
  # INCLUDE_DIRS include
  LIBRARIES ${PROJECT_NAME}
  CATKIN_DEPENDS 
  roscpp 
  # moveit_core 
  # moveit_ros_planning 
  moveit_ros_planning_interface 
  # move_group_interface planning_scene_interface
  niryo_robot_sound 
  std_srvs
  record_experiment
  # moveit_ros_visualization
)

###########
## Build ##
###########

## Specify additional locations of header files
## Your package locations should be listed before other locations
include_directories(
# include
  ${catkin_INCLUDE_DIRS}
  # ${catkin_INCLUDE_DIRS}/record_experiment
  /root/ws_compare_alg/devel/include # we had to set the path to the include directory of the record_experiment package
)


## Declare a C++ library
# add_library(${PROJECT_NAME}
#   src/${PROJECT_NAME}/compare_alg.cpp
# )

## Add cmake target dependencies of the library
## as an example, code may need to be generated before libraries
## either from message generation or dynamic reconfigure
# add_dependencies(${PROJECT_NAME} ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Declare a C++ executable
## With catkin_make all packages are built within a single CMake context
## The recommended prefix ensures that target names across packages don't collide
# add_executable(${PROJECT_NAME}_node src/compare_alg_node.cpp)
# add_executable(exec_motion_alg_node src/exec_motion_alg.cpp)
# add_executable(exec_motion_alg2_node src/exec_motion_alg2.cpp)
add_executable(exec_motion_alg_node src/exec_motion_alg.cpp)
# add_executable(exec_motion_alg3_node src/exec_motion_alg3.cpp)
# add_executable(exec_motion_alg4_node src/exec_motion_alg4.cpp)
# add_executable(exec_motion_alg5_node src/exec_motion_alg5.cpp)

## Rename C++ executable without prefix
## The above recommended prefix causes long target names, the following renames the
## target back to the shorter version for ease of user use
## e.g. "rosrun someones_pkg node" instead of "rosrun someones_pkg someones_pkg_node"
# set_target_properties(${PROJECT_NAME}_node PROPERTIES OUTPUT_NAME node PREFIX "")

## Add cmake target dependencies of the executable
## same as for the library above
# add_dependencies(${PROJECT_NAME}_node ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
add_dependencies(exec_motion_alg_node ${catkin_EXPORTED_TARGETS} ${record_experiment_EXPORTED_TARGETS})
# add_dependencies(exec_motion_alg4_node ${catkin_EXPORTED_TARGETS} ${record_experiment_EXPORTED_TARGETS})
# add_dependencies(exec_motion_alg5_node ${catkin_EXPORTED_TARGETS} ${record_experiment_EXPORTED_TARGETS})

## Specify libraries to link a library or executable target against
# target_link_libraries(${PROJECT_NAME}_node
#   ${catkin_LIBRARIES}
# )
# target_link_libraries(exec_motion_alg_node ${catkin_LIBRARIES})
# target_link_libraries(exec_motion_alg2_node ${catkin_LIBRARIES})
target_link_libraries(exec_motion_alg_node ${catkin_LIBRARIES})
# target_link_libraries(exec_motion_alg3_node ${catkin_LIBRARIES})
# target_link_libraries(exec_motion_alg4_node ${catkin_LIBRARIES})
# target_link_libraries(exec_motion_alg5_node ${catkin_LIBRARIES})

