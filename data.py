import random
from collections import defaultdict
from datetime import datetime

from deap_solver_dependency import *


def get_data():
    dummy_data = {
        "test_WOEx": [
            {
                "acKey": "WO1",
                "adDeliveryDeadline": "2023-11-30",
                "acKeyParent": ""
            },
            {
                "acKey": "WO2",
                "adDeliveryDeadline": None,
                "acKeyParent": "WO1"
            },
            {
                "acKey": "WO3",
                "adDeliveryDeadline": None,
                "acKeyParent": ""
            },
            {
                "acKey": "WO4",
                "adDeliveryDeadline": "2023-12-15",
                "acKeyParent": "W03"
            },

        ],
        "test_WOOperations": [
            {
                "acKey": "WO1",
                "anNo": 1,
                "anQty": 600,
                "acResource": "Resource1",
                "acName": "Operation 1"
            },

            {
                "acKey": "WO2",
                "anNo": 1,
                "anQty": 400,
                "acResource": "Resource3",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO3",
                "anNo": 1,
                "anQty": 300,
                "acResource": "Resource3",
                "acName": "Operation 3"
            },
            {
                "acKey": "WO4",
                "anNo": 1,
                "anQty": 400,
                "acResource": "Resource3",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO5",
                "anNo": 1,
                "anQty": 500,
                "acResource": "Resource2",
                "acName": "Operation 2"
            },
            {
                "acKey": "WO6",
                "anNo": 1,
                "anQty": 700,
                "acResource": "Resource4",
                "acName": "Operation 1"
            }
        ]
    }

    return dummy_data


def parse_json_to_production_schedule():
    json_data = get_data()
    # Set company working hours (24/7)
    company_calendar = ProductionCalendar(
        [(8, 12), (13, 17)])

    resource_calendars = {
        "resource1": ProductionCalendar([(8, 12), (13, 17)]),
        "resource2": ProductionCalendar([(9, 12), (13, 18)]),
        "resource3": ProductionCalendar([(8, 12), (13, 16)]),
    }

    jobs = []
    jobs_list = []
    # Parse the data from JSON
    counter = 1
    for record in json_data['test_WOEx']:
        name = record["acKey"]
        parent = record["acKeyParent"]
        # Create job based on the record
        job = {
            'id': counter,
            'name': name,
            'dependency': parent,
            'operations': [],
        }
        counter += 1
        # Add the job to the list of jobs
        jobs.append(job)

    for record in json_data['test_WOOperations']:
        name = record["acKey"]
        no = record['anNo']
        qty = record['anQty']
        resource = record['acResource']
        operation_name = record['acName']
        job = next((job for job in jobs if job.get('name') == name), None)
        if job:
            if not job.get('operations'):
                job['operations'] = {}  # Change operations to a dictionary if it's not set yet

            if resource in job['operations']:
                job['operations'][resource] += float(qty)
            else:
                job['operations'][resource] = float(qty)

    counter = 1
    for job in jobs:
        index_dependency = 0
        for job_inner in jobs:
            if job_inner["name"] == job.get("dependency"):
                index_dependency = job_inner["id"]
        jobs_list.append(UncertainProductionJob(counter, job.get("name"), 1,
                                                3,
                                                job.get("operations"), [] if job.get("dependency") == "" or
                                                                             job.get(
                                                                                 "dependency") is None or index_dependency == 0 else
                                                [index_dependency]))
        counter += 1  # increment the id
    return company_calendar, resource_calendars, jobs_list
