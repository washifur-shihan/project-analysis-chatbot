import json
from typing import List, Dict, Any


def make_chunk_id(project_id: str, chunk_type: str, item_id: str = "main") -> str:
    return f"{project_id}:{chunk_type}:{item_id}"


def chunk_project_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = []

    for item in payload.get("data", []):
        project = item.get("project", {})
        project_id = project.get("id")
        project_name = project.get("name", "Unknown Project")

        # 1. Project overview chunk
        overview_text = f"""
Project Name: {project_name}
Project Status: {project.get("status")}
Project Health: {project.get("projectHealth")}
Project Progress: {project.get("projectProgress")}
Vendor: {project.get("vendorName")}
Start Date: {project.get("startDate")}
End Date: {project.get("endDate")}
Description:
{project.get("description")}

Weekly AI Summary:
{project.get("weeklyAiSummary")}

Project AI Summary:
{json.dumps(project.get("projectAiSummary", []), ensure_ascii=False)}
"""

        chunks.append({
            "id": make_chunk_id(project_id, "overview"),
            "text": overview_text.strip(),
            "metadata": {
                "project_id": project_id,
                "project_name": project_name,
                "type": "project_overview",
                "status": project.get("status"),
                "health": project.get("projectHealth"),
            }
        })

        # 2. AI details / RAIDD chunk
        ai_details = project.get("projectAiDetails") or {}
        raidd_text = f"""
Project Name: {project_name}
AI Flag: {ai_details.get("flag")}
Project Health: {ai_details.get("projectHealth")}
Project Score: {ai_details.get("projectScore")}
AI Summary:
{ai_details.get("summary")}

Notes:
{ai_details.get("notes")}

Weekly Summary:
{ai_details.get("weeklySummary")}

RAIDD Flags:
Risks: {json.dumps(ai_details.get("raiddFlags", {}).get("risks", []), ensure_ascii=False)}
Assumptions: {json.dumps(ai_details.get("raiddFlags", {}).get("assumptions", []), ensure_ascii=False)}
Issues: {json.dumps(ai_details.get("raiddFlags", {}).get("issues", []), ensure_ascii=False)}
Dependencies: {json.dumps(ai_details.get("raiddFlags", {}).get("dependencies", []), ensure_ascii=False)}
Decisions: {json.dumps(ai_details.get("raiddFlags", {}).get("decisions", []), ensure_ascii=False)}

Action Points:
{json.dumps(ai_details.get("actionPoints", []), ensure_ascii=False)}

Discussion Points:
{json.dumps(ai_details.get("discussionPoints", []), ensure_ascii=False)}
"""

        chunks.append({
            "id": make_chunk_id(project_id, "ai_details"),
            "text": raidd_text.strip(),
            "metadata": {
                "project_id": project_id,
                "project_name": project_name,
                "type": "project_ai_details",
                "flag": ai_details.get("flag"),
                "health": ai_details.get("projectHealth"),
            }
        })

        # 3. Task chunks
        for task in project.get("tasks", []):
            task_text = f"""
Project Name: {project_name}
Task Title: {task.get("title")}
Task Status: {task.get("status")}
Task Priority: {task.get("priority")}
Start Date: {task.get("startDate")}
End Date: {task.get("endDate")}
Description:
{task.get("taskDescription")}
"""
            chunks.append({
                "id": make_chunk_id(project_id, "task", task.get("id")),
                "text": task_text.strip(),
                "metadata": {
                    "project_id": project_id,
                    "project_name": project_name,
                    "type": "task",
                    "task_id": task.get("id"),
                    "task_status": task.get("status"),
                    "priority": task.get("priority"),
                }
            })

        # 4. Meeting chunks
        for meeting in project.get("meetings", []):
            meeting_text = f"""
Project Name: {project_name}
Meeting Title: {meeting.get("title")}
Meeting Date: {meeting.get("meetingDate")}
Notes:
{meeting.get("notes")}

Last Meeting Summary:
{meeting.get("lastMeetingSummary")}

AI Meeting Summary:
{json.dumps(meeting.get("aiMeetingSummary", []), ensure_ascii=False)}

Key Points:
{json.dumps(meeting.get("keyPoints", []), ensure_ascii=False)}

Action Points:
{json.dumps(meeting.get("actionPoints", []), ensure_ascii=False)}
"""
            chunks.append({
                "id": make_chunk_id(project_id, "meeting", meeting.get("id")),
                "text": meeting_text.strip(),
                "metadata": {
                    "project_id": project_id,
                    "project_name": project_name,
                    "type": "meeting",
                    "meeting_id": meeting.get("id"),
                    "meeting_title": meeting.get("title"),
                }
            })

    return chunks