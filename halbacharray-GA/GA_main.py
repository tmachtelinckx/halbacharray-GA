import os
import numpy as np
import random
from deap import base, tools, creator
import time
from halbachRings import HallbachRing
import psutil
import threading
import config

from field_calculations import fieldError, calculate_field_characteristics
from documentation import save_dataframe_to_excel, save_duplicate_statistics,save_comprehensive_results, save_hof_and_logbook
from pbs_monitor import get_current_job_id, monitor_pbs_resources
from genetic_function import island_model
from initialization import initialize_shared_data, generate_hallbach_rings, create_spherical_mask, extract_symmetric_ring_positions, compute_shim_fields


#-------------------------------LAMBDA FUNCTION DEFINITIONS--------------------------------------#


# Replace lambda functions with named functions
def generate_indices():
    return random.randint(0, num_rings_perm - 1)

def create_individual():
    return creator.Individual([generate_indices() for _ in range(num_positions)])

def create_population(n):
    return [create_individual() for _ in range(n)]

def evaluate(individual):
    return fieldError(individual, shared_data)


#------------------------------------DEAP TOOLBOX SETUP-------------------------------------#

def setup_deap_toolbox(num_rings_perm, num_positions):
    """Sets up the DEAP toolbox for genetic algorithm operations."""
    try:
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
    except AttributeError:
        pass  # Already created

    toolbox = base.Toolbox()
    toolbox.register("indices", generate_indices)
    toolbox.register("individual", create_individual)
    toolbox.register("population", create_population)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=0, up=num_rings_perm - 1, indpb=0.2)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("evaluate", evaluate)

    return toolbox

#-----------------------------------MAIN EXECUTION-----------------------------------------#

if __name__ == '__main__':

    # Get PBS Job ID and Start Execution Timer
    job_id = get_current_job_id()
    total_start_time = time.time()

    # Create a folder to save results if it doesn't already exist
    results_folder = "GA_Results"
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    # Start memory monitoring in a separate thread
    memory_log_file = os.path.join(results_folder, "memory_usage.csv")
    memory_monitor_thread = threading.Thread(target=monitor_pbs_resources, args=(job_id, 600, memory_log_file))
    memory_monitor_thread.daemon = True  # Allows the thread to close with the main program
    memory_monitor_thread.start()

    # Generate Hallbach Rings
    df, num_rings_perm = generate_hallbach_rings(
        config.magnetSize, config.InnerBoreDiameter, config.OuterBoreDiameter,
        config.amountBand, config.bandRadiiGap,
        config.magnetSpace, config.bandSep, HallbachRing
    )

    # Create Spherical Mask
    mask, octantMask = create_spherical_mask(config.DSV, config.resolution)

    # Only use Symmetrical Rings (For Efficiency)
    ringPositionsSymmetry = extract_symmetric_ring_positions(config.ringPositions)

    # Compute shim fields
    shimFields, num_positions = compute_shim_fields(
        df, ringPositionsSymmetry, octantMask, config.simDimensions,
        config.magnetSize, config.resolution, n_workers=int(os.environ.get('PBS_NCPUS', os.cpu_count())))
    
    # Share shim fields data (For multi node calculations)
    shared_data = initialize_shared_data(shimFields)

    del shimFields, octantMask, mask  # None of these are needed beyond this point

    # Set up DEAP toolbox
    toolbox = setup_deap_toolbox(num_rings_perm, num_positions)

    excel_file_path = save_dataframe_to_excel(df, results_folder, config.InnerBoreDiameter, config.OuterBoreDiameter, config.magnetSize)
    # Run Island Model GA with duplicate tracking
    start_time = time.time()

    final_pops, logs, hof, duplicate_stats = island_model(
        toolbox, config.CXPB, config.MUTPB, config.NGEN, config.num_islands, config.NGEN, 
        config.migration_interval, config.popSim, config.selected_algorithm)

    end_time = time.time()


    # Save duplicate statistics
    duplicate_file = save_duplicate_statistics(duplicate_stats, results_folder)


    # Calculate field characteristics for the best individual
    best_individual = hof[0]
    mean_field, homogeneity = calculate_field_characteristics(best_individual, shared_data)
    
    # Calculate total execution time
    total_end_time = time.time()
    algorithm_time = end_time - start_time
    total_execution_time = total_end_time - total_start_time

    # Save comprehensive results
    comprehensive_results_file = save_comprehensive_results(
        best_individual, mean_field, homogeneity, 
        algorithm_time, total_execution_time, config.NGEN, results_folder, config.ringPositions
    )

    # Save Hall of Fame and Logbook
    hof_file, logbook_file = save_hof_and_logbook(hof, logs, results_folder)

    print(f"Hall of Fame saved to: {hof_file}")
    print(f"Logbook saved to: {logbook_file}")
    print(f"Comprehensive results saved to: {comprehensive_results_file}")
    print(f"Duplicate statistics saved to: {duplicate_file}")