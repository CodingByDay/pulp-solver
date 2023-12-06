import random
import numpy as np
from deap import base, creator, tools, algorithms
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import networkx as nx


class TimeSlot:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class ProductionCalendar:
    def __init__(self, work_periods):
        self.work_periods = [TimeSlot(start, end) for start, end in work_periods]


def evaluate(individual, jobs):
    total_duration = sum(individual)
    idle_time = max(0, max(individual) - total_duration)
    total_utilization = sum([job.actual_duration for job, duration in zip(jobs, individual)])

    # Calculate the total deviation from deadlines
    total_deadline_deviation = 0 #sum([max(0, job.end_time - job.deadline) if job.deadline is not None else 0 for job in jobs])

    return total_duration, -idle_time, total_utilization, total_deadline_deviation



def dynamic_priority(job, current_time):
    # Example of dynamic priority based on urgency (deadline proximity)
    if job.deadline is not None:
        time_to_deadline = max(0, job.deadline - current_time)
        urgency_priority = 1 / (time_to_deadline + 1)  # The closer to the deadline, the higher the urgency
        return urgency_priority
    else:
        return 0


def predict_job_durations(jobs, historical_data):
    # Example: Use a RandomForestRegressor for duration prediction based on historical data
    features = np.array(
        [[job.resource_requirements['resource1'], job.resource_requirements['resource2']] for job in historical_data])
    labels = np.array([job.actual_duration for job in historical_data])

    # Split the data into training and testing sets
    features_train, features_test, labels_train, labels_test = train_test_split(features, labels, test_size=0.2,
                                                                                random_state=42)

    # Train the regression model
    regressor = RandomForestRegressor(n_estimators=100, random_state=42)
    regressor.fit(features_train, labels_train)

    # Predict durations for jobs without historical data
    for job in jobs:
        if job not in historical_data:
            job.min_duration = regressor.predict(
                np.array([[job.resource_requirements['resource1'], job.resource_requirements['resource2']]]))[0]
            job.max_duration = job.min_duration * 1.5  # Adjust for uncertainty


def simulate_resource_availability(resource_calendars, uncertainty_factor=0.2):
    # Simulate uncertainties in resource availability
    for resource, calendar in resource_calendars.items():
        for time_slot in calendar.work_periods:
            if random.uniform(0, 1) < uncertainty_factor:
                # Reduce resource availability during this time slot
                time_slot.end -= random.uniform(0, (time_slot.end - time_slot.start) * 0.5)  # Reduce by up to 50%


def create_dag(jobs):
    # Create a directed acyclic graph (DAG) to represent job dependencies
    dag = nx.DiGraph()
    for job in jobs:
        dag.add_node(job.id, job=job)
        if job.dependencies:
            for dependency_id in job.dependencies:
                dag.add_edge(dependency_id, job.id)
    return dag


def topological_sort(dag):
    # Perform topological sorting of the DAG
    return list(nx.topological_sort(dag))


def check_time_window(job, current_time):
    # Check if the current time is within the job's time window
    return job.time_window[0] <= current_time <= job.time_window[1]


def check_resource_availability(job, resource_calendars, current_time):
    # Check if the required resources are available at the current time
    for resource, calendar in job.resource_requirements.items():
        resource_calendar = resource_calendars[resource]
        for time_slot in resource_calendar.work_periods:
            if time_slot.start <= current_time <= time_slot.end:
                return True
    return False


def find_alternative_resources(job, resource_calendars, current_time):
    # Find alternative resources available at the current time
    alternative_resources = []
    for resource, calendar in resource_calendars.items():
        for time_slot in calendar.work_periods:
            if time_slot.start <= current_time <= time_slot.end and resource not in job.resource_requirements:
                alternative_resources.append(resource)
    return alternative_resources


