import boto3
import os
import pytoml as toml
from botocore.exceptions import ClientError as BotoClientError

s3 = boto3.resource('s3')
bucket = s3.Bucket('xcite-simulations')


def get(key):
    key = os.path.join(bucket, key)
    try:
        return s3.Object(key).get()['Body'].read()
    except BotoClientError as e:
        if e.response['Error']['Code'] == '404':
            return None
        else:
            raise


def status(sim):
    toml_key = os.path.join(os.path.basename(sim['directory']), 'simulation.toml')
    report_key = os.path.join(sim['directory'], sim['directory'] + '.pdf')
    try:
        remote = toml.loads(s3.Object('xcite-simulations', toml_key).get()['Body'].read().decode('utf-8'))
    except BotoClientError:
        return 'not started'
    else:
        try:
            s3.Object('xcite-simulations', report_key).get()
        except BotoClientError:
            return 'started by {}'.format(remote['server'])
        else:
            return 'downloading'


def download(sim):
    urls = []
    for item in bucket.objects.filter(Prefix=sim['directory']):
        if 'dose' in item.key:
            continue
        folder = os.path.join('reports', os.path.dirname(item.key))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join('reports', item.key)
        with open(path, 'wb') as f:
            f.write(item.get()['Body'].read())
        url = 'https://s3-us-west-2.amazonaws.com/xcite-simulations/' + item.key
        urls.append(url)
        if item.key.endswith('simulation.toml'):
            with open(path) as fp:
                sim = toml.load(fp)
                sim['urls'] = urls
    print(sim['name'])
    for url in urls:
        print('\t' + url)
    print()
    return sim


with open('simulations.toml') as f:
    simulations = toml.load(f)['simulations']


sims = []
for sim in simulations:
    sim['directory'] = sim['name'].replace(' - ', '-').replace(' ', '-')
    s = status(sim)
    print(sim['name'], s)
    if s == 'downloading':
        res = download(sim)
        if 'results' in res:
            sims.append(res)
with open('reports/results.toml', 'w') as fp:
    toml.dump(fp, {'simulations': sims})
