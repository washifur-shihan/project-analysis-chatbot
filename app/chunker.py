import json
from typing import Any, Dict, List


def make_chunk_id(project_id: str, chunk_type: str, item_id: str = "main") -> str:
    return f"{project_id}:{chunk_type}:{item_id}"


def flatten_json(obj: Any, prefix: str = "") -> List[str]:
    lines = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            lines.extend(flatten_json(value, new_prefix))

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            new_prefix = f"{prefix}[{index}]"
            lines.extend(flatten_json(value, new_prefix))

    else:
        lines.append(f"{prefix}: {obj}")

    return lines


def chunk_full_json_payload(payload: Dict[str, Any], max_lines: int = 40) -> List[Dict[str, Any]]:
    chunks = []

    for item in payload.get("data", []):
        project = item.get("project", {})
        project_id = project.get("id", "unknown")
        project_name = project.get("name", "Unknown Project")

        lines = flatten_json(item)

        for i in range(0, len(lines), max_lines):
            part = lines[i:i + max_lines]

            text = f"""
Project Name: {project_name}
Project ID: {project_id}

Full JSON searchable data:
{chr(10).join(part)}
""".strip()

            chunks.append({
                "id": f"{project_id}:full_json:{i // max_lines}",
                "text": text,
                "metadata": {
                    "project_id": project_id,
                    "project_name": project_name,
                    "type": "full_json",
                    "chunk_index": i // max_lines
                }
            })

    return chunks


def chunk_project_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = []

    for item in payload.get("data", []):
        project = item.get("project", {})
        project_id = project.get("id")
        project_name = project.get("name", "Unknown Project")

        manager = project.get("manager") or {}
        assign_team = project.get("assignTeam") or {}
        ai_details = project.get("projectAiDetails") or {}
        raidd = ai_details.get("raiddFlags") or {}

        manager_name = f"{manager.get('firstName', '')} {manager.get('lastName', '')}".strip()

        overview_text = f"""
Project Name: {project_name}
Project ID: {project_id}
Project Status: {project.get("status")}
Project Health: {project.get("projectHealth")}
Project Progress: {project.get("projectProgress")}
Vendor Name: {project.get("vendorName")}
Manager Name: {manager_name}
Manager Role: {manager.get("role")}
Assigned Team: {assign_team.get("name")}
Project Owner ID: {project.get("projectOwnerId")}
Manager ID: {project.get("managerId")}
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

Risks:
{json.dumps(raidd.get("risks", []), ensure_ascii=False)}

Assumptions:
{json.dumps(raidd.get("assumptions", []), ensure_ascii=False)}

Issues:
{json.dumps(raidd.get("issues", []), ensure_ascii=False)}

Dependencies:
{json.dumps(raidd.get("dependencies", []), ensure_ascii=False)}

Decisions:
{json.dumps(raidd.get("decisions", []), ensure_ascii=False)}

Action Points:
{json.dumps(ai_details.get("actionPoints", []), ensure_ascii=False)}

Discussion Points:
{json.dumps(ai_details.get("discussionPoints", []), ensure_ascii=False)}

Milestones:
{json.dumps(ai_details.get("milestones", []), ensure_ascii=False)}
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

        for meeting in project.get("meetings", []):
            transcript = meeting.get("transcriptData") or []

            meeting_text = f"""
Project Name: {project_name}
Meeting Title: {meeting.get("title")}
Meeting Date: {meeting.get("meetingDate")}
Meeting URL: {meeting.get("meetingUrl")}
Video Play URL: {meeting.get("videoPlayUrl")}
Transcript URL: {meeting.get("transcriptUrl")}

Notes:
{meeting.get("notes")}

Last Meeting Summary:
{meeting.get("lastMeetingSummary")}

Agenda:
{json.dumps(meeting.get("agenda", {}), ensure_ascii=False)}

AI Meeting Summary:
{json.dumps(meeting.get("aiMeetingSummary", []), ensure_ascii=False)}

Key Points:
{json.dumps(meeting.get("keyPoints", []), ensure_ascii=False)}

Action Points:
{json.dumps(meeting.get("actionPoints", []), ensure_ascii=False)}

Transcript:
{json.dumps(transcript[:80], ensure_ascii=False)}
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