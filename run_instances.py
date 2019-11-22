import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import chain, product
from math import sqrt
from time import perf_counter
from typing import Any, List

import numpy

from local_search import annealing_standalone
from graph import Graph, tuples_to_dict
from reader import read_graph
from solution import solver

FUNCTIONS = [annealing_standalone]
ARGUMENTS = [{}]


def loop(graph: Graph, filename: str, params: Any, func: solver,
         iterations: int) -> List[str]:
    output = []
    for _ in range(iterations):
        start_time = perf_counter()
        solution = func(graph, **params)
        diff = perf_counter() - start_time
        output.append(f'{os.path.basename(filename)}\t{params}\t'
                      f'{solution.colors_count}\t{diff:.5f}')
    return output


def run_instance(filename: str, params: Any, func: solver,
                 total_iterations: int = 100):
    graph = init_graph(filename)
    output = loop(graph, filename, params, func, total_iterations)
    with open(out_filename(filename, func), 'a') as file:
        file.write('\n'.join(output))
        file.write('\n')


def run_instance_multiprocess(filename: str, params: Any, func: solver,
                              total_iterations: int = 100):
    graph = init_graph(filename)

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(loop, graph, filename, params, func,
                                   total_iterations // executor._max_workers)
                   for _ in range(executor._max_workers)]
        output = [f.result() for f in as_completed(futures)]

    with open(out_filename(filename, func), 'a') as file:
        file.write('\n'.join(chain.from_iterable(output)))
        file.write('\n')


def init_graph(filename: str) -> Graph:
    vertices, edges = read_graph(filename)
    vertex_neighbors = tuples_to_dict(vertices, edges)
    return vertex_neighbors


def out_filename(in_filename: str, func: solver):
    basename = '.'.join(os.path.basename(in_filename).split(".")[:-1])

    return f'out/{basename}-{func.__name__}.txt'


def generate_summary():
    output = ['inst\tmin\tmed\tmax\tsd\tvar']

    for filename in filter(
            lambda s: not s.startswith('_') and s.endswith('.txt'),
            os.listdir('out')):

        instance = '-'.join(filename.split('-')[:-1])
        with open(f'out/{filename}') as file:
            values = [int(l.split('\t')[2]) for l in file if l.strip()]
        min_, max_ = min(values), max(values)
        mean = numpy.mean(values)
        var = numpy.var(values)
        sdev = sqrt(var)
        output.append(f'{instance}\t{min_}\t{mean}\t{max_}\t{var}\t{sdev}')

    with open('out/_summary.txt', 'w') as file:
        file.write('\n'.join(output))


def main():
    for filename, (func, args) in product(os.listdir('benchmarks'),
                                          zip(FUNCTIONS, ARGUMENTS)):
        print(filename, func.__name__)
        run_instance_multiprocess(f'benchmarks/{filename}', args, func)
    generate_summary()


if __name__ == '__main__':
    main()
