from datetime import datetime
from sqlalchemy.orm import Session
from app.models import ProjectFact


def normalize(text: str) -> str:
    return text.lower().strip()


def save_project_facts(db: Session, payload: dict):
    for item in payload.get("data", []):
        project = item.get("project", {})
        project_id = project.get("id")
        project_name = project.get("name", "")

        ai = project.get("projectAiDetails") or {}
        raidd = ai.get("raiddFlags") or {}
        manager = project.get("manager") or {}
        assign_team = project.get("assignTeam") or {}

        manager_name = f"{manager.get('firstName', '')} {manager.get('lastName', '')}".strip()

        task_titles = [
            f"{task.get('title')} ({task.get('status')}, {task.get('priority')})"
            for task in project.get("tasks", [])
        ]

        meeting_titles = [
            f"{meeting.get('title')} on {meeting.get('meetingDate')}"
            for meeting in project.get("meetings", [])
        ]

        facts = [
            {
                "fact_type": "description",
                "question_key": "description",
                "answer": project.get("description") or "No description found."
            },
            {
                "fact_type": "status",
                "question_key": "status",
                "answer": (
                    f"The project {project_name} is currently {project.get('status')}. "
                    f"Its health is {project.get('projectHealth')}, "
                    f"progress is {project.get('projectProgress')}, "
                    f"and AI flag is {ai.get('flag')}."
                )
            },
            {
                "fact_type": "manager",
                "question_key": "manager",
                "answer": (
                    f"The manager of {project_name} is {manager_name}. "
                    f"Their role is {manager.get('role')}."
                )
            },
            {
                "fact_type": "vendor",
                "question_key": "vendor",
                "answer": f"The vendor for {project_name} is {project.get('vendorName')}."
            },
            {
                "fact_type": "team",
                "question_key": "team",
                "answer": f"The assigned team for {project_name} is {assign_team.get('name')}."
            },
            {
                "fact_type": "owner",
                "question_key": "owner",
                "answer": f"The project owner ID for {project_name} is {project.get('projectOwnerId')}."
            },
            {
                "fact_type": "health",
                "question_key": "health",
                "answer": (
                    f"The project {project_name} health is {project.get('projectHealth')}. "
                    f"AI score is {ai.get('projectScore')} and flag is {ai.get('flag')}."
                )
            },
            {
                "fact_type": "progress",
                "question_key": "progress",
                "answer": f"The project {project_name} progress is {project.get('projectProgress')}."
            },
            {
                "fact_type": "tasks",
                "question_key": "tasks",
                "answer": (
                    f"Tasks for {project_name}: "
                    + (", ".join(task_titles) or "No tasks found.")
                )
            },
            {
                "fact_type": "meetings",
                "question_key": "meetings",
                "answer": (
                    f"Meetings for {project_name}: "
                    + (", ".join(meeting_titles) or "No meetings found.")
                )
            },
            {
                "fact_type": "issues",
                "question_key": "issues",
                "answer": (
                    f"Issues for {project_name}: "
                    + (", ".join(raidd.get("issues", [])) or "No issues found.")
                )
            },
            {
                "fact_type": "risks",
                "question_key": "risks",
                "answer": (
                    f"Risks for {project_name}: "
                    + (", ".join(raidd.get("risks", [])) or "No risks found.")
                )
            },
            {
                "fact_type": "decisions",
                "question_key": "decisions",
                "answer": (
                    f"Decisions for {project_name}: "
                    + (", ".join(raidd.get("decisions", [])) or "No decisions found.")
                )
            },
            {
                "fact_type": "assumptions",
                "question_key": "assumptions",
                "answer": (
                    f"Assumptions for {project_name}: "
                    + (", ".join(raidd.get("assumptions", [])) or "No assumptions found.")
                )
            },
            {
                "fact_type": "dependencies",
                "question_key": "dependencies",
                "answer": (
                    f"Dependencies for {project_name}: "
                    + (", ".join(raidd.get("dependencies", [])) or "No dependencies found.")
                )
            },
            {
                "fact_type": "action_points",
                "question_key": "action points",
                "answer": (
                    f"Recommended action points for {project_name}: "
                    + (", ".join(ai.get("actionPoints", [])) or "No action points found.")
                )
            },
            {
                "fact_type": "summary",
                "question_key": "summary",
                "answer": ai.get("summary") or project.get("weeklyAiSummary") or "No summary found."
            }
        ]

        for fact in facts:
            record_id = f"{project_id}:{fact['fact_type']}"

            existing = db.query(ProjectFact).filter(ProjectFact.id == record_id).first()

            if existing:
                existing.answer = fact["answer"]
                existing.updated_at = datetime.utcnow()
            else:
                db.add(ProjectFact(
                    id=record_id,
                    project_id=project_id,
                    project_name=project_name,
                    fact_type=fact["fact_type"],
                    question_key=fact["question_key"],
                    answer=fact["answer"],
                    updated_at=datetime.utcnow()
                ))

    db.commit()


def find_cached_answer(db: Session, question: str):
    q = normalize(question)

    project = None
    projects = db.query(ProjectFact.project_name).distinct().all()

    for row in projects:
        name = row[0]
        if name and name.lower() in q:
            project = name
            break

    if not project:
        return None

    if "manager" in q or "project manager" in q:
        fact_type = "manager"
    elif "vendor" in q:
        fact_type = "vendor"
    elif "team" in q or "assigned team" in q:
        fact_type = "team"
    elif "owner" in q:
        fact_type = "owner"
    elif "status" in q:
        fact_type = "status"
    elif "health" in q:
        fact_type = "health"
    elif "progress" in q:
        fact_type = "progress"
    elif "task" in q:
        fact_type = "tasks"
    elif "meeting" in q:
        fact_type = "meetings"
    elif "issue" in q or "problem" in q:
        fact_type = "issues"
    elif "risk" in q:
        fact_type = "risks"
    elif "decision" in q:
        fact_type = "decisions"
    elif "assumption" in q:
        fact_type = "assumptions"
    elif "depend" in q or "dependency" in q:
        fact_type = "dependencies"
    elif "action" in q or "todo" in q or "next step" in q:
        fact_type = "action_points"
    elif "summary" in q or "summarize" in q:
        fact_type = "summary"
    elif "what is" in q or "about" in q or "describe" in q:
        fact_type = "description"
    else:
        return None

    fact = (
        db.query(ProjectFact)
        .filter(ProjectFact.project_name == project)
        .filter(ProjectFact.fact_type == fact_type)
        .first()
    )

    if not fact:
        return None

    return {
        "answer": fact.answer,
        "source": "database_cache"
    }