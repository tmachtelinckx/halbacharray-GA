# Halbach Ring Magnetic Field Optimization

## Overview
This project uses a genetic algorithm (GA) to optimize the configuration of Halbach ring arrays for generating homogeneous magnetic fields. The algorithm tries to find the optimal placement and sizing of multiple Halbach rings to create a target magnetic field strength while maximizing field homogeneity.

## Requirements
- Python 3.x
- Required packages: numpy, scipy, pandas, deap, matplotlib, psutil

## Project Structure
- `GA_main.py`: Main entry point for the genetic algorithm
- `config.py`: Configuration file with all tunable parameters
- `halbachRings.py`: Defines the Halbach ring class and related functions
- `halbachFields.py`: Functions for calculating magnetic fields from Halbach arrays
- `field_calculations.py`: Functions to calculate field characteristics and error metrics
- `genetic_function.py`: Implementation of the island model genetic algorithm
- `initialization.py`: Functions to initialize the simulation environment
- `pbs_monitor.py`: Utility for monitoring PBS job resources
- `documentation.py`: Creates readable documents for results logging
- `GA_scheduler.job`: PBS job scheduler script

## Configuration Options
The `config.py` file contains all parameters that can be adjusted:

### Ring Dimensions
```python
# Inner and outer diameter limits of the rings
InnerBoreDiameter = 160 * 1e-3  # Inner Diameter of the Ring (m)
OuterBoreDiameter = 250 * 1e-3  # Outer Diameter of the Ring (m)
magnetSize = 12 * 1e-3          # Length of cube magnets (m)
```

### Variable Ring Parameters
```python
amountBand = np.array([1,2])                # Number of bands within each ring
bandRadiiGap = np.linspace(0, 0.1, 60)      # Space between bands (mm)
magnetSpace = np.linspace(0, 0.05, 35)      # Space between magnets (mm)
bandSep = np.linspace(0.002, 0.1, 60)       # Space between bore and 1st band (mm)
```

### Ring Positions
The code provides three options for configuring ring positions. Uncomment only one section:

1. **Hard-Coded Ring Separation and Array Length**:
```python
arrayLength_0 = 240 * 1e-3       # Total array length (m)
ringSep = 0.022                  # Separation between rings (m)
numRings_1 = arrayLength_0 / ringSep
numRings = int(numRings_1) + 1
arrayLength = ringSep * (numRings-1)
ringPositions = np.linspace(-arrayLength / 2, arrayLength / 2, numRings)
```

2. **Hard-Coded Ring Number and Array Length** (currently commented):
```python
arrayLength_0 = 240 * 1e-3
numRings = 8
arrayLength = arrayLength_0
ringSep = arrayLength/(numRings-1)
ringPositions = np.linspace(-arrayLength / 2, arrayLength / 2, numRings)
```

3. **Hard-Coded Ring Number and Ring Separation** (currently commented):
```python
ringSep = 0.05
numRings = 22
arrayLength = ringSep * (numRings-1)
ringPositions = np.linspace(-arrayLength / 2, arrayLength / 2, numRings)
```

### Field Error Parameters
```python
T_target = 0.05                # Target field strength in Tesla
homogeneity_weight = 0.85      # Weight for homogeneity error (between 0-1)
field_strength_weight = 0.15   # Weight for field strength error (between 0-1)
```
Note: `homogeneity_weight + field_strength_weight` should equal 1.0

### Simulation Parameters
```python
resolution = 20                      # Spatial resolution (higher values = lower precision)
DSV = 0.6 * InnerBoreDiameter        # Diameter of Spherical Volume (mm)
simDimensions = (DSV, DSV, DSV)      # 3D dimensions of simulation space (mm)
```

### Genetic Algorithm Parameters
```python
popSim = 500000                      # Total population size across all islands
CXPB, MUTPB = 0.6, 0.3               # Crossover and mutation probabilities
maxGeneration = 150                  # Maximum generations
NGEN = maxGeneration                 # Alias for maxGeneration
num_islands = 24                     # Number of islands (subpopulations)
migration_interval = 15              # Generations between migrations
selected_algorithm = "eaSimple"      # EA algorithm type: "eaSimple", "eaMuPlusLambda", or "eaMuCommaLambda"
```

## Running the Algorithm

### Local Execution
To run the algorithm locally, go into the `halbacharray-GA_Local` folder and execute GA_Local.py:
```bash
python GA_Local.py
```

This folder contains a self-contained, locally runnable version of the Halbach array GA, including (`GA_Local.py`), (`GA_documentation.py`), (`HallbachRing_Edit_1.py`), and (`halbachFields.py`).

### Using PBS Scheduler
The project includes a PBS scheduler job script (`GA_scheduler.job`) for running on HPC clusters:

1. **Job Configuration**:
```bash
#PBS -l select=1:ncpus=24:mpiprocs=24   # Resource allocation: 1 node, 24 CPUs
#PBS -P ????                       # Project ID
#PBS -q smp                             # Queue name
#PBS -l walltime=24:00:00               # Maximum runtime (24 hours)
#PBS -o /mnt/lustre/users/......./GA_Island_Model/GA_out.out  # Output file
#PBS -e /mnt/lustre/users/......./GA_Island_Model/GA_err.err  # Error file
```

2. **Environment Setup**:
```bash
# Load Python module
module add chpc/python/anaconda/3-2021.11

# Initialize conda
eval "$(conda shell.bash hook)"

# Activate environment
conda activate /home/tmachtelinckx/myenv

# Change to project directory
cd /mnt/lustre/users/tmachtelinckx/GA_Island_Model
```

3. **Submit the Job**:
```bash
qsub GA_scheduler.job
```

4. **Monitor Job**:
```bash
qstat -u <username>
```

## Output
The algorithm creates a `GA_Results` folder containing:
- Excel file with ring configurations
- Memory usage logs
- Duplicate statistics
- Comprehensive results with best individual
- Hall of Fame and logbook records

## Performance Monitoring
The code includes resource monitoring through the `pbs_monitor.py` module:
- Tracks CPU usage, memory usage, and walltime
- Records data at regular intervals (default: every 600 seconds)
- Saves data to a CSV file for post-processing analysis

## Tips for Optimization
1. Adjust `homogeneity_weight` and `field_strength_weight` based on your priority between field uniformity and strength
2. Increase `popSim` for better exploration of the solution space
3. Adjust `CXPB` and `MUTPB` to balance exploration vs exploitation
4. Match `num_islands` to available CPU cores for optimal parallelization
5. For longer runs, increase the `walltime` in the PBS script

## Island Model GA Parameters
The algorithm uses an island model approach to improve genetic diversity:
- Population is divided into `num_islands` subpopulations
- Each island evolves independently for `migration_interval` generations
- After each interval, individuals migrate between islands
- Helps prevent premature convergence to local optima

## Algorithm Selection
Three evolutionary algorithms are available:
1. `eaSimple`: Traditional generational genetic algorithm
2. `eaMuPlusLambda`: Selects best individuals from both parents and offspring
3. `eaMuCommaLambda`: Selects best individuals only from offspring

## Acknowledgments
Original authors: tmachtelinckx, to_reilly

