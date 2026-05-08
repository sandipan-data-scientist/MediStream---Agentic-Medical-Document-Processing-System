# File: api/main.py

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from app.graph import run_pipeline

app = FastAPI(
    title="MediStream API",
    description="Automated medical document extraction, coding, and formatting pipeline.",
    version="1.0.0"
)


class PipelineResponse(BaseModel):
    status: str
    reviewer_verdict: str
    xml_path: str
    xlsx_path: str
    validation_issues: list[str]
    timeline_event_count: int


@app.post("/process", response_model=PipelineResponse)
async def process_document(file: UploadFile = File(...)):
    """
    Accepts a PDF, image, or text file and runs the full MediStream pipeline.
    Returns paths to the generated XML and Excel files.
    """

    file_bytes = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        file_type = "pdf"
    elif filename.endswith((".jpg", ".jpeg", ".png")):
        file_type = "image"
    else:
        file_type = "text"

    try:
        final_state = run_pipeline(file_bytes, file_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    all_issues = []
    for log in final_state.validation_logs:
        all_issues.extend(log.issues_found)

    return PipelineResponse(
        status="completed",
        reviewer_verdict=final_state.reviewer_verdict or "no_review",
        xml_path=final_state.output_xml_path or "",
        xlsx_path=final_state.output_xlsx_path or "",
        validation_issues=all_issues,
        timeline_event_count=len(final_state.chronological_timeline)
    )


@app.get("/download/xml")
async def download_xml(path: str):
    """Download a generated XML file by its path."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/xml", filename=os.path.basename(path))


@app.get("/download/xlsx")
async def download_xlsx(path: str):
    """Download a generated Excel file by its path."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(path)
    )


@app.get("/health")
async def health():
    return {"status": "ok"}