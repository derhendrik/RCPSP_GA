import random
import os
import timeit

#from matplotlib import pyplot as plt

#plt.rcParams["figure.figsize"] = (16, 11)


class Node(object):

    def __init__(self):
        self.predecessors = []
        self.successors = []

        self.renewable_resource_requirements = []

        self.start_time = None
        self.finish_time = None

        self.duration = None

        self.name = None

        self.es = None
        self.ls = None
        self.ef = None
        self.lf = None

        self.prio_value = None

        self.started = False
        self.finished = False

        self.scheduled = False

        self.selection_probability = None

    def __repr__(self):
        return str(self.name)


class Project(object):

    def __init__(self):

        self.renewable_resource_availability = []
        self.number_of_jobs = None
        self.number_of_nondummy_jobs = None
        self.number_of_renewable_resources = None
        self.nodes = dict()

        self.horizon = None
        self.population = []

    def read_project(self, instance_filepath, instance_name):

        full_path = os.path.join(instance_filepath, instance_name)

        with open(full_path, "r") as file:
            file = list(file)
            for line_index, line in enumerate(file):
                if "projects" in line:
                    # Get number of jobs
                    dummy = file[line_index + 1].split(" ")
                    self.number_of_jobs = int(dummy[-1])
                    self.number_of_nondummy_jobs = self.number_of_jobs - 2

                    # Get horizon
                    dummy = file[line_index + 2].split(" ")
                    self.horizon = int(dummy[-1])

                    # Get number of renewable resources
                    dummy = file[line_index + 4].split(" ")
                    self.number_of_renewable_resources = int(dummy[-4])

                    # Create nodes and store in dictionary 'nodes'
                    for i in range(self.number_of_jobs):
                        dummy = Node()
                        dummy.name = i
                        self.nodes[i] = dummy

                elif "PRECEDENCE RELATIONS:" in line:

                    starting_line_index = line_index + 2

                    for i in range(self.number_of_jobs):
                        dummy = file[starting_line_index + i]
                        dummy = dummy.rstrip()
                        dummy = dummy.split(" ")
                        dummy = list(filter(None, dummy))
                        dummy = [int(entry) for entry in dummy]

                        number_of_successors = dummy[2]
                        for j in range(number_of_successors):
                            # careful: here offset needed due to renaming of nodes: Starting from 0 -> n+1
                            successor_node_name = dummy[3 + j] - 1
                            self.nodes[i].successors.append(self.nodes[successor_node_name])

                    for node in self.nodes.values():
                        for succ in node.successors:
                            succ.predecessors.append(node)

                    for node in self.nodes.values():
                        node.predecessors = list(set(node.predecessors))

                elif "REQUESTS/DURATIONS:" in line:

                    starting_line_index = line_index + 3

                    for i in range(self.number_of_jobs):
                        dummy = file[starting_line_index + i]
                        dummy = dummy.rstrip()
                        dummy = dummy.split(" ")
                        dummy = list(filter(None, dummy))
                        dummy = [int(entry) for entry in dummy]

                        self.nodes[i].duration = dummy[2]
                        for k in range(self.number_of_renewable_resources):
                            self.nodes[i].renewable_resource_requirements.append(int(dummy[3 + k]))

                elif "RESOURCEAVAILABILITIES:" in line:

                    starting_line_index = line_index + 2

                    dummy = file[starting_line_index]
                    dummy = dummy.rstrip()
                    dummy = dummy.split(" ")
                    dummy = list(filter(None, dummy))
                    dummy = [int(entry) for entry in dummy]

                    for availability in dummy:
                        self.renewable_resource_availability.append(availability)

    def solve_instance_via_ga(self, pop_size, number_of_generations, mutation_probability, sgs):

        incumbent = Individual()

        population = self.create_initial_population(pop_size)

        for indiv in population:
            sgs(indiv)

        for gen in range(number_of_generations):
            # print("gen: " + str(gen))
            # print("incumbent fitness: " + str(incumbent.fitness))
            # print("--")

            offsprings = self.crossover(population)
            offsprings = self.mutate(offsprings, mutation_probability)

            population, incumbent = self.rank_and_reduce(population, offsprings, incumbent, sgs)

        print("finished GA with fitness of: " + str(incumbent.fitness))

    def create_initial_population(self, pop_size):

        self.forward_backward_scheduling()

        population = []

        # add one pure MIN-LFT-rule individual, can be extended by further priority rules if desired

        dummy = Individual()
        nodes_sorted_by_min_lft = list(self.nodes.values())
        nodes_sorted_by_min_lft.sort(key=lambda x: x.lf)

        dummy.activity_list = nodes_sorted_by_min_lft
        population.append(dummy)

        # Sampling Procedure based on min lft:
        for i in range(1, pop_size):
            dummy = Individual()

            unselected_nodes = list(self.nodes.values())
            selected_nodes = []

            starting_node = unselected_nodes[0]
            selected_nodes.append(starting_node)
            unselected_nodes.remove(starting_node)

            while unselected_nodes:
                possibles = []
                for node in unselected_nodes:
                    if all([predecessor in selected_nodes for predecessor in node.predecessors]):
                        possibles.append(node)

                max_lft = max([_.lf for _ in possibles])
                total = sum([(max_lft - _.lf + 1) for _ in possibles])

                for node in possibles:
                    node.selection_probability = (max_lft - node.lf + 1) / total

                selected_node = random.choices(possibles, [_.selection_probability for _ in possibles])[0]

                selected_nodes.append(selected_node)
                unselected_nodes.remove(selected_node)

            dummy.activity_list = selected_nodes
            population.append(dummy)

        # Also an idea: Do not base selection solely on MIN-LFT priority rule, but instead add more random selection.

        return population

    def forward_backward_scheduling(self):

        # forward pass:
        self.nodes[0].es = 0
        self.nodes[0].ef = 0

        for node in self.nodes.values():
            if node == self.nodes[0]:
                continue
            node.es = max([_.ef for _ in node.predecessors])
            node.ef = node.es + node.duration

        # backward pass:
        finish_node = self.nodes[self.number_of_jobs - 1]
        finish_node.lf = self.horizon
        finish_node.ls = self.horizon

        nodes = list(self.nodes.values())
        nodes.reverse()

        for node in nodes:
            if node == finish_node:
                continue
            node.lf = min([_.ls for _ in node.successors])
            node.ls = node.lf - node.duration

        return None

    def crossover(self, population):

        random.shuffle(population)
        mothers = population[:int(len(population) / 2)]
        fathers = population[int(len(population) / 2):]

        q = random.randint(1, self.number_of_nondummy_jobs - 1)

        offsprings = []

        for mother, father in zip(mothers, fathers):
            # create daughter:
            daughter = Individual()
            mother_input = mother.activity_list[:q]
            father_input = [_ for _ in father.activity_list if _ not in mother_input]
            daughter.activity_list = mother_input + father_input
            offsprings.append(daughter)

            # create son:
            son = Individual()
            father_input = father.activity_list[:q]
            mother_input = [_ for _ in mother.activity_list if _ not in father_input]
            son.activity_list = father_input + mother_input
            offsprings.append(son)

        return offsprings

    def mutate(self, offsprings, mutation_probability):

        indiv: Individual
        for indiv in offsprings:
            for index, activity in enumerate(indiv.activity_list[:-1]):
                if random.random() < mutation_probability:
                    store_current_activity_list = indiv.activity_list[:]
                    indiv.activity_list[index + 1], indiv.activity_list[index] = indiv.activity_list[index], \
                                                                                 indiv.activity_list[index + 1]
                    if not indiv.check_precedence_feasibility():
                        indiv.activity_list = store_current_activity_list

        return offsprings

    def rank_and_reduce(self, population, offsprings, incumbent, sgs):

        for indiv in offsprings:
            sgs(indiv)

        new_population = population + offsprings
        new_population.sort(key=lambda x: x.fitness)

        new_population = new_population[:len(population)]

        if new_population[0].fitness < incumbent.fitness:
            incumbent = new_population[0]

        return new_population, incumbent

    def serial_SGS(self, individual, debug=False):

        individual: Individual

        # set prio-values based on activity_list and reset states:
        for node in self.nodes.values():
            node.prio_value = individual.activity_list.index(node)
            node.start_time = None
            node.finish_time = None
            node.started = False
            node.finished = False
            node.scheduled = False

        # create resource profile indexed by k and t
        R_kt = [[k] * self.horizon for k in self.renewable_resource_availability]

        scheduled_activities = set()
        starting_node = self.nodes[0]
        starting_node.start_time = 0
        starting_node.finish_time = 0
        starting_node.started = True
        starting_node.finished = True
        starting_node.scheduled = True

        scheduled_activities.add(starting_node)

        eligibles = [succ for succ in starting_node.successors]
        eligibles.sort(key=lambda x: x.prio_value)

        resource_profile_changes = [0]

        while len(scheduled_activities) != self.number_of_jobs:

            selected_node: Node = eligibles[0]
            current_t = max([(pred.start_time + pred.duration) for pred in selected_node.predecessors])

            while not selected_node.scheduled:
                violation = False

                for k in range(self.number_of_renewable_resources):
                    for t_iterator in range(current_t, current_t + selected_node.duration):
                        if selected_node.renewable_resource_requirements[k] > R_kt[k][t_iterator]:
                            violation = True

                            current_t = min(
                                [resource_profile_change for resource_profile_change in resource_profile_changes if
                                 resource_profile_change > current_t])

                            break
                    if violation:
                        break

                if not violation:
                    selected_node.scheduled = True
                    selected_node.start_time = current_t
                    selected_node.finish_time = current_t + selected_node.duration
                    selected_node.started = True
                    selected_node.finished = True

                    resource_profile_changes = []

                    for k in range(self.number_of_renewable_resources):
                        for t_iterator in range(current_t, current_t + selected_node.duration):
                            R_kt[k][t_iterator] -= selected_node.renewable_resource_requirements[k]

                        resource_profile_changes.extend(
                            [i + 1 for i, value in enumerate(R_kt[k][1:]) if (R_kt[k][i] < value)])

                    resource_profile_changes = list(set(resource_profile_changes))

            scheduled_activities.add(selected_node)
            eligibles.remove(selected_node)
            eligibles.extend([_ for _ in selected_node.successors if
                              (_ not in eligibles and all([pred.scheduled for pred in _.predecessors]))])

            eligibles.sort(key=lambda x: x.prio_value)

        individual.fitness = max([_.finish_time for _ in scheduled_activities])

        ### All following checks can be deleted ###

        if debug:

            latest_finish = max([_.finish_time for _ in scheduled_activities])
            print(latest_finish)
            print("Printing of checks. Can be Deleted")
            print(resource_profile_changes)

            print("Resource Profile: ")
            for k in range(self.number_of_renewable_resources):
                res_profile = R_kt[k][:latest_finish + 1]
                print(res_profile)
                plt.step(range(latest_finish + 1), res_profile, where='post')
                plt.xticks(range(latest_finish + 1))
                plt.axvline(latest_finish, color='green', alpha=0.5)
                plt.grid()
                plt.show()

            print("All scheduled?")
            print(all([_ in scheduled_activities for _ in self.nodes.values()]))

            print("finish times")
            print([_.finish_time for _ in self.nodes.values()])
            for node in self.nodes.values():
                print("\n __")
                print("name : " + str(node))

                print(node.start_time)
                print(node.finish_time)
                print(node.renewable_resource_requirements)

    def parallel_SGS(self, individual, debug=False):

        individual: Individual

        # set prio-values based on activity_list and reset states:
        for node in self.nodes.values():
            node.prio_value = individual.activity_list.index(node)
            node.start_time = None
            node.finish_time = None
            node.started = False
            node.finished = False
            node.scheduled = False

        # create resource profile indexed by k and t
        R_kt = [[k] * self.horizon for k in self.renewable_resource_availability]

        actives = set()
        eligibles = [self.nodes[0]]
        scheduled_activities = set()

        current_t = 0
        resource_profile_changes = []

        while len(scheduled_activities) != self.number_of_jobs:

            started_nodes_in_iteration = set()

            while eligibles:
                # print(eligibles)

                selected_node: Node = eligibles[0]

                selected_node.scheduled = True
                selected_node.start_time = current_t
                selected_node.finish_time = current_t + selected_node.duration
                selected_node.started = True
                # selected_node.finished = True

                for k in range(self.number_of_renewable_resources):
                    for t_iterator in range(current_t, current_t + selected_node.duration):
                        R_kt[k][t_iterator] -= selected_node.renewable_resource_requirements[k]
                    resource_profile_changes.extend(
                        [i + 1 for i, value in enumerate(R_kt[k][1:]) if (R_kt[k][i] < value)])

                actives.add(selected_node)
                eligibles.remove(selected_node)
                scheduled_activities.add(selected_node)
                started_nodes_in_iteration.add(selected_node)

                for eligible in eligibles[:]:
                    violation = False

                    for k in range(self.number_of_renewable_resources):
                        for t_iterator in range(current_t, current_t + eligible.duration):
                            if eligible.renewable_resource_requirements[k] > R_kt[k][t_iterator]:
                                violation = True
                                eligibles.remove(eligible)
                                break
                        if violation:
                            break

            resource_profile_changes = [resource_profile_change for resource_profile_change in resource_profile_changes
                                        if resource_profile_change > current_t]
            finish_of_actives = [n.start_time + n.duration for n in actives]

            current_t = min(resource_profile_changes + finish_of_actives)

            eligibles = []
            for node in scheduled_activities:
                eligibles.extend(node.successors)

            eligibles = list(set(eligibles))
            eligibles = [_ for _ in eligibles if _ not in scheduled_activities]
            eligibles = [_ for _ in eligibles if (all([pred.scheduled for pred in _.predecessors]))]

            eligibles = [_ for _ in eligibles if (all([pred.finish_time <= current_t for pred in _.predecessors]))]

            for eligible in eligibles[:]:
                violation = False

                for k in range(self.number_of_renewable_resources):
                    for t_iterator in range(current_t, current_t + eligible.duration):
                        if eligible.renewable_resource_requirements[k] > R_kt[k][t_iterator]:
                            violation = True
                            eligibles.remove(eligible)
                            break
                    if violation:
                        break

            eligibles.sort(key=lambda x: x.prio_value)

            actives.clear()
            actives.update([_ for _ in scheduled_activities if (_.start_time <= current_t < _.finish_time)])

        individual.fitness = max([_.finish_time for _ in scheduled_activities])

        ### All following checks can be deleted ###
        if debug:
            latest_finish = max([_.finish_time for _ in scheduled_activities])
            print(latest_finish)
            print("Printing of checks. Can be Deleted")
            print(resource_profile_changes)

            print("Resource Profile: ")
            for k in range(self.number_of_renewable_resources):
                res_profile = R_kt[k][:latest_finish + 1]
                print(res_profile)
                plt.step(range(latest_finish + 1), res_profile, where='post')
                plt.xticks(range(latest_finish + 1))
                plt.axvline(latest_finish, color='green', alpha=0.5)
                plt.grid()
                plt.show()

            print("All scheduled?")
            print(all([_ in scheduled_activities for _ in self.nodes.values()]))

            print("finish times")
            print([_.finish_time for _ in self.nodes.values()])
            for node in self.nodes.values():
                print("\n __")
                print("name : " + str(node))

                print(node.start_time)
                print(node.finish_time)
                print(node.renewable_resource_requirements)


class Individual(object):

    def __init__(self):
        self.fitness = float('inf')
        self.activity_list = []
        self.start_times = dict()
        self.finish_times = dict()

    def restore_precedence_of_activity_list(self):
        pass

    def check_precedence_feasibility(self):

        violation = False

        for node in self.activity_list:
            if all([self.activity_list.index(pred) < self.activity_list.index(node) for pred in node.predecessors]):
                continue
            else:
                violation = True

        return not violation


if __name__ == "__main__":
    start_time = timeit.default_timer()

    my_test_project = Project()
    instance_filepath = os.path.join(os.getcwd(), "Instances", "j30.sm")

    # my_test_project.read_project(instance_filepath, "test.sm")
    my_test_project.read_project(instance_filepath, "j3045_1.sm")

    my_test_project.solve_instance_via_ga(100, 50, 0.05, my_test_project.serial_SGS)

    end_time = timeit.default_timer()
    run_time = end_time - start_time

    print("finished in seconds: " + str(run_time))
