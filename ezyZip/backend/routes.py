from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.ai_core.gemini_generator import (
    GeminiConfigurationError,
    GeminiDocumentGenerator,
    GeminiGenerationError,
)

from backend.config import get_settings

from backend.models import (
    DocumentRequest,
    ExportRequest,
    GenerateResponse,
)

from backend.services.document_service import (
    format_docx,
    format_pdf,
    format_txt,
)


router = APIRouter()

settings = get_settings()


ROOT_DIR = Path(
    __file__
).resolve().parents[1]


LOGO_PATH = (
    ROOT_DIR
    / "assets"
    / "logo.png"
)


# ============================================================
# GENERATE DOCUMENT
# ============================================================

@router.post(
    "/generate",
    response_model=GenerateResponse
)
def generate_document(
    request: DocumentRequest
):

    try:

        generator = (
            GeminiDocumentGenerator()
        )


        text = generator.generate_document(

            document_type=request.document_type,

            parties=request.parties,

            terms=request.terms,

            dates=request.dates,

            jurisdiction=request.jurisdiction,

            language=request.language,
        )


        if len(text) > settings.max_document_chars:

            text = text[
                :settings.max_document_chars
            ]


        return GenerateResponse(

            document_type=request.document_type,

            text=text,

            model=settings.gemini_model
        )


    except GeminiConfigurationError as exc:

        raise HTTPException(

            status_code=503,

            detail=str(exc)

        ) from exc


    except GeminiGenerationError as exc:

        raise HTTPException(

            status_code=502,

            detail=str(exc)

        ) from exc


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                f"Unexpected generation error: {exc}"
            )

        ) from exc


# ============================================================
# EXPORT DOCUMENT
# ============================================================

@router.post("/export")
def export_document(
    request: ExportRequest
):

    try:

        terms = request.terms


        # ----------------------------------------------------
        # TXT
        # ----------------------------------------------------

        if request.format == "txt":

            payload = format_txt(
                request.text
            )

            media_type = (
                "text/plain; charset=utf-8"
            )

            filename = (
                "legalease-document.txt"
            )


        # ----------------------------------------------------
        # DOCX
        # ----------------------------------------------------

        elif request.format == "docx":

            payload = format_docx(

                request.text,

                request.document_type,

                terms=terms,

                brand_name=request.brand_name,

                logo_path=(
                    str(LOGO_PATH)
                    if LOGO_PATH.exists()
                    else None
                ),
            )

            media_type = (
                "application/"
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            )

            filename = (
                "legalease-document.docx"
            )


        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        elif request.format == "pdf":

            payload = format_pdf(

                request.text,

                request.document_type,

                terms=terms,

                brand_name=request.brand_name,

            )

            media_type = (
                "application/pdf"
            )

            filename = (
                "legalease-document.pdf"
            )


        # ----------------------------------------------------
        # INVALID FORMAT
        # ----------------------------------------------------

        else:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Unsupported export format: "
                    f"{request.format}"
                )
            )


        # ----------------------------------------------------
        # RETURN FILE
        # ----------------------------------------------------

        return Response(

            content=payload,

            media_type=media_type,

            headers={

                "Content-Disposition":
                    (
                        'attachment; '
                        f'filename="{filename}"'
                    )
            }
        )


    except HTTPException:

        raise


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                f"{request.format.upper()} "
                f"export failed: {exc}"
            )

        ) from exc


# ============================================================
# EXAMPLE
# ============================================================

@router.get("/example")
def example_request():

    terms = [

        "Payment within 30 days of invoice",

        "Confidentiality must be maintained",

        "Either party may terminate with 15 days notice",
    ]


    return {

        "document_type":
            "Freelance Work Contract",

        "parties":
            "Jane Doe (Service Provider), "
            "TechNova Inc. (Client)",

        "terms":
            "; ".join(terms),

        "dates":
            "2026-10-02",

        "jurisdiction":
            "Not specified",

        "language":
            "English",

        "brand_name":
            "LegalEase",
    }