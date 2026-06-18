TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check if a person is available between two times on a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {"type": "string", "description": "Name of the person, e.g. Director Kumar"},
                    "requester_name": {"type": "string", "description": "Logged in user name"},
                    "date": {"type": "string", "description": "Date as YYYY-MM-DD"},
                    "start_hour": {"type": "integer", "description": "Start hour 0-23, default 14"},
                    "end_hour": {"type": "integer", "description": "End hour 0-23, default 15"},
                },
                "required": ["person_name", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_meeting_request",
            "description": "Create a pending meeting request with an executive. Goes to their EA for approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "requester_name": {"type": "string"},
                    "target_person_name": {"type": "string"},
                    "reason": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_hour": {"type": "integer", "default": 14},
                    "end_hour": {"type": "integer", "default": 15},
                },
                "required": ["requester_name", "target_person_name", "reason", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_meeting_email",
            "description": "Draft a polite email to request a meeting with someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "requester_name": {"type": "string"},
                    "target_person_name": {"type": "string"},
                    "reason": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_hour": {"type": "integer", "default": 14},
                    "end_hour": {"type": "integer", "default": 15},
                },
                "required": ["requester_name", "target_person_name", "reason", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_person",
            "description": "Look up a person by name in the office directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_rooms",
            "description": "List all meeting rooms and desks in the office.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_room_availability",
            "description": "Check if a meeting room is available at a given date and time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_name": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_hour": {"type": "integer", "default": 10},
                    "end_hour": {"type": "integer", "default": 11},
                },
                "required": ["room_name", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_room",
            "description": "Book a meeting room or desk for a time slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booker_name": {"type": "string"},
                    "room_name": {"type": "string"},
                    "title": {"type": "string", "description": "Purpose of booking"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_hour": {"type": "integer", "default": 10},
                    "end_hour": {"type": "integer", "default": 11},
                },
                "required": ["booker_name", "room_name", "title", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_tasks",
            "description": "Get tasks assigned to the logged-in user.",
            "parameters": {"type": "object", "properties": {"requester_name": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team_status",
            "description": "Get manager's team task summary and overdue tasks.",
            "parameters": {"type": "object", "properties": {"manager_name": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assign_task",
            "description": "Assign a task to an employee. Only managers/admin should use this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "manager_name": {"type": "string"},
                    "assignee_name": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string"},
                    "due_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["manager_name", "assignee_name", "title", "due_date"],
            },
        },
    },
]
