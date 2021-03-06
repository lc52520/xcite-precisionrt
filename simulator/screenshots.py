import asyncio
import os
import argparse
import platform

import pytoml as toml
from beamviz import visualize

from .utils import run_command, run_async

SCAD = 'openscad'
if platform.system() == 'Darwin':
    SCAD = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'


async def make_screenshot(conf, scad_path):
    img_path = os.path.splitext(scad_path)[0] + '-{}.png'.format(conf['name'])
    camera = conf['translation'] + conf['rotation'] + [conf['distance']]
    camera = list(map(str, camera))
    await run_command([
        SCAD,
        '--camera', ','.join(camera),
        scad_path, '-o', img_path,
        '--imgsize', ','.join(map(str, conf['size'])),
        '--autocenter'
    ])
    conf['path'] = img_path
    return conf


async def make_screenshots(shots, scad_path):
    futures = [make_screenshot(shot, scad_path) for shot in shots]
    return await asyncio.gather(*futures)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='screenshots.toml')
    # parser.add_argument('scad')
    args = parser.parse_args()
    with open(args.config) as fp:
        shots = toml.load(fp)['shots']
    with open('simulations.toml') as fp:
        simulations = toml.load(fp)['simulations']
    for sim in simulations:
        d = os.path.abspath(os.path.join('reports', sim['name'].replace(' - ', '-').replace(' ', '-')))
        scad_path = os.path.join(d, 'collimator.scad')
        await make_screenshots(shots, scad_path)


if __name__ == '__main__':
    run_async(main())
