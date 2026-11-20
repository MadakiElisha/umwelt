# Everything a robot currently believes that is worth sharing with the operator.
# Published by each robot on /umwelt/<robot_id>/belief.

std_msgs/Header header          # frame_id is the shared world frame (ENU, REP 103)
string robot_id

geometry_msgs/PoseWithCovariance pose   # the robot's own pose estimate
geometry_msgs/Twist velocity

# Leave width or height at zero when the robot has no grid to share.
GridBelief grid

ObjectBelief[] objects
CandidatePlan[] plans

string active_task_id           # empty when idle
