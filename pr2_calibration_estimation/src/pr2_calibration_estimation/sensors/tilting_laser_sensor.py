# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# author: Vijay Pradeep

# Error block for a monocular camera plus tilting laser.  The
# camera is attached to a chain, but also has a 6 dof transform
# in between the tilting laser is attached to the
#
#       checkerboard
#      /
#   root
#      \
#       tilting_laser

from numpy import reshape

import roslib; roslib.load_manifest('pr2_calibration_estimation')
import rospy

# Takes a measurment, plus a set of possible camera/laser pairs, and creates the necessary error blocks
class TiltingLaserBundler:
    def __init__(self, valid_configs):
        self._valid_configs = valid_configs

    # Construct a CameraLaserErrorBlock for each camera/laser pair that matches one of the configs
    def build_blocks(self, M_robot):
        sensors = []
        for cur_config in self._valid_configs:
            rospy.logdebug("On Config Block [%s]" % cur_config["laser_id"])
            if cur_config["laser_id"]  in [ x.laser_id  for x in M_robot.M_laser ] :
                rospy.logdebug("  Found block!")
                cur_M_laser = M_robot.M_laser[ [ x.laser_id  for x in M_robot.M_laser ].index(cur_config["laser_id"]) ]
                cur_sensor = TiltingLaserSensor(cur_config, cur_M_laser)
                sensors.append(cur_sensor)
            else:
                rospy.logdebug("  Didn't find block")
        return sensors

class TiltingLaserSensor:
    def __init__(self, config_dict, M_laser):
        self._config_dict = config_dict
        self.sensor_type = "laser"
        self.sensor_id = config_dict["laser_id"]
        self._M_laser = M_laser

    def update_config(self, robot_params):
        self._tilting_laser = robot_params.tilting_lasers[ self._config_dict["laser_id"] ]

    def compute_residual(self, target_pts):
        z_mat = self.get_measurement()
        h_mat = self.compute_expected(target_pts)
        assert(z_mat.shape[0] == 3)
        assert(h_mat.shape[0] == 3)
        assert(z_mat.shape[1] == z_mat.shape[1])
        r = reshape(h_mat.T - z_mat.T, [-1,1])
        return r

    # Get the laser measurement.
    # Returns a 3xN matrix of points in cartesian space
    def get_measurement(self):
        # Get the laser points in a 4xN homogenous matrix
        laser_pts_root = self._tilting_laser.project_to_3D([x.position for x in self._M_laser.joint_points])
        return laser_pts_root[0:3,:]

    # Returns the pixel coordinates of the laser points after being projected into the camera
    # Returns a 4xN matrix of the target points
    def compute_expected(self, target_pts):
        return target_pts[0:3,:]
        #return target_pts

    # Build a dictionary that defines which parameters will in fact affect this measurement
    def build_sparsity_dict(self):
        sparsity = dict()

        sparsity['tilting_lasers'] = {}
        sparsity['tilting_lasers'][self.sensor_id] = {'before_chain':[1,1,1,1,1,1],
                                                      'after_chain':[1,1,1,1,1,1]}

        return sparsity