#input_type_name: CreatePetitionInput
#output_type_name: CreatePetitionOutput
#function_name: create_petition

from datetime import datetime, timezone

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext, Pod


class CreatePetitionInput(BaseModel):
    photo_url: str
    address: str = ""
    lat: float
    lng: float
    description: str = ""
    workflow_run_id: str | None = None


class CreatePetitionOutput(BaseModel):
    petition_id: str
    status: str


async def create_petition(ctx: FunctionContext, data: CreatePetitionInput) -> CreatePetitionOutput:
    pod = Pod.from_env()

    row = pod.table("petitions").create(
        {
            "photo_url": data.photo_url,
            "location": {"address": data.address, "lat": data.lat, "lng": data.lng},
            "description": data.description,
            "status": "draft",
            "workflow_run_id": data.workflow_run_id,
        }
    )

    petition_id = row["id"]
    pod.table("activity_log").create(
        {
            "petition_id": petition_id,
            "event_type": "created",
            "message": "Petition created from citizen report",
            "metadata": {"description": data.description[:200]},
        }
    )

    return CreatePetitionOutput(petition_id=petition_id, status="draft")
