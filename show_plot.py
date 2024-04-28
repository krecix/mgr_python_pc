import sys
import pandas as pd
import numpy as np
from calculations import parse_measurements

if __name__ == "__main__":
    number = int(sys.argv[1])
    time_series = pd.read_csv(f'time_series/{number}.csv')

    start_index = np.asarray(time_series["x"]).argmax()
    if (start_index > 100):
        start_index = 0

    print(time_series)
    print(f"Start Index: {start_index}")

    x, v, a = parse_measurements(time_series["x"], time_series["u"], 
                                 skipped_samples=start_index, show_plot=True)
    