import random
import os
import timeit

import matplotlib as plt


class Node(object):

    def __init__(self):
        self.predecessors = []
        self.successors = []

        self.renewable_resource_requirements = []

        self.start_time = None
        self.finish_time = None

        self.duration = None

        self.name = None

        self.est = None
        self.lst = None
        self.eft = None
        self.lft = None

        self.prio_value = None

        self.started = False
        self.finished = False

        self.scheduled = False

    def __repr__(self):
        return str(self.name)


class Project(object):

    def __init__(self):

        self.renewable_resource_availability = []
        self.number_of_jobs = None
        self.number_of_nondummy_jobs = None
        self.number_of_renewable_resources = None
        self.nodes = dict()

        # self.successors = []

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

    def solve_instance(self, pop_size, number_of_generations, mutation_probability):

        population = []

    def serial_SGS(self, individual):
        individual: Individual

        # set prio-values based on activity_list and reset states:
        for node in self.nodes.values():
            node.prio_value = individual.activity_list.index(node)
            node.start_time = None
            node.finish_time = None
            node.started = False
            node.finished = False

        # create resource profile indexed by k and t
        R_kt = [[k] * self.horizon for k in self.renewable_resource_availability]

        scheduled_activities = set()
        starting_node = self.nodes[0]
        starting_node.start_time = 0
        starting_node.finish_time = 0
        starting_node.started = True
        starting_node.finished = True
        starting_node.scheduled = True

        scheduled_activities.add(self.nodes[0])

        eligibles = [succ for succ in self.nodes[0].successors]
        eligibles.sort(key=lambda x: x.prio_value)

        while len(scheduled_activities) != self.number_of_jobs:

            selected_node = eligibles[0]
            t = max([(pred.start_time + pred.duration) for pred in selected_node.predecessors])

            current_t = t

            while not selected_node.scheduled:
                violation = False

                for k in range(self.number_of_renewable_resources):
                    for t_iterator in range(current_t, current_t + selected_node.duration):
                        if selected_node.renewable_resource_requirements[k] > R_kt[k][t_iterator]:
                            violation = True
                            current_t = min([_.finish_time for _ in scheduled_activities if _.finish_time > current_t])
                            break
                    if violation:
                        break

                if not violation:
                    selected_node.scheduled = True

                    selected_node.start_time = current_t
                    selected_node.finish_time = current_t + selected_node.duration
                    selected_node.started = True

                    for k in range(self.number_of_renewable_resources):
                        for t_iterator in range(current_t, current_t + selected_node.duration):
                            R_kt[k][t_iterator] -= selected_node.renewable_resource_requirements[k]

            scheduled_activities.add(selected_node)
            eligibles.remove(selected_node)
            eligibles.extend([_ for _ in selected_node.successors if
                              (_ not in eligibles and all([pred.scheduled for pred in _.predecessors]))])

            eligibles.sort(key=lambda x: x.prio_value)



        print("Checks. Can be Deleted")

        print("Resource Profile: ")
        for k in range(self.number_of_renewable_resources):
            print(R_kt[k])

        print(scheduled_activities)
        print(len(scheduled_activities))

        for node in self.nodes.values():
            print("\n __")
            print("name : " + str(node))

            print(node.start_time)
            print(node.finish_time)
            print(node.renewable_resource_requirements)

    def parallel_SGS(self, individual):
        individual: Individual

        # set prio-values based on activity_list and reset states:
        for node in self.nodes.values():
            node.prio_value = individual.activity_list.index(node)
            node.start_time = None
            node.finish_time = None
            node.started = False
            node.finished = False

        # create resource profile indexed by k and t
        R_kt = [[k] * self.horizon for k in self.renewable_resource_availability]


        actives = []
        eligibles = [self.nodes[0]]
        scheduled_activities = set()

        while len(scheduled_activities) != self.number_of_jobs:
            while eligibles:
                selected_node = eligibles[0]








        scheduled_activities = set()
        starting_node = self.nodes[0]
        starting_node.start_time = 0
        starting_node.finish_time = 0
        starting_node.started = True
        starting_node.finished = True
        starting_node.scheduled = True

        scheduled_activities.add(self.nodes[0])

        eligibles = [succ for succ in self.nodes[0].successors]
        eligibles.sort(key=lambda x: x.prio_value)








class Individual(object):

    def __init__(self):
        self.fitness = float('inf')
        self.activity_list = []
        self.start_times = dict()
        self.finish_times = dict()

    def restore_precedence_of_activity_list(self):
        pass

    def check_precedence_of_activity_list(self):
        pass


if __name__ == "__main__":
    my_test_project = Project()
    instance_filepath = os.path.join(os.getcwd(), "Instances", "j30.sm")

    my_test_project.read_project(instance_filepath, "j301_1.sm")
    indiv = Individual()
    indiv.activity_list = [_ for _ in my_test_project.nodes.values()]

    my_test_project.serial_SGS(indiv)
    print("finished")
