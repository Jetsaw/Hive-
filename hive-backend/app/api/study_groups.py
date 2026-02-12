"""
Study Group Matching API
Create, join, and find study groups with intelligent partner matching
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sqlite3
import json
from app.core.config import settings

router = APIRouter(prefix="/api/study-groups", tags=["study-groups"])


class StudentProfile(BaseModel):
    user_id: str
    name: str
    programme: str = ""
    enrolled_courses: List[str] = []
    interests: List[str] = []
    trimester: str = ""


class GroupCreate(BaseModel):
    name: str
    course_code: str
    description: str = ""
    max_members: int = Field(default=6, ge=2, le=12)
    creator_id: str = ""


def _init_study_tables():
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            programme TEXT DEFAULT '',
            enrolled_courses TEXT DEFAULT '[]',
            interests TEXT DEFAULT '[]',
            trimester TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS study_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course_code TEXT NOT NULL,
            description TEXT DEFAULT '',
            max_members INTEGER DEFAULT 6,
            creator_id TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS group_members (
            group_id INTEGER,
            user_id TEXT,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES study_groups(id)
        );
    """)
    conn.commit()
    conn.close()


_init_study_tables()


@router.post("/register")
async def register_student(profile: StudentProfile):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO student_profiles
           (user_id, name, programme, enrolled_courses, interests, trimester)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (profile.user_id, profile.name, profile.programme,
         json.dumps(profile.enrolled_courses), json.dumps(profile.interests),
         profile.trimester),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Profile registered"}


@router.post("/create")
async def create_group(group: GroupCreate):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    cur = conn.execute(
        "INSERT INTO study_groups (name, course_code, description, max_members, creator_id) VALUES (?, ?, ?, ?, ?)",
        (group.name, group.course_code, group.description, group.max_members, group.creator_id),
    )
    group_id = cur.lastrowid
    if group.creator_id:
        conn.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
                      (group_id, group.creator_id))
    conn.commit()
    conn.close()
    return {"success": True, "group_id": group_id}


@router.get("")
async def list_groups(course_code: Optional[str] = None):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    if course_code:
        cur = conn.execute(
            "SELECT id, name, course_code, description, max_members, creator_id, created_at FROM study_groups WHERE course_code=?",
            (course_code,))
    else:
        cur = conn.execute(
            "SELECT id, name, course_code, description, max_members, creator_id, created_at FROM study_groups")
    groups = []
    for r in cur.fetchall():
        member_count = conn.execute("SELECT COUNT(*) FROM group_members WHERE group_id=?", (r[0],)).fetchone()[0]
        groups.append({
            "id": r[0], "name": r[1], "course_code": r[2], "description": r[3],
            "max_members": r[4], "creator_id": r[5], "created_at": r[6],
            "member_count": member_count,
        })
    conn.close()
    return groups


@router.post("/{group_id}/join")
async def join_group(group_id: int, user_id: str = ""):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    group = conn.execute("SELECT max_members FROM study_groups WHERE id=?", (group_id,)).fetchone()
    if not group:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")
    member_count = conn.execute("SELECT COUNT(*) FROM group_members WHERE group_id=?", (group_id,)).fetchone()[0]
    if member_count >= group[0]:
        conn.close()
        raise HTTPException(status_code=400, detail="Group is full")
    conn.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Joined group"}


@router.post("/{group_id}/leave")
async def leave_group(group_id: int, user_id: str = ""):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.execute("DELETE FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Left group"}


@router.get("/user/{user_id}")
async def get_user_groups(user_id: str):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    cur = conn.execute("""
        SELECT sg.id, sg.name, sg.course_code, sg.description, sg.max_members
        FROM study_groups sg
        JOIN group_members gm ON sg.id = gm.group_id
        WHERE gm.user_id = ?
    """, (user_id,))
    groups = [{"id": r[0], "name": r[1], "course_code": r[2], "description": r[3], "max_members": r[4]}
              for r in cur.fetchall()]
    conn.close()
    return groups


@router.get("/matches/{user_id}/{course_code}")
async def find_matches(user_id: str, course_code: str):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    user = conn.execute("SELECT * FROM student_profiles WHERE user_id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return {"matches": [], "message": "Register your profile first"}

    user_courses = json.loads(user[3]) if user[3] else []
    user_interests = json.loads(user[4]) if user[4] else []
    user_trimester = user[5]

    others = conn.execute("SELECT * FROM student_profiles WHERE user_id != ?", (user_id,)).fetchall()
    conn.close()

    matches = []
    for other in others:
        other_courses = json.loads(other[3]) if other[3] else []
        other_interests = json.loads(other[4]) if other[4] else []
        other_trimester = other[5]

        score = 0
        if course_code in other_courses:
            score += 30
        common_courses = set(user_courses) & set(other_courses)
        score += len(common_courses) * 10
        common_interests = set(user_interests) & set(other_interests)
        score += len(common_interests) * 5
        if user_trimester and user_trimester == other_trimester:
            score += 15

        score = min(score, 100)

        if score > 0:
            matches.append({
                "user_id": other[0],
                "name": other[1],
                "programme": other[2],
                "score": score,
                "common_courses": list(common_courses),
                "common_interests": list(common_interests),
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": matches[:10]}
