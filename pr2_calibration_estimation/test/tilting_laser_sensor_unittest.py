#!/usr/bin/env python
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


import roslib; roslib.load_manifest('pr2_calibration_estimation')

import sys
import unittest
import rospy
import numpy
import yaml
from pr2_calibration_estimation.sensors.tilting_laser_sensor import TiltingLaserBundler, TiltingLaserSensor
from calibration_msgs.msg import *
from sensor_msgs.msg import JointState, CameraInfo
from pr2_calibration_estimation.robot_params import RobotParams

from pr2_calibration_estimation.single_transform import SingleTransform
from pr2_calibration_estimation.dh_chain import DhChain
from pr2_calibration_estimation.camera import RectifiedCamera
from pr2_calibration_estimation.tilting_laser import TiltingLaser
from pr2_calibration_estimation.full_chain import FullChainCalcBlock

from numpy import *

def loadConfigList():

    config_yaml = '''
- laser_id:     laser1
'''
    config_dict = yaml.load(config_yaml)
    return config_dict

class TestTiltingLaserBundler(unittest.TestCase):
    def test_basic(self):
        config_list = loadConfigList()

        bundler = TiltingLaserBundler(config_list)

        M_robot = RobotMeasurement()
        M_robot.M_laser.append( LaserMeasurement(laser_id="laser1"))

        blocks = bundler.build_blocks(M_robot)

        self.assertEqual( len(blocks), 1)
        self.assertEqual( blocks[0]._M_laser.laser_id, "laser1")

def loadSystem():

    config = yaml.load('''
        laser_id: laserA
        ''')

    robot_params = RobotParams()
    robot_params.configure( yaml.load('''
        dh_chains: {}
        tilting_lasers:
            laserA:
                before_joint: [0, 0, 0, 0, 0, 0]
                after_joint:  [0, 0, 0, 0, 0, 0]
        rectified_cams: {}
        transforms: {}
        checkerboards: {}
        ''' ) )

    P = [ 1, 0, 0, 0,
          0, 1, 0, 0,
          0, 0, 1, 0 ]

    return config, robot_params, P


class TestTiltingLaser(unittest.TestCase):

    def test_tilting_laser_1(self):
        print ""
        config, robot_params, P = loadSystem()

        joint_points = [ JointState(position=[0,0,0]),
                         JointState(position=[0,pi/2,1]),
                         JointState(position=[pi/2,0,1]) ]

        block = TiltingLaserSensor(config, LaserMeasurement(laser_id="laserA",
                                                            joint_points=joint_points))

        block.update_config(robot_params)

        target_pts = matrix( [ [ 0,  0,  0 ],
                               [ 0,  1,  0 ],
                               [ 0,  0, -1 ],
                               [ 1,  1,  1 ] ] )

        h = block.compute_expected(target_pts)
        z = block.get_measurement()
        r = block.compute_residual(target_pts)

        self.assertAlmostEqual(numpy.linalg.norm(h-target_pts[0:3,:]), 0.0, 6)
        self.assertAlmostEqual(numpy.linalg.norm(z-target_pts[0:3,:]), 0.0, 6)
        self.assertAlmostEqual(numpy.linalg.norm(r), 0.0, 6)


        # Test Sparsity
        sparsity = block.build_sparsity_dict()
        self.assertEqual(sparsity['tilting_lasers']['laserA']['before_chain'], [1,1,1,1,1,1])
        self.assertEqual(sparsity['tilting_lasers']['laserA']['after_chain'],  [1,1,1,1,1,1])


if __name__ == '__main__':
    import rostest
    rostest.unitrun('pr2_calibration_estimation', 'test_TiltingLaserBundler',   TestTiltingLaserBundler,   coverage_packages=['pr2_calibration_estimation.sensors.tilting_laser_sensor'])
    rostest.unitrun('pr2_calibration_estimation', 'test_TiltingLaser', TestTiltingLaser, coverage_packages=['pr2_calibration_estimation.sensors.tilting_laser_sensor'])