# A 2D grid of occupancy probabilities with full float precision.
#
# nav_msgs/OccupancyGrid stores occupancy as int8 percentages with -1 for
# unknown, which throws away the uncertainty we want to show. Here every cell
# holds P(occupied) in [0, 1]. A cell that has never been observed keeps the
# prior (normally 0.5), which is also the point of maximum entropy, so
# "unknown" and "uncertain" are the same thing and need no special value.

std_msgs/Header header          # frame_id is the shared world frame

float32 resolution              # cell size in metres
uint32 width                    # cells along x
uint32 height                   # cells along y
geometry_msgs/Pose origin       # pose of cell (0, 0) in the header frame

float32 prior                   # value of a cell with no observations

# Row-major, starting at (0, 0). Length must be width * height.
float32[] p_occupied
