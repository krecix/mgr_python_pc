import numpy
import matplotlib.pyplot as plt
import csv
from geneticUtils import getSignalEnvelope, movingFilter, MOVE_FILTER_LENGTH

def parse_measurements(values):
    t= numpy.arange(0, len(values))
    dt = t[1] - t[0]

    x = values
    v = numpy.gradient(x, dt)
    a = numpy.gradient(v, dt)

    envelope_x = getSignalEnvelope(x)
    filteringEnvelope_x = movingFilter(envelope_x, MOVE_FILTER_LENGTH)
    maxValue_x = filteringEnvelope_x[filteringEnvelope_x.argmax()]
    print("Max x: %d" % maxValue_x)

    envelope_v = getSignalEnvelope(v)
    filteringEnvelope_v = movingFilter(envelope_v, MOVE_FILTER_LENGTH)
    maxValue_v = filteringEnvelope_v[filteringEnvelope_v.argmax()]
    print("Max v: %d" % maxValue_v)

    envelope_a = getSignalEnvelope(a)
    filteringEnvelope_a = movingFilter(envelope_a, MOVE_FILTER_LENGTH)
    maxValue_a = filteringEnvelope_a[filteringEnvelope_a.argmax()]
    print("Max a: %d" % maxValue_a)

    save_data(maxValue_x, 
              maxValue_v, 
              maxValue_a)
    
    show_plots(t, x, v, a, filteringEnvelope_x, filteringEnvelope_v, filteringEnvelope_a)
   

def show_plots(t, x, v, a, filteringEnvelope_x, filteringEnvelope_v, filteringEnvelope_a):
    plt.plot(x)
    plt.plot(v)
    plt.plot(a)

    plt.plot(filteringEnvelope_x)
    plt.plot(filteringEnvelope_v)
    plt.plot(filteringEnvelope_a)

    plt.legend(["x [$\mu m$]", "v [$\mu m/s$]", "a [$\mu m/s^2$]",
                "$x_{env}$ [$\mu m$]", "$v_{env}$ [$\mu m/s$]", "$a_{env}$ [$\mu m/s^2$]"])
    plt.show()

def save_data(x, v, a):
    data = [
        [x, v, a]
    ]
    path = 'measurements.csv'
    with open(path, 'a', newline='') as file_csv:
        writer = csv.writer(file_csv)
        writer.writerows(data)

    print(f'Dane zostały zapisane do pliku {path}')
