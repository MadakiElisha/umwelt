# Progress of a task, reported by the robot executing it.
# Published on /umwelt/<robot_id>/task_status.

uint8 QUEUED = 0
uint8 ACTIVE = 1
uint8 SUCCEEDED = 2
uint8 FAILED = 3
uint8 CANCELED = 4
uint8 REJECTED = 5              # robot cannot do this task, see detail

std_msgs/Header header
string task_id
string robot_id
uint8 state
float32 progress                # [0, 1], best estimate
string detail                   # short reason for FAILED or REJECTED
