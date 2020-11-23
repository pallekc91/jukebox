import sys
import fire

from jukebox.data.data_processor import DataProcessor
from jukebox.hparams import setup_hparams


def run(hps="teeny", port=29500, **kwargs):
    from jukebox.utils.dist_utils import setup_dist_from_mpi

    audio_database = kwargs['audio_database']
    del kwargs['audio_database']

    rank, local_rank, device = setup_dist_from_mpi(port=port)
    print('device:', device)
    hps = setup_hparams(hps, kwargs)
    hps.ngpus = 0
    hps.nworkers = 0
    hps.argv = " ".join(sys.argv)

    hps.bs_sample, hps.nworkers, hps.bs = 1, 1, 1
    hps.bs_sample = hps.nworkers = hps.bs

    # Setup dataset
    data_processor = DataProcessor(hps, audio_database)

    data_processor.dataset.get_midi_chunk(1)


if __name__ == '__main__':
    fire.Fire(run)
