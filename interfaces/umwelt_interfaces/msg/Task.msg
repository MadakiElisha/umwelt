# A high-level goal for one robot. Vehicle independent: a UAV, UGV and USV
# all accept the same task types and each robot layer decides how to carry
# them out. Published on /umwelt/<robot_id>/task.

uint8 GOTO = 1                  # go to region[0] and hold
uint8 INSPECT = 2               # observe region[0] from standoff distance
uint8 SURVEY = 3                # cover the polygon in region
uint8 HOLD = 4                  # stop and hold position
uint8 RETURN_HOME = 5
uint8 CANCEL = 6                # cancel the task named in id

std_msgs/Header header          # frame_id is the shared world frame
string id
string robot_id
uint8 type

# One point for GOTO and INSPECT, a closed polygon (three or more points,
# last not repeated) for SURVEY, empty otherwise.
geometry_msgs/Point[] region

float32 standoff                # metres from the target for INSPECT, 0 for robot default
float32 max_speed               # m/s, 0 for robot default

string source_intent_id         # Intent that produced this task, if any
