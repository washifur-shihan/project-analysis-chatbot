from datetime import datetime
from sqlalchemy.orm import Session
from app.models import ProjectFact


def normalize(text: str) -> str:
    return text.lower().strip()


def save_project_facts(db: Session, payload: dict):
    """
    Save project facts to the database with proper upsert handling.
    Deduplicates records within the same batch to prevent UNIQUE constraint violations.
    """
    seen_ids = set()  # Track record IDs we've already processed in this batch

    for item in payload.get("data", []):
        project = item.get("project", {})
        project_id = project.get("id")
        project_name = project.get("name", "")

        # Skip items with no project ID
        if not project_id:
            continue

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

        meeting_links = []

        for meeting in project.get("meetings", []):
            title = meeting.get("title") or "Meeting"
            meeting_url = meeting.get("meetingUrl")
            video_url = meeting.get("videoPlayUrl")
            transcript_url = meeting.get("transcriptUrl")

            if meeting_url:
                meeting_links.append(f"{title}: {meeting_url}")

            if video_url:
                meeting_links.append(f"{title} video link: {video_url}")

            if transcript_url:
                meeting_links.append(f"{title} transcript link: {transcript_url}")

        for link_item in project.get("meetingLinks", []):
            title = link_item.get("title", "Meeting link")
            link = link_item.get("link")
            if link:
                meeting_links.append(f"{title}: {link}")

        facts = [
            {
                "fact_type": "meeting_links",
                "question_key": "meeting links",
                "answer": (
                    f"Meeting links for {project_name}: "
                    + ("\n".join(meeting_links) if meeting_links else "No meeting links found.")
                )
            },
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
                    + (", ".join(task_titles) if task_titles else "No tasks found.")
                )
            },
            {
                "fact_type": "meetings",
                "question_key": "meetings",
                "answer": (
                    f"Meetings for {project_name}: "
                    + (", ".join(meeting_titles) if meeting_titles else "No meetings found.")
                )
            },
            {
                "fact_type": "issues",
                "question_key": "issues",
                "answer": (
                    f"Issues for {project_name}: "
                    + (", ".join(raidd.get("issues", [])) if raidd.get("issues") else "No issues found.")
                )
            },
            {
                "fact_type": "risks",
                "question_key": "risks",
                "answer": (
                    f"Risks for {project_name}: "
                    + (", ".join(raidd.get("risks", [])) if raidd.get("risks") else "No risks found.")
                )
            },
            {
                "fact_type": "decisions",
                "question_key": "decisions",
                "answer": (
                    f"Decisions for {project_name}: "
                    + (", ".join(raidd.get("decisions", [])) if raidd.get("decisions") else "No decisions found.")
                )
            },
            {
                "fact_type": "assumptions",
                "question_key": "assumptions",
                "answer": (
                    f"Assumptions for {project_name}: "
                    + (", ".join(raidd.get("assumptions", [])) if raidd.get("assumptions") else "No assumptions found.")
                )
            },
            {
                "fact_type": "dependencies",
                "question_key": "dependencies",
                "answer": (
                    f"Dependencies for {project_name}: "
                    + (", ".join(raidd.get("dependencies", [])) if raidd.get("dependencies") else "No dependencies found.")
                )
            },
            {
                "fact_type": "action_points",
                "question_key": "action points",
                "answer": (
                    f"Recommended action points for {project_name}: "
                    + (", ".join(ai.get("actionPoints", [])) if ai.get("actionPoints") else "No action points found.")
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

            # Skip if we already processed this exact record_id in this batch
            # This prevents duplicate inserts when the same project appears multiple times
            if record_id in seen_ids:
                continue
            seen_ids.add(record_id)

            now = datetime.utcnow()

            # Check if record already exists in database
            existing = db.query(ProjectFact).filter(ProjectFact.id == record_id).first()

            if existing:
                # Update existing record
                existing.project_name = project_name
                existing.fact_type = fact["fact_type"]
                existing.question_key = fact["question_key"]
                existing.answer = fact["answer"]
                existing.updated_at = now
            else:
                # Insert new record
                db.add(ProjectFact(
                    id=record_id,
                    project_id=project_id,
                    project_name=project_name,
                    fact_type=fact["fact_type"],
                    question_key=fact["question_key"],
                    answer=fact["answer"],
                    updated_at=now
                ))

    db.commit()


def find_cached_answer(db: Session, question: str):
    q = normalize(question)

    project = None
    projects = db.query(ProjectFact.project_name).distinct().all()
    project_names = [row[0] for row in projects if row[0]]

    for name in project_names:
        if name.lower() in q:
            project = name
            break

    if not project and len(project_names) == 1:
        project = project_names[0]

    if not project:
        return None

    fact_types = []

    if "manager" in q or "project manager" in q:
        fact_types.append("manager")

    if "vendor" in q:
        fact_types.append("vendor")

    if "team" in q or "assigned" in q or "assigned team" in q:
        fact_types.append("team")

    if "owner" in q:
        fact_types.append("owner")

    if "status" in q:
        fact_types.append("status")

    if "health" in q:
        fact_types.append("health")

    if "progress" in q:
        fact_types.append("progress")

    if "task" in q:
        fact_types.append("tasks")

    if ("meeting" in q and ("link" in q or "url" in q)) or "meeting link" in q:
        fact_types.append("meeting_links")
    elif "meeting" in q:
        fact_types.append("meetings")

    if "issue" in q or "problem" in q:
        fact_types.append("issues")

    if "risk" in q:
        fact_types.append("risks")

    if "decision" in q:
        fact_types.append("decisions")

    if "assumption" in q:
        fact_types.append("assumptions")

    if "depend" in q or "dependency" in q:
        fact_types.append("dependencies")

    if "action" in q or "todo" in q or "next step" in q:
        fact_types.append("action_points")

    if "summary" in q or "summarize" in q or "note" in q or "detail" in q or "weekly" in q:
        fact_types.append("summary")

    if "what is" in q or "about" in q or "describe" in q:
        fact_types.append("description")

    # remove duplicates while preserving order
    fact_types = list(dict.fromkeys(fact_types))

    if not fact_types:
        return None

    answers = []

    for fact_type in fact_types:
        fact = (
            db.query(ProjectFact)
            .filter(ProjectFact.project_name == project)
            .filter(ProjectFact.fact_type == fact_type)
            .first()
        )

        if fact:
            answers.append(fact.answer)

    if not answers:
        return None

    return {
        "answer": "\n\n".join(answers),
        "source": "database_cache"
    }