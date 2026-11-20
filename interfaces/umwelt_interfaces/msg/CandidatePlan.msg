# A plan the robot is considering, scored under active inference.
#
# Lower expected free energy is better. It splits into two parts:
#   pragmatic_value  how well the plan's predicted outcomes match preferences
#   epistemic_value  how much the plan is expected to reduce uncertainty
# Both are reported as values (higher is better), so
#   expected_free_energy = -(pragmatic_value + epistemic_value)
# Planners that do not use active inference can leave the decomposition at
# zero and fill expected_free_energy with any cost where lower is better.

string id
nav_msgs/Path path              # in the Belief header frame

float32 expected_free_energy
float32 pragmatic_value
float32 epistemic_value

string summary                  # a few words for the operator, e.g. "covers the gap"
bool selected                   # true for the plan the robot is executing or about to
