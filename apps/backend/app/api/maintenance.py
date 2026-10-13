from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.src.retrieve_knowledge import retrieve_documents


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"],
)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=500,
        description="Question about machine maintenance",
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of relevant passages",
    )


@router.post("/search")
def search_maintenance_knowledge(
    request: KnowledgeSearchRequest,
):
    """Retrieve relevant maintenance knowledge."""

    try:
        results = retrieve_documents(
            query=request.query,
            top_k=request.top_k,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="The maintenance knowledge base is unavailable.",
        ) from exc

    return {
        "application": "FactoryPulse AI",
        "retrieval_method": "TF-IDF",
        "query": request.query,
        "results_count": len(results),
        "results": results,
        "notice": (
            "Retrieved passages provide general guidance, "
            "not a confirmed diagnosis. Consult applicable "
            "manufacturer documentation and site procedures."
        ),
    }