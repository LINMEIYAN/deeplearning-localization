'''
Generate sensors and training data
'''

from typing import List

import random
import numpy as np
import imageio
import argparse
import os
from visualize import Visualize
from propagation import Propagation
from input_output import Default
from node import Sensor
from utility import Utility


class GenerateSensors:
    '''generate sensors
    '''
    @classmethod
    def random(cls, grid_length: int, sensor_density: int, seed: int, filename: str):
        '''randomly generate some sensors in a grid
        '''
        random.seed(seed)
        all_sensors = list(range(grid_length * grid_length))
        subset_sensors = random.sample(all_sensors, sensor_density)
        Visualize.sensors(subset_sensors, grid_length, 1)
        subset_sensors = GenerateSensors.relocate_sensors(subset_sensors, grid_length)
        Visualize.sensors(subset_sensors, grid_length, 2)
        subset_sensors = GenerateSensors.relocate_sensors(subset_sensors, grid_length)
        Visualize.sensors(subset_sensors, grid_length, 3)
        subset_sensors.sort()
        GenerateSensors.save(subset_sensors, grid_length, filename)

    @classmethod
    def relocate_sensors(cls, random_sensors: List, grid_len: int):
        '''Relocate sensors that are side by side
        '''
        new_random_sensors = []
        need_to_relocate = []
        ocupy_grid = np.zeros((grid_len, grid_len), dtype=int)
        random_sensors.sort()
        for sen in random_sensors:
            s_x = sen // grid_len
            s_y = sen % grid_len
            if ocupy_grid[s_x][s_y] == 1:
                need_to_relocate.append(sen)
            else:
                new_random_sensors.append(sen)
                for x, y in [(0, 0), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]:
                    try:
                        ocupy_grid[s_x + x][s_y + y] = 1
                    except:
                        pass
        available = []
        for x in range(grid_len):
            for y in range(grid_len):
                if ocupy_grid[x][y] == 0:
                    available.append(x*grid_len + y)

        relocated = random.sample(available, len(need_to_relocate))
        new_random_sensors.extend(relocated)
        return new_random_sensors

    @classmethod
    def save(cls, sensors: List[int], grid_length: int, filename: str):
        with open(filename, 'w') as f:
            for sensor in sensors:
                x = sensor // grid_length
                y = sensor % grid_length
                f.write(f'{x} {y}\n')


class GenerateData:
    '''generate training data using a propagation model
    '''
    def __init__(self, seed: int, alpha: float, std: float, grid_length: int, cell_length: int, sensor_density: int):
        self.seed = seed
        self.alpha = alpha
        self.std = std
        self.grid_length = grid_length
        self.cell_length = cell_length
        self.sensor_density = sensor_density
        self.propagation = Propagation(self.alpha, self.std)

    def generate(self, power: float, cell_percentage: float, sample_per_cell: int, sensor_file: str, root_dir: str):
        '''
        Args:
            power           -- the power of the transmitter
            cell_percentage -- percentage of cells being label (see if all discrete location needs to be labels)
            sample_per_cell -- samples per cell
            sensor_file -- sensor location file
            root_dir    -- the image output directory
        '''
        Utility.remove_make(root_dir)

        random.seed(self.seed)
        # 1 read the sensor file, do a checking
        if str(self.grid_length) not in sensor_file[:sensor_file.find('-')]:
            print(f'grid length {self.grid_length} and sensor file {sensor_file} not match')

        sensors = []
        with open(sensor_file, 'r') as f:
            indx = 0
            for line in f:
                x, y = line.split()
                sensors.append(Sensor(int(x), int(y), indx))
                indx += 1

        # 2 start from (0, 0), generate data, might skip some locations
        label_count = int(self.grid_length * self.grid_length * cell_percentage)
        population = [(i, j) for j in range(self.grid_length) for i in range(self.grid_length)]
        labels = random.sample(population, label_count)

        for label in labels:
            tx = label           # each label create a directory
            os.mkdir(f'{root_dir}/{tx}')
            for i in range(sample_per_cell):
                grid = np.zeros((self.grid_length, self.grid_length))
                grid.fill(Default.noise_floor)
                for sensor in sensors:
                    dist = Utility.distance(tx, (sensor.x, sensor.y))
                    pathloss = self.propagation.pathloss(dist)
                    rssi = power - pathloss
                    grid[sensor.x][sensor.y] = rssi if rssi > Default.noise_floor else Default.noise_floor
                imageio.imwrite(f'{root_dir}/{tx}/{i}.png', grid)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Localize multiple transmitters')

    parser.add_argument('-gs', '--generate_sensor', action='store_true')
    parser.add_argument('-gd', '--generate_data', action='store_true')
    parser.add_argument('-al', '--alpha', nargs=1, type=float, default=[Default.alpha], help='the slope of pathloss')
    parser.add_argument('-st', '--std', nargs=1, type=float, default=[Default.std], help='the standard deviation zero mean Guassian')
    parser.add_argument('-gl', '--grid_length', nargs=1, type=int, default=[Default.grid_length], help='the length of the grid')
    parser.add_argument('-cl', '--cell_length', nargs=1, type=float, default=[Default.cell_length], help='the length of a cell')
    parser.add_argument('-rs', '--random_seed', nargs=1, type=int, default=[Default.random_seed], help='random seed')
    parser.add_argument('-sd', '--sensor_density', nargs=1, type=int, default=[Default.sen_density], help='number of sensors')
    parser.add_argument('-po', '--power', nargs=1, type=int, default=[Default.power], help='the power of the transmitter')
    parser.add_argument('-cp', '--cell_percentage', nargs=1, type=int, default=[Default.cell_percentage], help='percentage of cells being labels')
    parser.add_argument('-sl', '--sample_per_label', nargs=1, type=int, default=[Default.sample_per_label], help='# of samples per label')
    parser.add_argument('-rd', '--root_dir', nargs=1, type=str, default=[Default.root_dir], help='the root directory for the images')

    args = parser.parse_args()

    random_seed = args.random_seed[0]
    grid_length = args.grid_length[0]
    sensor_density = args.sensor_density[0]

    if args.generate_sensor:
        print('generating sensor')
        GenerateSensors.random(grid_length, sensor_density, random_seed, f'data/sensors-{grid_length}-{sensor_density}')

    if args.generate_data:
        alpha = args.alpha[0]
        std = args.std[0]
        cell_length = args.cell_length[0]
        power = args.power[0]
        cell_percentage = args.cell_percentage[0]

        print('generating data')
        print(random_seed, alpha, std, grid_length, cell_length, sensor_density)
        generatedata = GenerateData(random_seed, alpha, std, grid_length, cell_length, sensor_density)

        gd = GenerateData(random_seed, alpha, std, grid_length, cell_length, sensor_density)
        root_dir = 'data/images-1'
        gd.generate(power, cell_percentage, 2, f'data/sensors/{grid_length}-{sensor_density}', 'data/images_1')