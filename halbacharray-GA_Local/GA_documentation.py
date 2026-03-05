import pandas as pd
import os
import csv
import psutil
import time
import threading

def save_hallbach_configurations(df, folder="GA_Results", filename="halbach_configurations.csv"):
    """
    Save the Halbach ring configurations DataFrame to a CSV file.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing Halbach ring configurations.
    folder : str
        Folder where CSV will be saved.
    filename : str
        Name of the CSV file.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(folder, filename)
    df.to_csv(path, index=False)
    print(f"Halbach configurations saved to {path}")


def save_fitness_per_generation(minTracker, folder="GA_Results", filename="fitness_per_generation.csv"):
    """
    Save the minimum fitness value per generation to CSV.

    Parameters
    ----------
    minTracker : list or numpy array
        Minimum fitness per generation.
    folder : str
        Folder where CSV will be saved.
    filename : str
        Name of the CSV file.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(folder, filename)
    df = pd.DataFrame({"Generation": range(1, len(minTracker) + 1),
                       "MinFitness": minTracker})
    df.to_csv(path, index=False)
    print(f"Fitness per generation saved to {path}")


def save_best_vector(best_vector, df_meters, ring_positions, folder="GA_Results", filename="best_vector.csv"):
    """
    Save the best individual's configuration to a CSV file.

    Parameters
    ----------
    best_vector : list
        Indices of the best ring configuration per position.
    df_meters : pandas.DataFrame
        DataFrame with ring configuration options.
    ring_positions : list or numpy array
        Positions of the rings corresponding to the best vector.
    folder : str
        Folder to save CSV file.
    filename : str
        Name of the CSV file.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    rows = []
    for pos_idx, df_idx in enumerate(best_vector):
        row = df_meters.iloc[df_idx]
        position = ring_positions[pos_idx]
        rows.append({
            "RingPosition_m": position,
            "BandNumber": row['BandNumber'],
            "BandRadii_m": row['BandRadius'],
            "MagnetNr": row['MagnetNr'],
            "BandRadiiGap_m": row['BandRadiiGap'],
            "MagnetSpace_m": row['MagnetSpace'],
            "BandSeparation_m": row['BandSeparation']
        })

    path = os.path.join(folder, filename)
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Best vector configuration saved to {path}")


def save_custom_csv(data, folder="GA_Results", filename="custom.csv"):
    """
    Save any list of dictionaries or DataFrame as a CSV.

    Parameters
    ----------
    data : list of dict or pandas.DataFrame
        Data to save.
    folder : str
        Folder where CSV will be saved.
    filename : str
        CSV file name.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(folder, filename)
    if isinstance(data, pd.DataFrame):
        data.to_csv(path, index=False)
    else:
        # assume list of dicts
        keys = data[0].keys()
        with open(path, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
    print(f"Data saved to {path}")



def track_system_usage(folder="GA_Results", filename="system_usage.csv", interval=1):
    """
    Track RAM and CPU usage over time in a separate thread.
    
    Parameters
    ----------
    folder : str
        Folder to save the CSV.
    filename : str
        CSV filename.
    interval : int
        Time interval between measurements in seconds.
    
    Returns
    -------
    stop_event : threading.Event
        Event to signal the tracking thread to stop.
    thread : threading.Thread
        The tracking thread object.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    path = os.path.join(folder, filename)
    stop_event = threading.Event()
    data = []

    def monitor():
        start_time = time.time()
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=None)
            data.append({
                "Time_s": elapsed,
                "CPU_percent": cpu,
                "RAM_percent": mem.percent,
                "RAM_used_MB": mem.used / (1024**2),
                "RAM_total_MB": mem.total / (1024**2)
            })
            time.sleep(interval)
        # Save to CSV when stopping
        pd.DataFrame(data).to_csv(path, index=False)
        print(f"System usage logged to {path}")

    thread = threading.Thread(target=monitor)
    thread.start()
    return stop_event, thread