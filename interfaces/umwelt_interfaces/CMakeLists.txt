cmake_minimum_required(VERSION 3.8)
project(umwelt_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/GridBelief.msg"
  "msg/ObjectBelief.msg"
  "msg/CandidatePlan.msg"
  "msg/Belief.msg"
  "msg/OperatorQuery.msg"
  "msg/Intent.msg"
  "msg/Task.msg"
  "msg/TaskStatus.msg"
  DEPENDENCIES builtin_interfaces std_msgs geometry_msgs nav_msgs
)

ament_export_dependencies(rosidl_default_runtime)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
