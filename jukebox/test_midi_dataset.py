print("starting imports")
import sys
import fire

from jukebox.data.data_processor import DataProcessor
from jukebox.hparams import setup_hparams
print("done importing everything")

def run(hps="teeny", port=29500, **kwargs):
    from jukebox.utils.dist_utils import setup_dist_from_mpi

    audio_database = kwargs['audio_database']
    del kwargs['audio_database']

    rank, local_rank, device = setup_dist_from_mpi(port=port)
    print('device:', device)
    print("hps setup")
    hps = setup_hparams(hps, kwargs)
    hps.ngpus = 0
    hps.nworkers = 0
    hps.argv = " ".join(sys.argv)

    hps.bs_sample, hps.nworkers, hps.bs = 1, 1, 1
    hps.bs_sample = hps.nworkers = hps.bs
    print("setting up database")
    # Setup dataset
    data_processor = DataProcessor(hps, audio_database)
    print("midi chunk call")
    for idx in range(8868):
        chunk = data_processor.dataset.get_midi_chunk(idx)
        if chunk.shape != (95, 200):
            print(chunk.shape)
            raise RuntimeError('It failed')

if __name__ == '__main__':
    fire.Fire(run)
