import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.src.retrieve_knowledge import retrieve_documents
from ml.src.rag_pipeline import generate_maintenance_answer


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"],
)


class KnowledgeSearchRequest(BaseModel):
    """Request for searching maintenance documentation."""

    query: str = Field(
        min_length=3,
        max_length=500,
        description="Question about machine maintenance",
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of passages to retrieve",
    )


class MaintenanceAssistantRequest(BaseModel):
    """Request for the AI maintenance assistant."""

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Natural-language maintenance question",
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of knowledge passages to retrieve",
    )


@router.post("/search")
def search_maintenance_knowledge(
    request: KnowledgeSearchRequest,
):
    """Retrieve relevant maintenance documentation."""

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

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "application": "FactoryPulse AI",
        "retrieval_method": "TF-IDF",
        "query": request.query,
        "results_count": len(results),
        "results": results,
        "notice": (
            "Retrieved passages provide general guidance, "
            "not a confirmed machine diagnosis."
        ),
    }


@router.post("/assistant")
def ask_maintenance_assistant(
    request: MaintenanceAssistantRequest,
):
    """
    Retrieve maintenance information and optionally generate
    an LLM-powered answer when the provider is configured.
    """

    api_key = os.getenv("FACTORYPULSE_LLM_API_KEY")
    model_name = os.getenv("FACTORYPULSE_LLM_MODEL")

    # Retrieval-only mode: usable before LLM configuration.
    if not api_key or not model_name:
        try:
            results = retrieve_documents(
                query=request.question,
                top_k=request.top_k,
            )

        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=503,
                detail="The maintenance knowledge base is unavailable.",
            ) from exc

        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

        if not results:
            return {
                "application": "FactoryPulse AI",
                "status": "no_relevant_context",
                "question": request.question,
                "answer": None,
                "llm_used": False,
                "sources": [],
                "message": (
                    "No relevant maintenance passages were found. "
                    "Consult the applicable equipment documentation."
                ),
            }

        return {
            "application": "FactoryPulse AI",
            "status": "retrieval_only",
            "question": request.question,
            "answer": None,
            "llm_used": False,
            "sources": results,
            "message": (
                "Relevant maintenance information was retrieved. "
                "LLM generation is not configured yet."
            ),
            "notice": (
                "The retrieved material is general guidance, "
                "not a confirmed diagnosis."
            ),
        }

    # LLM mode: generate a grounded answer when configured.
    try:
        result = generate_maintenance_answer(
            question=request.question,
            top_k=request.top_k,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="The maintenance knowledge base is unavailable.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Maintenance answer generation failed: {exc}",
        ) from exc

    return {
        "application": "FactoryPulse AI",
        "status": "answered",
        "question": request.question,
        **result,
        "notice": (
            "AI-generated guidance is not a confirmed diagnosis. "
            "Follow applicable manufacturer documentation "
            "and site safety procedures."
        ),
    }