import time

import pybullet as pb
import pybullet_data
import numpy as np
import os

class FrankaEnv(object):

    def __init__(self, render=True, ts=0.002):

        self.frame_skip=10
        if render:
            self.client = pb.connect(pb.GUI)
        else:
            self.client = pb.connect(pb.DIRECT)
        pb.setTimeStep(ts)
        pb.setAdditionalSearchPath(pybullet_data.getDataPath())
        planeID = pb.loadURDF('plane.urdf')
        self.robot = pb.loadURDF('./franka_description/robots/franka_panda.urdf', [0.,0.,0.], useFixedBase=1)
        pb.setGravity(0,0,-9.81)
        self.reset_joint_state = [0., -0.78, 0., -2.35, 0., 1.57, 0.78]
        self.ee_id = 7
        self.sat_val = 0.3
        self.reset()
        self.joint_low = np.array([-2.9,-1.8,-2.9,-3.0,-2.9,-0.08,-2.9])
        self.joint_high = np.array([2.9,1.8,2.9,0.08,2.9,3.0,2.9])
        self.Nstates = 17
        self.udim = 7
        self.dt = self.frame_skip*ts

    def get_ik(self, position, orientation=None):
        if orientation is None:
            jnts = pb.calculateInverseKinematics(self.robot, self.ee_id, position)[:7]
        else:
            jnts = pb.calculateInverseKinematics(self.robot, self.ee_id, position, orientation)[:7]
        return jnts

    def get_state(self):
        jnt_st = pb.getJointStates(self.robot, range(7))
        ## 1,2,3 position 
        ## 4,5,6 are the link frame pose, orientation in quat and ve
        ee_state = pb.getLinkState(self.robot, self.ee_id)[-2:] ### Why local and not the Cartesian ones? Ask Ian
        jnt_ang = []
        jnt_vel = []
        for jnt in jnt_st:
            jnt_ang.append(jnt[0])
            jnt_vel.append(jnt[1])
        # print(ee_state[0],ee_state[1],jnt_ang,jnt_vel)
        self.state = np.concatenate([ee_state[0], ee_state[1], jnt_ang, jnt_vel]) # ee_state[0] are [x,y,z] of EE, ee_state[1] are quaternions: x,y,z,w of EE
        return self.state.copy()

    def reset(self):
        for i, jnt in enumerate(self.reset_joint_state):
            pb.resetJointState(self.robot, i, self.reset_joint_state[i])
        return self.get_state()

    def reset_state(self,joint):
        for i, jnt in enumerate(joint):
            pb.resetJointState(self.robot, i, joint[i])
        return self.get_state()

    def step(self, action):
        a = np.clip(action, -self.sat_val, self.sat_val)
        pb.setJointMotorControlArray(
                    self.robot, range(7),
                    pb.VELOCITY_CONTROL, targetVelocities=a)
        for _ in range(self.frame_skip):
            pb.stepSimulation()

        return self.get_state()

if __name__ == '__main__':
    dt = 0.002
    env = FrankaEnv(render=True, ts=dt)
    uval = 0.12

    noise = (np.random.rand(7)-0.5)*2*0.2
    joint_init = env.reset_joint_state+noise
    joint_init = np.clip(joint_init,env.joint_low,env.joint_high)
    s0 = env.reset_state(joint_init)
    u10 = (np.random.rand(7)-0.5)*2*uval

    steps = 0
    while True:
        # env.step(np.random.uniform(-env.sat_val, env.sat_val, 7))
        # if steps % 100 == 0:
        #     # u10 = (np.random.rand(7)-0.5)*2*uval
        #     # u10 = np.random.uniform(-env.sat_val, env.sat_val, 7)
        u10 = (np.random.rand(7)-0.5)*2*uval
        env.step(u10)
        # time.sleep(dt * env.frame_skip)
        steps += 1


