import tkinter as tk
from tkinter import Canvas, Frame
from tkinter import simpledialog
from pulp_solver import *
from deap_solver import *
import json
from tkinter import ttk


def show_dialog():
    result = simpledialog.askstring("Input", "Enter your name:")
    if result:
        print("Hello,", result)


# Function to handle the drag-and-drop functionality
def on_drag_start(event, task):
    widget = event.widget
    widget.startX = event.x
    widget.startY = event.y
    widget.task = task


def create_toolbar(root):
    toolbar = ttk.Frame(root)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    algo_menu = ttk.Combobox(toolbar, values=["DEAP", "PULP"])
    algo_menu.set("Select Algorithm")
    algo_menu.pack(side=tk.LEFT, padx=10)

    run_button = ttk.Button(toolbar, text="Run", command=lambda: run_algorithm_and_update_gui(algo_menu.get()))
    run_button.pack(side=tk.LEFT, padx=5)

    # Add more options/buttons as needed

    return toolbar


def on_drag_motion(event):
    widget = event.widget
    deltax = event.x - widget.startX
    deltay = event.y - widget.startY
    widget.move(widget.task, deltax, deltay)
    widget.startX = event.x
    widget.startY = event.y


def transform_to_schedule(tasks):
    schedule = {}
    for task in tasks.values():
        for t in task:
            resource_id = t['resource_id']
            if resource_id not in schedule:
                schedule[resource_id] = []
            schedule[resource_id].append(t)
    return schedule


def convert_to_task_structure(jobs):
    task_structure = {}
    task_id = 0

    for job in jobs:
        if job.id not in task_structure:
            task_structure[job.id] = []

        task_structure[job.id].append({
            'task_id': job.id,
            'start_time': job.start_time if job.start_time else 0.0,
            'end_time': job.end_time if job.end_time else 0.0,
            'color': 'blue',
            'resource_id': next(iter(job.resource_requirements)),
            'level': job.level,
            'job_name': job.name
        })
    return task_structure


def create_gantt_chart(schedule):
    root = tk.Tk()
    root.title("Production planning.")
    toolbar = create_toolbar(root)
    canvas_width = 800
    canvas_height = 1000

    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
    canvas.pack()

    y = 50  # Initial y position



    for resource_id, tasks in schedule.items():
        # Draw horizontal line as a divider between resource timelines
        canvas.create_line(0, y, canvas_width, y, fill='black')

        # Label for the resource
        canvas.create_text(10, y - 20, text=f"Resource: {resource_id}", anchor=tk.W, fill='black')

        # Separation box for each resource's tasks
        start_x = float('inf')
        end_x = float('-inf')
        start_y = y

        for task in tasks:
            start_time = task['start_time'] * 50
            end_time = task['end_time'] * 50

            # Update the box dimensions
            if start_time < start_x:
                start_x = start_time
            if end_time > end_x:
                end_x = end_time

            # Draw rectangles representing tasks on each resource's timeline
            canvas.create_rectangle(start_time, y, end_time, y + 40, fill=task['color'], outline='black')
            canvas.create_text(start_time + 2, y + 20, text=task['job_name'], anchor=tk.W, fill='black')

            y += 50  # Move to the next line for the next task

        # Enclose tasks of each resource within a box
        canvas.create_rectangle(start_x, start_y, end_x, y + 40, outline='black')

        y += 50  # Space between different resources

    root.mainloop()


def run_algorithm_and_update_gui(algorithm):
    # Run your production planning algorithm here and get the schedule
    # Replace this with the actual function call and schedule retrieval based on your algorithm
    if algorithm == "DEAP":
        schedule = get_production_schedule_deap()
        create_gantt_chart(convert_to_task_structure(schedule))

    elif algorithm == "PULP":

        schedule = get_production_schedule_pulp()
        create_gantt_chart(transform_to_schedule(schedule))


def get_production_schedule_deap():
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
    return scheduled_jobs


def get_production_schedule_pulp():
    # Replace this function with the call to your production planning algorithm
    # Return the schedule generated by your algorithm
    jobs = {
        1: {'duration': 3, 'resource': 'A', 'level': 1, 'name': 'Job_A'},
        2: {'duration': 2, 'resource': 'B', 'level': 2, 'name': 'Job_B'},
        3: {'duration': 4, 'resource': 'B', 'level': 2, 'name': 'Job_C'},
        4: {'duration': 5, 'resource': 'C', 'level': 2, 'name': 'Job_D'},
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
    data = {
        'jobs': jobs,
        'dependencies': dependencies
    }

    json_data = json.dumps(data, indent=4)

    schedule = pulp_solve(jobs, dependencies)
    tasks_by_resource = {}
    for slot, tasks in schedule.items():
        for task in tasks:
            resource_id = task['resource_id']
            if resource_id not in tasks_by_resource:
                tasks_by_resource[resource_id] = []
            tasks_by_resource[resource_id].append(task)

    # Ensure non-overlapping schedules for tasks sharing the same resource
    for resource, tasks in tasks_by_resource.items():
        tasks.sort(key=lambda x: x['start_time'])  # Sort tasks by start time
        for i in range(len(tasks) - 1):
            current_task = tasks[i]
            next_task = tasks[i + 1]
            if current_task['end_time'] > next_task['start_time']:
                # Resolve conflict by adjusting the start time of next task
                new_start_time = current_task['end_time']
                tasks[i + 1]['start_time'] = new_start_time
                tasks[i + 1]['end_time'] = new_start_time + (tasks[i + 1]['end_time'] - tasks[i + 1]['start_time'])

    # Updated schedule after resolving conflicts
    updated_schedule = {}
    for slot, tasks in schedule.items():
        updated_schedule[slot] = tasks

    return schedule


# Running the application

if __name__ == "__main__":
    run_algorithm_and_update_gui("PULP")
