import GeneticAlgorithm
import os
import multiprocess as mp
import itertools
import timeit

number_of_threads = 8
computation_limit_SGS = 5000

population_sizes = [50, 100, 500]
mutation_rates = [0.1, 0.2]
schedule_generation_schemes = ["serial", "parallel"]
instance_names = ["j301_1.sm", "j301_2.sm"]

configs = list(itertools.product(instance_names, population_sizes, mutation_rates, schedule_generation_schemes))

def run_study(instance_name, population_size, mutation_rate, sgs):
    print("---------- Starting Run -----------")
    print("Solving: " + instance_name)
    print("With parameter settings:")
    print("Population size: " + str(population_size))
    print("Mutation rate: " + str(mutation_rate))
    print("SGS: " + sgs)

    scheduling_project = GeneticAlgorithm.Project()
    instance_filepath = os.path.join(os.getcwd(), "Instances", "j30.sm")
    scheduling_project.read_project(instance_filepath, instance_name)
    if sgs == "serial":
        scheduling_project.solve_instance_via_ga(population_size, int(computation_limit_SGS / population_size),
                                                 mutation_rate, scheduling_project.serial_SGS)
    elif sgs == "parallel":
        scheduling_project.solve_instance_via_ga(population_size, int(computation_limit_SGS / population_size),
                                                 mutation_rate, scheduling_project.parallel_SGS)

    print("---------- Finished Run -----------\n\n")


if __name__ == "__main__":
    start_time = timeit.default_timer()

    pool = mp.Pool(number_of_threads)
    pool.starmap(run_study, configs)

    end_time = timeit.default_timer()

    print('Time: ', end_time - start_time)
