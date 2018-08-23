from env import MyPaintEnv
import numpy as np
from gym import wrappers

class RandomAgent(object):
    """ simplest agent """
    def __init__(self, action_space):
        self.action_space = action_space
    
    def act(self, observation, reward, done):
        return self.action_space.sample()

    
if __name__ == '__main__':
    env = MyPaintEnv()
    env = wrappers.Monitor(env, directory='./tmp', force=True)

    agent = RandomAgent(env.action_space)

    steps = 100

    reward = 0
    done = False
    ob = env.reset()

    for t in range(steps):
        action = agent.act(ob, reward, done)
        ob, reward, done, _ = env.step(action)

    env.close()