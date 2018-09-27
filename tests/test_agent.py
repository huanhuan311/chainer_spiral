from nose.tools import eq_
import os
from agents import spiral
from models.spiral import SpiralToyDiscriminator, SpiralToyModel
from environments import ToyEnv
from chainerrl.optimizers import rmsprop_async
from dataset.toy_dataset import ToyDataset

def init_agent():
    # initialize an agent
    imsize = 3
    env = ToyEnv(imsize)
    G = SpiralToyModel(imsize, False)
    D = SpiralToyDiscriminator(imsize, False)
    G_opt = rmsprop_async.RMSpropAsync()
    D_opt = rmsprop_async.RMSpropAsync()
    G_opt.setup(G)
    D_opt.setup(D)
    p = [(1, 4, 7)]
    dataset = ToyDataset(imsize, p, p)
    def process_image():
        pass
    def preprocess_image():
        pass
    def preprocess_obs():
        pass
    def pack_action():
        pass
    def compute_auxiliary_reward():
        pass

    timestep_limit = 3
    rollout_n = 1
    conditional = True

    agent = spiral.SPIRAL(
        generator=G,
        discriminator=D,
        gen_optimizer=G_opt,
        dis_optimizer=D_opt,
        dataset=dataset,
        preprocess_image_func=preprocess_image,
        preprocess_obs_func=preprocess_obs,
        pack_action_func=pack_action,
        timestep_limit=timestep_limit,
        rollout_n=rollout_n,
        conditional=conditional,
        compute_auxiliary_reward_func=compute_auxiliary_reward)
    return agent

def test_save_and_load():
    # check the parameters are same between before save and after loading
    
    # create tmp dir
    save_dir = '/tmp/chainer_spiral_test'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    agent = init_agent()

    # insert some value to the generator
    w = agent.generator.pi.e1_c1.W.data
    w = w * 10
    agent.generator.pi.e1_c1.W.data = w

    # save agent to save_dir
    agent.snap(0, save_dir)

    # re-init agent
    del agent
    agent = init_agent()

    # load parameters from the snap
    agent.load(os.path.join(save_dir, '0'))

    eq_(agent.generator.pi.e1_c1.W.data.sum(), w.sum())
