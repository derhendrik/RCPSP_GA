# Genetic Algorithm for the Resource-Constrained Project Scheduling Problem

Python implementation of the Genetic Algorithm proposed by S. Hartmann in the research paper *"A competitive genetic algorithm for the resource-constrained project scheduling"*, see also [here](https://doi.org/10.1002/(SICI)1520-6750(199810)45:7%3C733::AID-NAV5%3E3.0.CO;2-C).
Some adjustments have been made, such as generating the initial population with a roulette-wheel selection based on latest-finish-times of activities (instead of purely random).

Mostly serves as a test bench for personal use or as a starting point for students that work on scheduling problems.

For an extensive introduction to the resource-constrained project scheduling problem, see also here:
- *"Complex Scheduling"* - Brucker & Knust [[Link](https://link.springer.com/book/10.1007/978-3-642-23929-8)]
- *"Project Scheduling - A Research Handbook"* - Demeulemeester & Herroelen [[Link](https://link.springer.com/book/10.1007/b101924)]
- *"Scheduling Algorithms"* - Brucker [[Link](https://link.springer.com/book/10.1007/978-3-540-69516-5)]
- *"Resource-Constrained Project Scheduling: Models, Algorithms, Extensions and Applications"* - Artigues, Demassey and Néron [[Link](https://onlinelibrary.wiley.com/doi/book/10.1002/9780470611227)]

For a more visual introduction, see also this website: [PM Knowledge Center](https://www.pmknowledgecenter.be/dynamic_scheduling/baseline/optimizing-regular-scheduling-objectives-schedule-generation-schemes)

### Installation
Install the modules listed in the `requirements.txt`.

### Code Execution
Run the `driver.py` file. The variable `number_of_threads` may need to be adjusted according to your hardware.