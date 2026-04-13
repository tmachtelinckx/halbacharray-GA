"""
@author: tmachtelinckx
"""

import numpy as np
import ctypes
import multiprocessing
import pandas as pd
import config 
import halbachFields


def generate_hallbach_rings(magnetSize, InnerBoreDiameter, OuterBoreDiameter, amountBand, bandRadiiGap, magnetSpace, bandSep,  HallbachRing):
    """
    Generates possible Halbach ring configurations based on the provided parameters.

    Parameters:
    - magnetSize (float): The size (diameter) of each magnet.
    - InnerBoreDiameter (float): The inner bore diameter where no magnets are placed.
    - OuterBoreDiameter (float): The outer bore diameter defining the maximum placement area.
    - amountBand (list): A list of possible numbers of magnet bands.
    - bandRadiiGap (list): A list of possible gaps between adjacent magnet bands.
    - magnetSpace (list): A list of possible spacing values between magnets in the same band.
    - bandSep (list): A list of possible separations between bands.
    - HallbachRing (class): The class that represents a single Halbach ring.

    Returns:
    - df (DataFrame): A DataFrame containing valid Halbach ring configurations.
    - num_rings_perm (int): The number of generated valid Halbach ring permutations.
    """

    # Default Values
    BandRadii = [-1]
    MagnetInBandNr = [-1]

    # Determine maximum radius at which magnets can be placed (upper threshold)
    bandRadiusThreshold = (OuterBoreDiameter / 2) - magnetSize

    # Initialize lists to store data
    data = []

    # Iterate over combinations of amountBand, bandRadiiGap, and magnetSpace
    for i in range(len(amountBand)):
        for j in range(len(bandRadiiGap)):
            for l in range(len(bandSep)):
                for k in range(len(magnetSpace)):

                    # Skip iterations where bandRadiiGap is varied but amountBand is 1
                    if amountBand[i] == 1 and bandRadiiGap[j] != 0:
                        continue

                    singleHallbachRing = HallbachRing(
                        magnetSize,
                        InnerBoreDiameter / 2,
                        BandRadii * amountBand[i],
                        MagnetInBandNr * amountBand[i],
                        bandRadiiGap[j],
                        magnetSpace[k],
                        bandSep[l]
                    )
                    bandRadius, bandMagnetNr = singleHallbachRing.getParameters()

                    if any(r > bandRadiusThreshold for r in bandRadius):
                        continue
                        #I added this section to ensure that all the best rings must have an even number of magnets for the sake of symmetry.
                        if config.even_magnet_only:
                          if any(m % 2 != 0 for m in bandMagnetNr):
                              continue

                    data.append({
                        'BandNumber': amountBand[i],
                        'BandRadiiGap': bandRadiiGap[j],
                        'MagnetSpace': magnetSpace[k],
                        'BandSeparation': bandSep[l],
                        'BandRadius': bandRadius,
                        'MagnetNr': bandMagnetNr
                    })

    df = pd.DataFrame(data)

    # Track the number of rings and the length of df
    num_rings_perm = len(df)

    return df, num_rings_perm
    
def create_spherical_mask(DSV, resolution):
    """
    Creates a spherical mask inside a cubic simulation space.

    Parameters:
    - DSV (float): Diameter of the spherical volume.
    - resolution (float): The spatial resolution of the simulation grid.

    Returns:
    - mask (numpy.ndarray): A binary mask where 1 indicates points inside the sphere.
    - octantMask (numpy.ndarray): A mask of the first octant of the sphere for symmetry reduction.
    """
    
    coordinateAxis = np.linspace(-config.simDimensions[0] / 2, config.simDimensions[0] / 2, int(1e3 * config.simDimensions[0] / resolution + 1))
    coords = np.meshgrid(coordinateAxis, coordinateAxis, coordinateAxis)

    mask = np.zeros(np.shape(coords[0]))
    mask[np.square(coords[0]) + np.square(coords[1]) + np.square(coords[2]) <= (DSV / 2) ** 2] = 1

    octantMask = np.copy(mask)
    octantMask[coords[0] < 0] = 0
    octantMask[coords[1] < 0] = 0
    octantMask[coords[2] < 0] = 0


    return mask, octantMask

def extract_symmetric_ring_positions(ringPositions):
    """
    Extracts only the non-negative positions of Halbach rings.

    Parameters:
    - ringPositions (numpy.ndarray): Array containing ring positions.

    Returns:
    - numpy.ndarray: An array of ring positions that are non-negative.
    """
    return ringPositions[ringPositions >= 0]

def _compute_shim_fields_for_position(args):
    """
    Worker function: computes shim fields for a single ring position across all configurations.
    Designed to be called in parallel via multiprocessing.Pool.
    """
    positionIdx, position, df_records, octantMask, simDimensions, magnetSize, resolution = args

    num_rings = len(df_records)
    result = np.zeros((int(np.sum(octantMask)), num_rings))

    rings = (0,) if position == 0 else (-position, position)

    for sizeIdx, row in enumerate(df_records):
        fieldData = None
        for band_idx in range(int(row['BandNumber'])):
            band_field_data = halbachFields.createHalbach(
                numMagnets=int(row['MagnetNr'][band_idx]),
                rings=rings,
                radius=row['BandRadius'][band_idx],
                magnetSize=magnetSize,
                resolution=1e3 / resolution,
                simDimensions=simDimensions
            )
            if fieldData is None:
                fieldData = np.zeros_like(band_field_data)
            fieldData += band_field_data

        result[:, sizeIdx] = fieldData[octantMask == 1, 0]

    return positionIdx, result

def compute_shim_fields(df, ringPositionsSymmetry, octantMask, simDimensions, magnetSize, resolution, n_workers=None):
    """
    Computes the shim fields for each ring position and size.

    Parameters:
    - df (DataFrame): DataFrame containing Halbach ring configurations.
    - ringPositionsSymmetry (numpy.ndarray): Array of non-negative ring positions.
    - octantMask (numpy.ndarray): Binary mask for the simulation domain.
    - simDimensions (tuple): The dimensions of the simulation space.
    - magnetSize (float): The size of each magnet.
    - resolution (float): The resolution of the simulation grid.
    - n_workers (int, optional): Number of parallel worker processes. Defaults to all available CPUs.

    Returns:
    - shimFields (numpy.ndarray): 3D array storing the shim fields for each configuration.
    - num_positions (int): The number of symmetric ring positions processed.
    """
    num_positions = np.size(ringPositionsSymmetry)
    num_rings = df.shape[0]
    shimFields = np.zeros((int(np.sum(octantMask)), num_positions, num_rings))

    # Convert df rows to plain dicts so they are picklable for multiprocessing
    df_records = df.to_dict('records')

    args_list = [
        (positionIdx, position, df_records, octantMask, simDimensions, magnetSize, resolution)
        for positionIdx, position in enumerate(ringPositionsSymmetry)
    ]

    with multiprocessing.Pool(processes=n_workers) as pool:
        for positionIdx, result in pool.imap_unordered(_compute_shim_fields_for_position, args_list):
            shimFields[:, positionIdx, :] = result
            print(f"  Computed shim fields for position {positionIdx + 1}/{num_positions}", flush=True)

    return shimFields, num_positions

def initialize_shared_data(shimFields):
    shared_data_base = multiprocessing.Array(ctypes.c_double, np.size(shimFields))
    shared_data = np.ctypeslib.as_array(shared_data_base.get_obj())
    shared_data = shared_data.reshape(np.size(shimFields, 0), np.size(shimFields, 1), np.size(shimFields, 2))
    shared_data[...] = shimFields[...]
    return shared_data
