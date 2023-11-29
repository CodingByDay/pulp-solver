import pulp

# Sample data
jobs = {
    1: {'duration': 20, 'resource': 'A', 'level': 1, 'name': 'Job_A'},
    2: {'duration': 30, 'resource': 'B', 'level': 2, 'name': 'Job_B'},
    3: {'duration': 30, 'resource': 'B', 'level': 2, 'name': 'Job_C'},
    4: {'duration': 30, 'resource': 'C', 'level': 2, 'name': 'Job_D'},
    5: {'duration': 30, 'resource': 'A', 'level': 3, 'name': 'Job_E'},
    # Add more jobs as needed
}

# Job dependencies
dependencies = [
    (1, 2),
    (1, 3),
    (1, 4),
    (2, 5),
    (3, 5),
    (4, 5),
    # Add more dependencies as needed
]

# Create a list of resources
resources = set(job['resource'] for job in jobs.values())

# Initialize the problem
problem = pulp.LpProblem("Production Scheduling", pulp.LpMinimize)

# Define decision variables
start_times = {job_id: pulp.LpVariable(f"Start_{job_id}", lowBound=0, cat='Continuous') for job_id in jobs}

# Binary variables to indicate resource usage at each time slot for each resource
resource_usage = {res: {job_id: pulp.LpVariable(f"Resource_{res}_{job_id}", cat='Binary') for job_id in jobs if jobs[job_id]['resource'] == res} for res in resources}

# Set objective function
problem += pulp.lpSum([start_times[job_id] + jobs[job_id]['duration'] for job_id in jobs])

# Add constraints
for job_id in jobs:
    for dep in dependencies:
        if dep[1] == job_id:
            problem += start_times[dep[0]] + jobs[dep[0]]['duration'] <= start_times[job_id]

# Resource constraint: jobs with the same resource cannot happen at the same time
for res, jobs_same_res in resource_usage.items():
    for job_id_i, var_i in jobs_same_res.items():
        for job_id_j, var_j in jobs_same_res.items():
            if job_id_i != job_id_j:
                problem += start_times[job_id_i] + jobs[job_id_i]['duration'] <= start_times[job_id_j] + (1 - var_i) * 10000
                problem += start_times[job_id_j] + jobs[job_id_j]['duration'] <= start_times[job_id_i] + (1 - var_j) * 10000

# Solve the problem
problem.solve()

# Output the results
if pulp.LpStatus[problem.status] == "Optimal":
    schedule = {}
    for job_id, var in start_times.items():
        job_name = jobs[job_id]['name']
        start_time = var.varValue
        end_time = start_time + jobs[job_id]['duration']
        time_slot = int(start_time / 100)  # Group tasks based on time slots
        task_info = {'task_id': job_id, 'start_time': start_time, 'end_time': end_time, 'color': 'blue'}
        if time_slot in schedule:
            schedule[time_slot].append(task_info)
        else:
            schedule[time_slot] = [task_info]
    formatted_schedule = {slot: schedule[slot] for slot in sorted(schedule.keys())}
    print(formatted_schedule)
else:
    print("No optimal solution found.")
