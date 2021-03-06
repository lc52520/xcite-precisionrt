"""

Plot a DVH from a 3ddose file. We write it so it can take a 3ddose path,
or a py3ddose Dose tuple, and a py3ddose Target object. This target has
an isocenter and a radius. From there we choose voxels that are in the
target zone, and ignore those that are not. Then we bin by dose amount
into 100 bins (for smoothness), and find those matching that predicate.

"""
import os
import argparse
import numpy as np
from . import matplotlibstub  # NOQA
import matplotlib.pyplot as plt

from .py3ddose import dvh, read_3ddose, Target


def plot_dvh(sim, data):
    """
    Assumes data is a 2d array of shape
    """
    x, y = zip(*data)
    print('x', x)
    print('y', y)
    x = np.array(x)
    y = np.array(y)
    plt.figure()
    plt.plot(x, y)
    plt.ylabel('Fractional target volume')
    plt.xlabel('Grays in 30 minutes')
    path = os.path.join(sim['directory'], 'dvh.pdf')
    plt.savefig(path)
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='+')
    args = parser.parse_args()
    dose = read_3ddose(args.input[0])
    target = Target(np.array([0, 0, 10]), 1)
    result = dvh(dose, target)
    os.makedirs('dvh', exist_ok=True)
    plot_dvh({'directory': 'dvh'}, result)
