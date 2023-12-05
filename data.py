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
                "acKeyParent": "WO1"
            },
            {
                "acKey": "WO4",
                "adDeliveryDeadline": "2023-12-15",
                "acKeyParent": ""
            },
            {
                "acKey": "WO5",
                "adDeliveryDeadline": None,
                "acKeyParent": "WO4"
            },
            {
                "acKey": "WO6",
                "adDeliveryDeadline": None,
                "acKeyParent": "WO4"
            }
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
                "acKey": "WO1",
                "anNo": 2,
                "anQty": 450,
                "acResource": "Resource2",
                "acName": "Operation 2"
            },
            {
                "acKey": "WO1",
                "anNo": 3,
                "anQty": 300,
                "acResource": "Resource1",
                "acName": "Operation 3"
            },
            {
                "acKey": "WO2",
                "anNo": 1,
                "anQty": 400,
                "acResource": "Resource3",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO2",
                "anNo": 2,
                "anQty": 500,
                "acResource": "Resource2",
                "acName": "Operation 2"
            },
            {
                "acKey": "WO2",
                "anNo": 3,
                "anQty": 700,
                "acResource": "Resource4",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO2",
                "anNo": 4,
                "anQty": 600,
                "acResource": "Resource1",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO2",
                "anNo": 5,
                "anQty": 450,
                "acResource": "Resource2",
                "acName": "Operation 2"
            },
            {
                "acKey": "WO3",
                "anNo": 1,
                "anQty": 300,
                "acResource": "Resource1",
                "acName": "Operation 3"
            },
            {
                "acKey": "WO3",
                "anNo": 2,
                "anQty": 400,
                "acResource": "Resource3",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO3",
                "anNo": 3,
                "anQty": 500,
                "acResource": "Resource2",
                "acName": "Operation 2"
            },
            {
                "acKey": "WO3",
                "anNo": 4,
                "anQty": 700,
                "acResource": "Resource4",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO3",
                "anNo": 5,
                "anQty": 600,
                "acResource": "Resource1",
                "acName": "Operation 1"
            },
            {
                "acKey": "WO3",
                "anNo": 6,
                "anQty": 450,
                "acResource": "Resource2",
                "acName": "Operation 2"
            },
            {
                "acKey": "WO3",
                "anNo": 3,
                "anQty": 300,
                "acResource": "Resource1",
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
    company_working_hours = [(0, 24)]

    # Initialize dictionaries to store resource calendars and jobs
    resource_calendars = defaultdict(list)
    jobs = []

    # Parse the data from JSON
    for record in json_data['test_WOEx']:

        name_n = record["acKey"]
        deadline_n = record["adDeliveryDeadline"]
        parent_n = record["acKeyParent"]

        # Create job based on the record
        job = {
            'acKey': record['acKey'],
            'deadline': deadline_date,
            'operations': []
        }

        # Add the job to the list of jobs
        jobs.append(job)

    # Create resource requirements for each operation

    return company_working_hours, resource_calendars, jobs_list
