import gym
import os

from lib import mypaintlib
from lib import tiledsurface
from lib import brush
from lib import pixbufsurface
import numpy as np

import logging
import time

class MyPaintEnv(gym.Env):
    action_space = None
    observation_space = None
    reward_range = None
    viewer = None

    metadata = {
        'render.modes': ['human', 'rgb_array'],
    }

    def __init__(self, logger=None, imsize=64, bg_color=None):
        """ initialize environment """
        super().__init__()

        self.logger = logger or logging.getLogger(__name__)

        # starting positing of the pen for each episode
        self.tile_offset = mypaintlib.TILE_SIZE
        self.start_x = self.tile_offset
        self.start_y = self.tile_offset
        self.imsize = imsize

        # action space
        self.action_space = gym.spaces.Dict({
            'position': gym.spaces.Box(low=0, high=1.0, shape=(2,)),
            'pressure': gym.spaces.Box(low=0, high=1.0, shape=()),
            'color': gym.spaces.Box(low=0, high=1.0, shape=(3,)),
            'prob': gym.spaces.Discrete(2) 
        })

        # observation space
        self.observation_space = gym.spaces.Dict({
            'image': gym.spaces.Box(low=0, high=255, shape=(self.imsize, self.imsize, 3), dtype=np.uint8),
            'position': gym.spaces.Box(low=0, high=1.0, shape=(2,))
        })

        # color of the background
        if bg_color is None:
            self.bg_color = (1, 1, 1)
        else:
            self.bg_color = bg_color

        # open brush 
        brush_info_file = os.getenv('BRUSHINFO')
        if brush_info_file is None:
            raise ValueError('You need to specify brush file by BRUSHINFO')

        self.logger.debug('Open brush info from %s', brush_info_file)

        with open(brush_info_file, 'r') as f:
            self.brush_info = brush.BrushInfo(f.read())
        self.brush = brush.Brush(self.brush_info)

        # initialize canvas (surface)
        self.surface = tiledsurface.Surface()

        # reset canvas and set current position of the pen
        self.reset()

    def step(self, action):
        """ draw by action.
        Assuming that action is a dict whose keys are (x, p, c, q)
        x: tuple of float. (x, y) of the next point
        p: float. pressure
        c: tuple of float. (r, g, b). color value of the brush [0, 1] 
        q: integer = (0, 1). a binary flag specifying the type of action: draw or skip to the next point w/o drawing
        """
        x, y = action['position']

        # offset
        x = x * self.imsize + self.tile_offset
        y = y * self.imsize + self.tile_offset

        p = action['pressure']
        r, g, b = action['color']
        q = action['prob']

        self.brush_info.set_color_rgb((float(r), float(g), float(b)))

        # maybe draw
        if q:
            self.__draw(float(x), float(y), float(p))
        else:
            self.brush.reset()
            self.__draw(float(x), float(y), 0.0)
        
        # TODO: return some reward and some flagments
        reward = 0.0
        done = False

        # create observation
        ob = {'image': self._get_rgb_array(), 'position': np.array((self.x / self.imsize, self.y / self.imsize))}
        return ob, reward, done, {}

    def __draw(self, x, y, p, xtilt=0, ytilt=0, dtime=0.1, viewzoom=1.0, viewrotation=0.0):
        self.surface.begin_atomic()
        self.brush.stroke_to(
            self.surface.backend,
            x,
            y,
            p,
            xtilt,
            ytilt,
            dtime,
            viewzoom,
            viewrotation
        )
        self.surface.end_atomic()

        # update the current point
        self.x = x
        self.y = y

    def reset(self):
        """ clear all the content on the canvas, move the current position to the default """
        # clear content on the canvas
        self.surface.clear()

        # fill the canvas with the background color
        with self.surface.cairo_request(0, 0, self.imsize + self.tile_offset * 2, self.imsize + self.imsize * 2) as cr:
            r, g, b = self.bg_color
            cr.set_source_rgb(r, g, b)
            cr.rectangle(self.tile_offset, self.tile_offset, self.imsize + self.tile_offset * 2, self.imsize + self.tile_offset * 2)
            cr.fill()

        # set the pen's initial position
        self.__draw(self.start_x, self.start_y, 0)
        self.x = self.start_x
        self.y = self.start_y
        
        return self._get_rgb_array()

    def render(self, mode='human'):
        """ render the current drawn picture image for human """
        if mode == 'human':
            if self.viewer is None:
                from gym.envs.classic_control import rendering
                self.viewer = rendering.SimpleImageViewer()
            self.viewer.imshow(self._get_rgb_array())

        elif mode == 'rgb_array':
            return self._get_rgb_array()


    def _get_rgb_array(self):
        """ render the current canvas as a rgb array
        """
        buf = self.surface.render_as_pixbuf()
        w = buf.get_width()
        h = buf.get_height()

        # convert uint8 matrix whose shape is [w, h, 4]
        img = np.frombuffer(buf.get_pixels(), np.uint8).reshape(h, w, -1)
        img = img[:, :, :3]  # discard the alpha channel

        # cut out the canvas
        img = img[self.tile_offset:self.tile_offset+self.imsize,
                    self.tile_offset:self.tile_offset+self.imsize, :]

        return img

    def _close(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
    
    def _seed(self, seed=None):
        raise NotImplementedError
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    env = MyPaintEnv(logger=logger)

    # drawing something
    env.step({'position': (1.0, 1.0), 'pressure': 1.0, 'color': (1, 0, 0), 'prob': 1})

    while True:
        env.render()
        time.sleep(1)
    
    env.close()
