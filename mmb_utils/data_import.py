import os
import json
import luigi

import elf.parallel as parallel
from cluster_tools.downscaling import DownscalingWorkflow
from elf.io import open_file

DEFAULT_SCALE_FACTORS = [[2, 2, 2]] * 6
DEFAULT_CHUNKS = [64, 64, 64]
DEFAULT_BLOCK_SHAPE = [64, 64, 64]


def add_max_id(in_path, in_key, out_path, out_key):
    with open_file(out_path, 'a') as f_out, open_file(in_path, 'r') as f:
        attrs = f_out[out_key].attrs
        if 'maxId' in attrs:
            return

        ds_in = f[in_key]
        max_id = ds_in.attrs.get('maxId', None)

        # TODO make a cluster task so this can be safely run on the
        # login node
        if max_id is None:
            max_id = parallel.max(ds_in, n_threads=16, verbose=True)

        attrs['maxId'] = int(max_id)


def import_segmentation(in_path, in_key, out_path, resolution,
                        tmp_folder, scale_factors=DEFAULT_SCALE_FACTORS,
                        block_shape=DEFAULT_BLOCK_SHAPE, chunks=DEFAULT_CHUNKS,
                        target='local', max_jobs=16):
    task = DownscalingWorkflow

    config_dir = os.path.join(tmp_folder, 'configs')
    os.makedirs(config_dir, exist_ok=True)

    configs = DownscalingWorkflow.get_config()
    global_conf = configs['global']
    global_conf.update({'block_shape': block_shape})
    with open(os.path.join(config_dir, 'global.config'), 'w') as f:
        json.dump(global_conf, f)

    conf = configs['copy_volume']
    conf.update({'chunks': chunks})
    with open(os.path.join(config_dir, 'copy_volume.config'), 'w') as f:
        json.dump(conf, f)

    conf = configs['downscaling']
    conf.update({'chunks': chunks, 'library_kwargs': {'order': 0}})
    with open(os.path.join(config_dir, 'downscaling.config'), 'w') as f:
        json.dump(conf, f)

    halos = scale_factors
    metadata_format = 'bdv.n5'
    metadata_dict = {'resolution': resolution, 'unit': 'micrometer'}

    t = task(tmp_folder=tmp_folder, config_dir=config_dir,
             target=target, max_jobs=max_jobs,
             input_path=in_path, input_key=in_key,
             scale_factors=scale_factors, halos=halos,
             metadata_format=metadata_format, metadata_dict=metadata_dict,
             output_path=out_path)
    ret = luigi.build([t], local_scheduler=True)
    assert ret, "Importing segmentation failed"

    add_max_id(in_path, in_key, out_path, 'setup0/timepoint0/s0')


# TODO support mrc files (np.mmap) in elf.open_file
def import_raw_volume(in_path, in_key, out_path, resolution,
                      tmp_folder, scale_factors=DEFAULT_SCALE_FACTORS,
                      block_shape=DEFAULT_BLOCK_SHAPE, chunks=DEFAULT_CHUNKS,
                      target='local', max_jobs=16):
    task = DownscalingWorkflow

    config_dir = os.path.join(tmp_folder, 'configs')
    os.makedirs(config_dir, exist_ok=True)

    configs = DownscalingWorkflow.get_config()
    global_conf = configs['global']
    global_conf.update({'block_shape': block_shape})
    with open(os.path.join(config_dir, 'global.config'), 'w') as f:
        json.dump(global_conf, f)

    conf = configs['copy_volume']
    conf.update({'chunks': chunks})
    with open(os.path.join(config_dir, 'copy_volume.config'), 'w') as f:
        json.dump(conf, f)

    conf = configs['downscaling']
    conf.update({'chunks': chunks, 'library': 'skimage'})
    with open(os.path.join(config_dir, 'downscaling.config'), 'w') as f:
        json.dump(conf, f)

    halos = scale_factors
    metadata_format = 'bdv.n5'
    metadata_dict = {'resolution': resolution, 'unit': 'micrometer'}

    t = task(tmp_folder=tmp_folder, config_dir=config_dir,
             target=target, max_jobs=max_jobs,
             input_path=in_path, input_key=in_key,
             scale_factors=scale_factors, halos=halos,
             metadata_format=metadata_format, metadata_dict=metadata_dict,
             output_path=out_path)
    ret = luigi.build([t], local_scheduler=True)
    assert ret, "Importing raw data failed"
