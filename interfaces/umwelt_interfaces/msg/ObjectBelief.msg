# Something the robot believes is in the world, with its uncertainty.

string id                       # stable across updates for the same object

# Class distribution. labels[i] has probability label_probs[i].
# The two arrays must be the same length and the probabilities should sum to 1.
string[] labels
float32[] label_probs

# Probability that the object exists at all. Low values are tentative
# detections the operator may want to confirm.
float32 p_exists

geometry_msgs/PoseWithCovariance pose   # in the Belief header frame
geometry_msgs/Vector3 size              # bounding box extents in metres, zero if unknown
