# What the operator indicated, before it has been turned into a task.
#
# The glasses (or the desktop viewer) fill in what they observed: gaze, speech
# and head pose. The brain resolves the reference and the request and fills
# in the rest, then turns the result into one or more Task messages.

std_msgs/Header header          # frame_id is the shared world frame
string id

# Raw observation from the operator
geometry_msgs/Pose head_pose
geometry_msgs/Vector3 gaze_direction    # unit vector in the header frame
string utterance                        # transcribed speech, may be empty

# Resolved by the brain
bool target_resolved
geometry_msgs/Point target              # where the gaze ray met the shared map
string target_object_id                 # set when the target is a known object
string robot_id                         # robot addressed, empty for "any suitable robot"
string answers_query_id                 # set when this answers an OperatorQuery
float32 confidence                      # brain's confidence in the resolution, [0, 1]
