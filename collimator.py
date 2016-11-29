import argparse

import egsinp


def make_blocks(**kwargs):
    length = kwargs['length']
    septa = kwargs['septa']
    width = kwargs['width']  # phantom width TODO change to source max width
    size = kwargs['size']
    target_distance = kwargs['target_distance']  # focus from phantom side
    target_width = kwargs['target_width']
    n_blocks = kwargs['blocks']
    # source is considered z = 0, positive 'down'

    # first phantom hole on the right (to be copied, translated, and reflected)
    # z of these is length
    # center = ((septa / 2 + size, 0))
    points = [
        (-size, 0),
        (-size / 2, -size / 2),
        (size / 2, -size / 2),
        (size, 0),
        (size / 2, size / 2),
        (-size / 2, size / 2)
    ]
    dx = size * 2 + septa
    width_remaining = width / 2 - dx
    regions = []

    def translate(points, dx):
        translated = []
        for x, y in points:
            translated.append((x + dx, y))
        return translated
    i = 0
    while width_remaining >= 0:
        translated = translate(points, i * dx)
        regions.append(translated)
        width_remaining -= dx
        i += 1

    # here we copy/reflect
    def reflect(points):
        reflected = []
        for x, y in points:
            reflected.append((-x, y))
        return reflected

    # ok now we have all points on phantom side
    # and we have the target points
    # we need to choose our x2 value
    def find_x(x0, z0, x1, z1, z2):
        m = (z1 - z0) / ((x1 - x0) or 0.000001)
        x2 = (z2 - z0) / m + x0
        return x2
    # so now we need to interpolate between these
    # but for now, do we care? can't we just run it?
    # no, we need them, and a lot of them probably
    # so how do we interpolate?
    # we have all the value, and also what z focus??
    # z focus will be negative infty

    block_length = length / n_blocks
    target_x_left = -target_width / 2
    target_x_right = target_width / 2
    target_z = length + target_distance
    blocks = []
    for i in range(n_blocks):
        current_z = i * block_length
        block_regions = []
        for region in regions:
            phantom_x_left = region[0][0]
            left_x = find_x(target_x_left, target_z, phantom_x_left, length, current_z)
            phantom_x_right = region[3][0]
            right_x = find_x(target_x_right, target_z, phantom_x_right, length, current_z)
            size = (right_x - left_x) / 2
            # scale that shit? no, we need to get the right values
            # print(size)
            block_regions.append([
                (left_x, 0),
                (left_x + size / 2, -size / 2),
                (left_x + 3 * size / 2, -size / 2),
                (left_x + 2 * size, 0),
                (left_x + 3 * size / 2, size / 2),
                (left_x + size / 2, size / 2)
            ])
        for region in block_regions[1:]:
            block_regions.insert(0, reflect(region))
        blocks.append({
            'zmin': current_z,
            'zmax': current_z + block_length,
            'regions': block_regions
        })
    return blocks


def add_collimator(template, args):
    kwargs = {
        'length': args.length,
        'septa': args.septa_width,
        'size': args.hole_size,
        'width': args.width,
        'blocks': args.blocks,
        'target_distance': args.target_distance,
        'target_width': args.target_width,
        'rmax': args.rmax
    }
    blocks = make_blocks(**kwargs)
    for i, block in enumerate(blocks):
        cm = {
            'type': 'BLOCK',
            'identifier': 'BLCK{}'.format(i),
            'rmax_cm': kwargs['rmax'],
            'title': 'BLCK{}'.format(i),
            'zmin': block['zmin'],
            'zmax': block['zmax'],
            'zfocus': kwargs['length'] + kwargs['target_distance'],
            'xpmax': kwargs['rmax'],
            'ypmax': kwargs['rmax'],
            'xnmax': -kwargs['rmax'],
            'ynmax': -kwargs['rmax'],
            'air_gap': {
                'ecut': 0.811,
                'pcut': 0.01,
                'dose_zone': 0,
                'iregion_to_bit': 0
            },
            'opening': {
                'ecut': 0.811,
                'pcut': 0.01,
                'dose_zone': 0,
                'iregion_to_bit': 0,
                'medium': 'Air_516kVb'
            },
            'block': {
                'ecut': 0.521,
                'pcut': 0.01,
                'dose_zone': 0,
                'iregion_to_bit': 0,
                'medium': 'PB516'
            },
            'regions': []
        }
        for region in block['regions']:
            cm['regions'].append({
                'points': [{'x': x, 'y': y} for x, y in region]
            })
        template['cms'].append(cm)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--length', type=float, default=10)
    parser.add_argument('--blocks', type=int, default=10)
    parser.add_argument('--hole-size', type=float, default=0.2)
    parser.add_argument('--septa-width', type=float, default=-0.05)
    parser.add_argument('--width', type=float, default=60)
    parser.add_argument('--target-distance', type=float, default=40.0)
    parser.add_argument('--target-width', type=float, default=1.0)
    parser.add_argument('--rmax', type=float, default=40.0)
    parser.add_argument('output')
    args = parser.parse_args()
    template = egsinp.parse_egsinp(open('template.egsinp').read())
    add_collimator(template, args)
    print(len(template['cms'][1]['regions']))
    print(template['cms'][1]['regions'][30])
    open(args.output, 'w').write(egsinp.unparse_egsinp(template))
    print('Wrote to {}'.format(args.output))