def create_production_schedule(jobs, company_calendar, resource_calendars, historical_data, uncertainty_factor=0.2):
    # Particle Swarm Optimization parameters
    POPULATION_SIZE = 10
    PARTICLE_SIZE = len(jobs)
    ITERATIONS = 10

    # Create a creator for the individual (schedule)
    creator.create("FitnessMulti", base.Fitness,
                   weights=(1.0, -1.0, -1.0, -1.0))  # Minimize duration, idle time, utilization, and deadline deviation
    creator.create("Particle", list, fitness=creator.FitnessMulti, speed=list, pmin=None, pmax=None, best=None)

    def create_particle():
        particle = creator.Particle()
        particle.extend([random.uniform(0, max([job.max_duration for job in jobs])) for _ in range(PARTICLE_SIZE)])
        particle.speed = [random.uniform(0, 1) for _ in range(PARTICLE_SIZE)]
        particle.pmin = [0] * PARTICLE_SIZE
        particle.pmax = [max([job.max_duration for job in jobs])] * PARTICLE_SIZE
        particle.best = creator.Particle(particle)
        particle.best.fitness.values = toolbox.evaluate(particle)
        return particle

    toolbox = base.Toolbox()
    toolbox.register("particle", create_particle)
    toolbox.register("population", lambda: [toolbox.particle() for _ in range(POPULATION_SIZE)])
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
    toolbox.register("select", tools.selBest)
    toolbox.register("evaluate", evaluate, jobs=jobs)

    # Initialize the particle population
    population = toolbox.population()

    # predict_job_durations(jobs, historical_data)
    # PSO algorithm
    for iteration in range(ITERATIONS):
        # Simulate uncertainties in resource availability for each iteration
        simulate_resource_availability(resource_calendars, uncertainty_factor)

        # Create a directed acyclic graph (DAG) for job dependencies
        dag = create_dag(jobs)

        # Perform topological sorting to determine the order of job scheduling
        sorted_job_ids = topological_sort(dag)

        for job_id in sorted_job_ids:
            job = dag.nodes[job_id]['job']

            # Find the particle index corresponding to the job
            particle_index = jobs.index(job)
            current_time = 0

            # Check if the job can be scheduled at the current time
            if check_time_window(job, current_time) and check_resource_availability(job, resource_calendars,
                                                                                    current_time):
                # Update particle speed and position for the specific job
                for i in range(PARTICLE_SIZE):
                    inertia = 0.5
                    cognitive_weight = 1.5
                    social_weight = 1.5
                    r1, r2 = random.uniform(0, 1), random.uniform(0, 1)

                    # Update speed
                    population[particle_index].speed[i] = inertia * population[particle_index].speed[i] + \
                                                          cognitive_weight * r1 * (population[particle_index].best[i] -
                                                                                   population[particle_index][i]) + \
                                                          social_weight * r2 * (population[particle_index].best[i] -
                                                                                population[particle_index][i])

                    # Update position
                    population[particle_index][i] += population[particle_index].speed[i]

                    # Clip position to the feasible range
                    population[particle_index][i] = max(population[particle_index].pmin[i],
                                                        min(population[particle_index][i],
                                                            population[particle_index].pmax[i]))

                # Evaluate fitness for the specific job
                fitness = toolbox.evaluate(population[particle_index])

                # Update personal best if the current position is better

                compare_to = population[particle_index].best.fitness.values
                if fitness > compare_to:
                    population[particle_index].best = creator.Particle(population[particle_index])
                    population[particle_index].best.fitness.values = fitness

                # Update job start and end times based on the best individual
                job.actual_duration = (job.min_duration + job.max_duration) / 2
                job.start_time = current_time
                job.end_time = current_time + job.actual_duration
                current_time = max(current_time, job.end_time)

            # If the job cannot be scheduled at the current time, try alternative resources
            else:
                alternative_resources = find_alternative_resources(job, resource_calendars, current_time)
                if alternative_resources:
                    # Randomly select an alternative resource
                    selected_resource = random.choice(alternative_resources)
                    job.resource_requirements[selected_resource] = job.resource_requirements.popitem()[0]

    return jobs


# Example usage
if __name__ == "__main__":
    company_calendar = ProductionCalendar(
        [(0, 24)])  # Company works from 8 am to 5 pm with a break from 12 pm to 1 pm

    resource_calendars = {
        "resource1": ProductionCalendar([(0, 24)]),
        "resource2": ProductionCalendar([(0, 24)]),
        "resource3": ProductionCalendar([(0, 24)]),
    }


    class ProductionJob:
        def __init__(self, id, name, duration, resource_requirements, dependencies=None, deadline=None):
            self.id = id
            self.name = name
            self.duration = duration
            self.resource_requirements = resource_requirements
            self.dependencies = dependencies if dependencies else []
            self.deadline = deadline
            self.start_time = None
            self.end_time = None


    class UncertainProductionJob(ProductionJob):
        def __init__(self, id, name, min_duration, max_duration, resource_requirements, dependencies=None,
                     deadline=None, time_window=None, alternative_resources=None):
            super().__init__(id, name, 0, resource_requirements, dependencies, deadline)
            self.min_duration = min_duration
            self.max_duration = max_duration
            self.actual_duration = 0
            self.time_window = time_window  # Time window during which the job can be scheduled
            self.alternative_resources = alternative_resources if alternative_resources else []


    job1 = UncertainProductionJob(1, "Job1", 4, 6, {"resource1": 2, "resource2": 1}, time_window=(0, 24), deadline=15)
    job2 = UncertainProductionJob(2, "Job2", 2, 4, {"resource1": 1, "resource3": 3}, time_window=(0, 24), deadline=20,
                                  alternative_resources=["resource2"])
    job3 = UncertainProductionJob(3, "Job3", 3, 5, {"resource2": 2, "resource3": 1}, dependencies=[1, 2],
                                  time_window=(0, 24), deadline=24)
    job4 = UncertainProductionJob(4, "Job4", 1, 3, {"resource1": 1, "resource2": 1}, time_window=(0, 24),
                                  dependencies=[2], deadline=24)

    jobs = [job1, job2, job3, job4]

    # Historical data for duration prediction (for demonstration purposes)
    historical_data = [

    ]

    scheduled_jobs = create_production_schedule(jobs, company_calendar, resource_calendars, historical_data)

    if scheduled_jobs:
        for job in scheduled_jobs:
            print(
                f"Job {job.name} scheduled from {job.start_time} to {job.end_time} with resources: {job.resource_requirements}, actual duration: {job.actual_duration}, time window: {job.time_window}, alternative resources: {job.alternative_resources}, deadline: {job.deadline}")
