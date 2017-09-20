#!/usr/bin/env python
import numpy as np
from multiprocessing import Process
from threading import Thread
from numpy.linalg import norm
import time
import pprint
import sys

# ROS packages
import rospy
import tf
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion, PoseStamped


class Estimator(object):
    """
    Estimator node class for ROS
    """
    def __init__(self, uav_name = 'UAV', num_state = None, num_sens = None):
        # ROS node setup: subscriber and publisher
        self.nh = rospy.init_node('Estimator', anonymous=False)
        self.pose_pub = rospy.Publisher('pose_est', PoseStamped, queue_size=1)
        self.imu_pub = rospy.Publisher('imu_est', Imu, queue_size=1)
        self.vicon_sub = rospy.Subscriber('/vicon/' + uav_name + "/pose", PoseStamped, self.vicon_callback)
        self.imu_sub = rospy.Subscriber("imu", Imu, self.imu_callback)
        self.imu_msg = Imu()
        self.pose_msg = PoseStamped()

        # Kalman filter setup
        self.x = np.matrix(np.zeros(shape=(num_state, 1)))
        self.P = np.matrix(np.identity(num_state)*10)
        self.F = np.matrix(np.identity(num_state))
        self.H = np.matrix(np.identity(num_sens))
        R_std = 0.1
        self.R = np.matrix(np.identity(num_sens)*R_std**2)
        self.I = np.matrix(np.identity(num_state))

        try:
            rospy.spin()
        except KeyboardInterrupt:
            print "Exiting..."
        finally:
            print "\nKilling estimator node"
        pass

    def vicon_callback(self, data):
        # TODO update attitude
        self.pose_msg = data
        self.state_update(self.vec2npVec(data.pose.position))

    def imu_callback(self, data):
        self.imu_msg.angular_velocity = data.angular_velocity
        self.imu_msg.linear_acceleration = data.linear_acceleration
        # self.state_update()
        self.state_predict()
        self.imu_pub.publish(data)
        self.pose_pub.publish(self.pose_msg)

    def state_predict(self):
        self.x = self.F*self.x
        self.P = self.F * self.P * self.F.getT()

    def state_update(self, Z):
        w = Z - self.H * self.x
        S = self.H * self.P * self.H.getT() + self.R
        K = self.P * self.H.getT() * S.getI()
        self.x = self.x + K * w
        self.P = (self.I - K * self.H) * self.P

    def vec2npVec(self, vec):
        return np.matrix(np.array([vec.x, vec.y, vec.z])).getT()


if __name__ == '__main__':
    estimator = Estimator(uav_name = 'Jetson',num_state = 3, num_sens=3)
