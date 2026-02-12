"""
Course Comparison API
Compare BSc Applied AI vs BSc Intelligent Robotics side-by-side
"""
from fastapi import APIRouter
from typing import Optional

router = APIRouter(prefix="/api/courses", tags=["comparison"])

PROGRAMMES = {
    "Applied Artificial Intelligence": {
        "code": "BSc-AAI",
        "full_name": "Bachelor of Science (Hons.) Applied Artificial Intelligence",
        "duration": "4 years (12 trimesters)",
        "credit_hours": 130,
        "focus_areas": [
            "Machine Learning & Deep Learning",
            "Natural Language Processing",
            "Computer Vision",
            "Data Science & Analytics",
            "AI Ethics & Governance",
        ],
        "career_paths": [
            "AI/ML Engineer",
            "Data Scientist",
            "NLP Engineer",
            "Computer Vision Engineer",
            "AI Research Scientist",
            "Business Intelligence Analyst",
        ],
        "core_subjects": [
            "Introduction to Artificial Intelligence",
            "Machine Learning",
            "Deep Learning",
            "Natural Language Processing",
            "Computer Vision",
            "Data Mining",
            "Big Data Analytics",
            "AI Ethics",
        ],
        "unique_subjects": [
            "Generative AI Applications",
            "Reinforcement Learning",
            "AI for Business",
            "Recommendation Systems",
        ],
        "shared_subjects": [
            "Programming Fundamentals",
            "Data Structures & Algorithms",
            "Mathematics for Computing",
            "Statistics & Probability",
            "Database Systems",
            "Software Engineering",
            "Final Year Project",
            "Industrial Training",
        ],
    },
    "Intelligent Robotics": {
        "code": "BSc-IR",
        "full_name": "Bachelor of Science (Hons.) Intelligent Robotics",
        "duration": "4 years (12 trimesters)",
        "credit_hours": 130,
        "focus_areas": [
            "Robotics & Automation",
            "Embedded Systems",
            "Control Systems",
            "IoT & Sensor Networks",
            "Robot Vision & Perception",
        ],
        "career_paths": [
            "Robotics Engineer",
            "Automation Engineer",
            "Embedded Systems Developer",
            "IoT Solutions Architect",
            "Control Systems Engineer",
            "Research Scientist (Robotics)",
        ],
        "core_subjects": [
            "Introduction to Robotics",
            "Robot Kinematics & Dynamics",
            "Embedded Systems",
            "Control Systems",
            "Sensor & Actuator Technology",
            "Robot Vision",
            "IoT Systems",
            "Human-Robot Interaction",
        ],
        "unique_subjects": [
            "Mobile Robotics",
            "Autonomous Systems",
            "Robot Operating System (ROS)",
            "Mechatronics",
        ],
        "shared_subjects": [
            "Programming Fundamentals",
            "Data Structures & Algorithms",
            "Mathematics for Computing",
            "Statistics & Probability",
            "Database Systems",
            "Software Engineering",
            "Final Year Project",
            "Industrial Training",
        ],
    },
}


@router.get("/compare")
async def compare_courses(
    course1: str = "Applied Artificial Intelligence",
    course2: str = "Intelligent Robotics",
):
    p1 = PROGRAMMES.get(course1)
    p2 = PROGRAMMES.get(course2)

    if not p1 or not p2:
        available = list(PROGRAMMES.keys())
        return {"error": f"Programme not found. Available: {available}"}

    similarities = list(set(p1["shared_subjects"]) & set(p2["shared_subjects"]))

    return {
        "programme_1": {
            "name": course1,
            "code": p1["code"],
            "full_name": p1["full_name"],
            "duration": p1["duration"],
            "credit_hours": p1["credit_hours"],
            "focus_areas": p1["focus_areas"],
            "career_paths": p1["career_paths"],
            "unique_subjects": p1["unique_subjects"],
            "core_subjects": p1["core_subjects"],
        },
        "programme_2": {
            "name": course2,
            "code": p2["code"],
            "full_name": p2["full_name"],
            "duration": p2["duration"],
            "credit_hours": p2["credit_hours"],
            "focus_areas": p2["focus_areas"],
            "career_paths": p2["career_paths"],
            "unique_subjects": p2["unique_subjects"],
            "core_subjects": p2["core_subjects"],
        },
        "shared_subjects": similarities,
        "shared_count": len(similarities),
        "recommendation": (
            "Choose Applied AI if you're passionate about machine learning, data science, "
            "and building intelligent software systems. Choose Intelligent Robotics if you prefer "
            "hands-on hardware, building physical robots, and working with embedded systems."
        ),
    }


@router.get("/list")
async def list_programmes():
    return [
        {
            "name": name,
            "code": data["code"],
            "full_name": data["full_name"],
            "credit_hours": data["credit_hours"],
            "focus_areas": data["focus_areas"],
        }
        for name, data in PROGRAMMES.items()
    ]
