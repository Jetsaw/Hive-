"""
Academic Calendar API
Provides trimester dates, deadlines, holidays, and exam schedules
"""
from fastapi import APIRouter
from datetime import datetime, date
from typing import List, Dict

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

# MMU Academic Calendar Data
TRIMESTERS = [
    {
        "id": "T2530",
        "name": "Trimester 1 2025/2026",
        "start": "2025-10-27",
        "end": "2026-02-27",
        "exam_start": "2026-02-09",
        "exam_end": "2026-02-27",
        "registration_start": "2025-10-13",
        "registration_end": "2025-10-24",
        "add_drop_end": "2025-11-07",
        "withdrawal_end": "2025-12-19",
    },
    {
        "id": "T2610",
        "name": "Trimester 2 2025/2026",
        "start": "2026-03-16",
        "end": "2026-07-17",
        "exam_start": "2026-06-29",
        "exam_end": "2026-07-17",
        "registration_start": "2026-03-02",
        "registration_end": "2026-03-13",
        "add_drop_end": "2026-03-27",
        "withdrawal_end": "2026-05-08",
    },
    {
        "id": "T2620",
        "name": "Trimester 3 2025/2026",
        "start": "2026-07-27",
        "end": "2026-11-27",
        "exam_start": "2026-11-09",
        "exam_end": "2026-11-27",
        "registration_start": "2026-07-13",
        "registration_end": "2026-07-24",
        "add_drop_end": "2026-08-07",
        "withdrawal_end": "2026-09-18",
    },
]

HOLIDAYS = [
    {"name": "Deepavali", "date": "2025-10-20", "type": "public"},
    {"name": "Christmas Day", "date": "2025-12-25", "type": "public"},
    {"name": "New Year's Day", "date": "2026-01-01", "type": "public"},
    {"name": "Thaipusam", "date": "2026-01-27", "type": "public"},
    {"name": "Chinese New Year", "date": "2026-02-17", "type": "public"},
    {"name": "Chinese New Year (2nd Day)", "date": "2026-02-18", "type": "public"},
    {"name": "Nuzul Al-Quran", "date": "2026-03-20", "type": "public"},
    {"name": "Hari Raya Aidilfitri", "date": "2026-03-31", "type": "public"},
    {"name": "Hari Raya Aidilfitri (2nd Day)", "date": "2026-04-01", "type": "public"},
    {"name": "Labour Day", "date": "2026-05-01", "type": "public"},
    {"name": "Wesak Day", "date": "2026-05-12", "type": "public"},
    {"name": "Agong's Birthday", "date": "2026-06-01", "type": "public"},
    {"name": "Hari Raya Haji", "date": "2026-06-07", "type": "public"},
    {"name": "Awal Muharram", "date": "2026-06-27", "type": "public"},
    {"name": "Malaysia Day", "date": "2026-09-16", "type": "public"},
    {"name": "Merdeka Day", "date": "2026-08-31", "type": "public"},
    {"name": "Prophet Muhammad's Birthday", "date": "2026-09-06", "type": "public"},
]


def _get_current_trimester():
    today = date.today().isoformat()
    for tri in TRIMESTERS:
        if tri["start"] <= today <= tri["end"]:
            return tri
    # Default to nearest upcoming
    for tri in TRIMESTERS:
        if tri["start"] > today:
            return tri
    return TRIMESTERS[-1]


def _days_between(d1: str, d2: str) -> int:
    return (date.fromisoformat(d2) - date.fromisoformat(d1)).days


@router.get("/current")
async def get_current_trimester():
    tri = _get_current_trimester()
    today = date.today().isoformat()
    total_days = _days_between(tri["start"], tri["end"])
    elapsed = max(0, _days_between(tri["start"], today))
    remaining = max(0, _days_between(today, tri["end"]))
    progress = round((elapsed / total_days) * 100, 1) if total_days > 0 else 0

    return {
        **tri,
        "days_remaining": remaining,
        "days_elapsed": elapsed,
        "total_days": total_days,
        "progress_percent": min(progress, 100),
    }


@router.get("/upcoming")
async def get_upcoming_events():
    today = date.today().isoformat()
    tri = _get_current_trimester()
    events = []

    deadlines = [
        {"name": "Add/Drop Deadline", "date": tri["add_drop_end"], "type": "deadline"},
        {"name": "Withdrawal Deadline", "date": tri["withdrawal_end"], "type": "deadline"},
        {"name": "Exam Period Starts", "date": tri["exam_start"], "type": "exam"},
        {"name": "Exam Period Ends", "date": tri["exam_end"], "type": "exam"},
        {"name": "Trimester Ends", "date": tri["end"], "type": "trimester"},
    ]

    for d in deadlines:
        if d["date"] >= today:
            d["days_until"] = _days_between(today, d["date"])
            events.append(d)

    for h in HOLIDAYS:
        if today <= h["date"] <= tri["end"]:
            h["days_until"] = _days_between(today, h["date"])
            events.append(h)

    events.sort(key=lambda x: x["date"])
    return events[:15]


@router.get("/deadlines")
async def get_deadlines():
    today = date.today().isoformat()
    all_deadlines = []
    for tri in TRIMESTERS:
        items = [
            {"name": f"Registration Opens ({tri['id']})", "date": tri["registration_start"], "trimester": tri["id"]},
            {"name": f"Registration Closes ({tri['id']})", "date": tri["registration_end"], "trimester": tri["id"]},
            {"name": f"Add/Drop Deadline ({tri['id']})", "date": tri["add_drop_end"], "trimester": tri["id"]},
            {"name": f"Withdrawal Deadline ({tri['id']})", "date": tri["withdrawal_end"], "trimester": tri["id"]},
            {"name": f"Exam Start ({tri['id']})", "date": tri["exam_start"], "trimester": tri["id"]},
            {"name": f"Exam End ({tri['id']})", "date": tri["exam_end"], "trimester": tri["id"]},
        ]
        for item in items:
            item["passed"] = item["date"] < today
            item["days_until"] = _days_between(today, item["date"]) if not item["passed"] else None
        all_deadlines.extend(items)
    return all_deadlines


@router.get("/holidays")
async def get_holidays():
    today = date.today().isoformat()
    result = []
    for h in HOLIDAYS:
        entry = {**h}
        entry["passed"] = h["date"] < today
        entry["days_until"] = _days_between(today, h["date"]) if not entry["passed"] else None
        result.append(entry)
    return result


@router.get("/summary")
async def get_calendar_summary():
    tri = _get_current_trimester()
    today = date.today().isoformat()
    remaining = max(0, _days_between(today, tri["end"]))
    total = _days_between(tri["start"], tri["end"])
    elapsed = max(0, _days_between(tri["start"], today))
    progress = round((elapsed / total) * 100, 1) if total > 0 else 0

    upcoming_holidays = [h for h in HOLIDAYS if today <= h["date"] <= tri["end"]][:3]

    return {
        "trimester": tri["name"],
        "trimester_id": tri["id"],
        "days_remaining": remaining,
        "progress_percent": min(progress, 100),
        "exam_start": tri["exam_start"],
        "exam_end": tri["exam_end"],
        "upcoming_holidays": upcoming_holidays,
    }
