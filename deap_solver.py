import random
import numpy as np
from deap import base, creator, tools, algorithms


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


class TimeSlot:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class ProductionCalendar:
    def __init__(self, work_periods):
        self.work_periods = [TimeSlot(start, end) for start, end in work_periods]


def evaluate(individual, jobs):
    valid_jobs = [job for job in jobs if job.end_time is not None and job.deadline is not None]

    # Calculate the total duration of the schedule
    total_duration = sum(individual)

    # Calculate the total idle time in the schedule
    idle_time = max(0, max(individual) - total_duration)

    # Calculate the total resource utilization
    total_utilization = sum([job.actual_duration for job, duration in zip(jobs, individual)])

    # Calculate the total deviation from deadlines for jobs with valid deadlines and end times
    total_deadline_deviation = sum([max(0, job.end_time - job.deadline) for job in valid_jobs])

    # Return a tuple of the multiple objectives
    return total_duration, -idle_time, total_utilization, total_deadline_deviation


def dynamic_priority(job, current_time):
    # Example of dynamic priority based on urgency (deadline proximity)
    if job.deadline is not None:
        time_to_deadline = max(0, job.deadline - current_time)
        urgency_priority = 1 / (time_to_deadline + 1)  # The closer to the deadline, the higher the urgency
        return urgency_priority
    else:
        return 0


def create_production_schedule(jobs, company_calendar, resource_calendars):
    # Particle Swarm Optimization parameters
    POPULATION_SIZE = 10
    PARTICLE_SIZE = len(jobs)
    ITERATIONS = 10

    # Create a creator for the individual (schedule)
    creator.create("FitnessMulti", base.Fitness,
                   weights=(1.0, -1.0, -1.0, -1.0))  # Minimize duration, idle time, utilization, and deadline deviation
    creator.create("Particle", list, fitness=creator.FitnessMulti, speed=list, pmin=None, pmax=None, best=None)

    # Create a toolbox for the PSO algorithm
    toolbox = base.Toolbox()
    toolbox.register("particle", tools.initRepeat, creator.Particle,
                     lambda: random.uniform(0, max(job.max_duration for job in jobs)), n=PARTICLE_SIZE)
    toolbox.register("population", tools.initRepeat, list, toolbox.particle)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
    toolbox.register("select", tools.selBest)
    toolbox.register("evaluate", evaluate, jobs=jobs)

    current_time = 0
    jobs.sort(key=lambda job: dynamic_priority(job, current_time), reverse=True)

    # Sort jobs based on level (lower level first)
    jobs.sort(key=lambda job: job.level)

    # Group jobs by level
    grouped_jobs = {}
    for job in jobs:
        grouped_jobs.setdefault(job.level, []).append(job)
    # Initialize the particle population
    population = toolbox.population(n=POPULATION_SIZE)

    # Initialize particle attributes (speed, pmin, pmax, best)
    for particle in population:
        particle.speed = [random.uniform(-1, 1) for _ in range(PARTICLE_SIZE)]
        particle.pmin = [0] * PARTICLE_SIZE
        particle.pmax = [max([job.max_duration for job in jobs])] * PARTICLE_SIZE
        particle.best = particle

    # PSO algorithm
    for iteration in range(ITERATIONS):
        for particle in population:
            # Update particle speed and position
            for i in range(PARTICLE_SIZE):
                inertia = 0.5
                cognitive_weight = 1.5
                social_weight = 1.5
                r1, r2 = random.uniform(0, 1), random.uniform(0, 1)

                # Update speed
                particle.speed[i] = inertia * particle.speed[i] + \
                                    cognitive_weight * r1 * (particle.best[i] - particle[i]) + \
                                    social_weight * r2 * (particle.best[i] - particle[i])

                # Update position
                particle[i] += particle.speed[i]

                # Clip position to the feasible range
                particle[i] = max(particle.pmin[i], min(particle[i], particle.pmax[i]))

            # Evaluate fitness
            fitness = toolbox.evaluate(particle)

            # Update personal best if the current position is better
            if fitness > particle.best.fitness.values:
                particle.best = creator.Particle(particle)
                particle.best.fitness.values = fitness

    # Select the best individual from the final population
    best_particle = tools.selBest(population, k=1)[0]

    # Update job start and end times based on the best individual
    current_time = 0
    for level, level_jobs in grouped_jobs.items():
        # Filter jobs on the same level that don't use the same resource and have no dependencies
        same_time_jobs = []
        used_resources = set()
        for job in level_jobs:
            resource_key = frozenset(job.resource_requirements.items())  # Convert dict to frozenset for hashing
            if job.dependencies or resource_key in used_resources:
                same_time_jobs.append(job)  # If job has dependencies or uses the same resource, add it to the list
            else:
                same_time_jobs.append(job)
                used_resources.add(resource_key)

        # Update start and end times for jobs that can run simultaneously
        max_start_time = 0  # Track the maximum start time for jobs on the same level
        for job in same_time_jobs:
            if not job.dependencies:
                job.actual_duration = (job.min_duration + job.max_duration) / 2
                job.start_time = current_time if job.start_time is None else job.start_time
                job.end_time = job.start_time + job.actual_duration
                max_start_time = max(max_start_time, job.end_time)  # Update the maximum start time

        # Update current_time based on the maximum start time of jobs on the same level
        current_time = max(max_start_time, current_time)

    return jobs


class UncertainProductionJob(ProductionJob):
    def __init__(self, id, name, level, min_duration, max_duration, resource_requirements, dependencies=None,
                 deadline=None, time_window=None, alternative_resources=None):
        super().__init__(id, name, 0, resource_requirements, dependencies, deadline)
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.actual_duration = 0
        self.time_window = time_window  # Time window during which the job can be scheduled
        self.alternative_resources = alternative_resources if alternative_resources else []
        self.level = level






# Example usage
if __name__ == "__main__":
    company_calendar = ProductionCalendar(
        [(8, 12), (13, 17)])  # Company works from 8 am to 5 pm with a break from 12 pm to 1 pm

    resource_calendars = {
        "resource1": ProductionCalendar([(8, 12), (13, 17)]),
        "resource2": ProductionCalendar([(9, 12), (13, 18)]),
        "resource3": ProductionCalendar([(8, 12), (13, 16)]),
    }

    job1 = UncertainProductionJob(1, "Job1", 2, 4, 6, {"resource1": 1}, time_window=(8, 12), deadline=15)
    job2 = UncertainProductionJob(2, "Job2", 1, 2, 4, {"resource1": 1}, deadline=20,
                                  alternative_resources=["resource2"])
    job3 = UncertainProductionJob(3, "Job3", 1, 3, 5, {"resource1": 1}, time_window=(13, 16))
    job4 = UncertainProductionJob(4, "Job4", 2, 1, 3, {"resource1": 1}, )

    jobs = [job1, job2, job3, job4]

    # Sort jobs based on dynamic priorities
    current_time = 0
    jobs.sort(key=lambda job: dynamic_priority(job, current_time), reverse=True)

    scheduled_jobs = create_production_schedule(jobs, company_calendar, resource_calendars)

    if scheduled_jobs:
        for job in scheduled_jobs:
            print(
                f"Job {job.name} scheduled from {job.start_time} to {job.end_time} with resources: {job.resource_requirements}, actual duration: {job.actual_duration}, time window: {job.time_window}, alternative resources: {job.alternative_resources}, deadline: {job.deadline}")