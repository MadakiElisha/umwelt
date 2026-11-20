# A question from a robot to the operator.
#
# A robot should send one only when the expected information gain from the
# answer is worth interrupting a person for. epistemic_value is that expected
# gain, in nats, so the brain can rank or suppress queries when several
# robots want attention at once.

std_msgs/Header header          # frame_id is the shared world frame
string id
string robot_id

string question                 # short and plain, e.g. "Water or shadow?"
string[] options                # suggested answers, may be empty for free speech

geometry_msgs/Point focus       # where in the world the question is about
float32 epistemic_value

builtin_interfaces/Duration timeout   # after this the robot proceeds on its own
