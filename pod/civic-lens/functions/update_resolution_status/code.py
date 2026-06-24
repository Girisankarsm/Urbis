#input_type_name: UpdateResolutionStatusInput
#output_type_name: UpdateResolutionStatusOutput
#function_name: update_resolution_status

from datetime import datetime, timezone

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class ResolutionVerdict(BaseModel):
    resolved: bool
    confidence: float = 0.0
    reasoning: str = ""
    recommended_status: str = "under_review"


class UpdateResolutionStatusInput(BaseModel):
    petition_id: str
    verdict: ResolutionVerdict


class UpdateResolutionStatusOutput(BaseModel):
    petition_id: str
    status: str
    resolved: bool


async def update_resolution_status(
    ctx: FunctionContext, data: UpdateResolutionStatusInput
) -> UpdateResolutionStatusOutput:
    pod = Pod.from_env()
    verdict = data.verdict

    status = verdict.recommended_status
    if verdict.resolved and verdict.confidence >= 0.7:
        status = "resolved"

    updates: dict = {
        "resolution_verdict": verdict.model_dump(),
        "status": status,
    }
    if status == "resolved":
        updates["resolved_at"] = datetime.now(timezone.utc).isoformat()

    pod.table("petitions").update(data.petition_id, updates)

    pod.table("activity_log").create(
        {
            "petition_id": data.petition_id,
            "event_type": "resolution_checked",
            "message": f"Resolution check: {'resolved' if verdict.resolved else 'still open'} (confidence {verdict.confidence:.0%})",
            "metadata": verdict.model_dump(),
        }
    )

    return UpdateResolutionStatusOutput(
        petition_id=data.petition_id,
        status=status,
        resolved=verdict.resolved,
    )
