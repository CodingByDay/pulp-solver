import pulp


# Sample data
def pulp_solve(jobs, dependencies):
    # Create a list of resources
    resources = set(job['resource'] for job in jobs.values())
    # Initialize the problem
    problem = pulp.LpProblem("Production Scheduling", pulp.LpMinimize)
    # Define decision variables
    start_times = {job_id: pulp.LpVariable(f"Start_{job_id}", lowBound=0, cat='Continuous') for job_id in jobs}
    # Set objective function (minimize completion time, for example)
    problem += pulp.lpSum([start_times[job_id] + jobs[job_id]['duration'] for job_id in jobs])
    # Add constraints
    for job_id in jobs:
        for dep in dependencies:
            if dep[1] == job_id:
                problem += start_times[dep[0]] + jobs[dep[0]]['duration'] <= start_times[job_id]
    # Resource constraint: jobs on the same level with different resources start at the same time
    for level in set(job['level'] for job in jobs.values()):
        jobs_same_level = [job_id for job_id, job in jobs.items() if job['level'] == level]
        resources_same_level = set(jobs[job_id]['resource'] for job_id in jobs_same_level)
        if len(resources_same_level) > 1:
            for res in resources_same_level:
                jobs_same_res = [job_id for job_id in jobs_same_level if jobs[job_id]['resource'] == res]
                for i in range(1, len(jobs_same_res)):
                    problem += start_times[jobs_same_res[i - 1]] == start_times[jobs_same_res[i]]

    # Solve the problem
    problem.solve()
    if pulp.LpStatus[problem.status] == "Optimal":
        schedule = {}
        for job_id, var in start_times.items():
            job_name = jobs[job_id]['name']
            start_time = var.varValue
            end_time = start_time + jobs[job_id]['duration']
            time_slot = int(start_time / 100)  # Group tasks based on time slots

            task_info = {
                'task_id': job_id,
                'start_time': start_time,
                'end_time': end_time,
                'color': 'blue',
                'resource_id': jobs[job_id]['resource'],
                'level': jobs[job_id]['level'],
                'job_name': job_name
            }

            if time_slot in schedule:
                schedule[time_slot].append(task_info)
            else:
                schedule[time_slot] = [task_info]

        # Sorting the schedule dictionary by keys (time slots)
        formatted_schedule = {slot: schedule[slot] for slot in sorted(schedule.keys())}
        # Returning the formatted_schedule
        return formatted_schedule


# Output the results
"""if pulp.LpStatus[problem.status] == "Optimal":
    for job_id, var in start_times.items():
        job_name = jobs[job_id]['name']
        start_time = var.varValue
        end_time = start_time + jobs[job_id]['duration']
        print(f"{job_name} starts at time {start_time} and ends at time {end_time}")
else:
    print("No optimal solution found.")
    
jobs = {
    1: {'duration': 3, 'resource': 'A', 'level': 1, 'name': 'Job_A'},
    2: {'duration': 2, 'resource': 'B', 'level': 2, 'name': 'Job_B'},
    3: {'duration': 4, 'resource': 'A', 'level': 2, 'name': 'Job_C'},
    4: {'duration': 2, 'resource': 'C', 'level': 2, 'name': 'Job_D'},
    5: {'duration': 5, 'resource': 'A', 'level': 3, 'name': 'Job_E'},
}
# Job dependencies (lower level needs to finish before higher level begins)
dependencies = [
    (1, 2),
    (1, 3),
    (1, 4),
    (2, 5),
    (3, 5),
    (4, 5),
]
    
    
    
    
    """
