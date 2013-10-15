import sys
import numpy as np
from util2dpolim.movie import Movie
from util2dpolim.misc import grid_image_section_into_squares_and_define_spots, \
    save_hdf5, \
    combine_outputs, \
    show_mem, \
    find_measurement_files_in_directory
import time as stopwatch

from mpi4py import MPI
comm = MPI.COMM_WORLD
myrank = comm.Get_rank()
nprocs = comm.Get_size()

show_mem()
tstart = stopwatch.time()


prefix = '/home/rafael/Desktop/Win/Well 01/'

basename = 'Cells-633ex-Well1-Area-01.SPE'

bgbounds   = [3,110,53,490]
fullbounds = [60,110,480,490]
resolution = 4
Nrowsatatime = 20*resolution


for r in np.arange(fullbounds[1], fullbounds[3], Nrowsatatime):

    m = Movie( prefix, basename )
    m.define_background_spot( bgbounds )

    bounds = [ fullbounds[0], r, fullbounds[2], r+Nrowsatatime ]
    if myrank==0: print 'current bounds: ',bounds

    grid_image_section_into_squares_and_define_spots( m, res=resolution, bounds=bounds )
    if myrank==0: print 'nspots: ',len(m.spots)

    m.collect_data()
    m.correct_emission_intensities( corrM=0.075 , corrphase=90*np.pi/180 )
    m.startstop()
    m.assign_portrait_data()
    m.are_spots_valid(SNR=4)
    # the rest is done only if we actually have any valid spots here
    if not len(m.validspots)==0:
        # m.fit_all_portraits_spot_parallel()
        # m.find_modulation_depths_and_phases()

        myspots = np.array_split( np.arange(len(m.validspots)), nprocs )
        m.fit_all_portraits_spot_parallel_selective( myspots[myrank] )
        m.find_modulation_depths_and_phases_selective( myspots[myrank] )
        m.ETrulerFFT_selective( myspots[myrank] )
        #    m.ETmodel_selective( myspots[myrank] )

        # all processes save their contributions separately
        save_hdf5( m, myspots[myrank], prefix, myrank )

print 'p=',myrank,': done. ',(stopwatch.time()-tstart)

comm.barrier()

# first process gets to combine them into a single file
if myrank==0: combine_outputs( m.data_basename, prefix )

# all done







