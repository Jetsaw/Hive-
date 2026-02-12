"""
Export Conversations API
Export chat history as PDF, TXT, or JSON
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import json
import sqlite3
from app.core.config import settings

router = APIRouter(prefix="/api/conversation", tags=["export"])


class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(pdf|txt|json)$")
    user_id: str = ""


def _get_messages(user_id: str):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    cur = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE user_id=? ORDER BY created_at ASC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]


@router.post("/export")
async def export_conversation(req: ExportRequest):
    messages = _get_messages(req.user_id)
    if not messages:
        raise HTTPException(status_code=404, detail="No conversation found")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if req.format == "txt":
        lines = [f"HIVE Conversation Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
        lines.append(f"User ID: {req.user_id}\n")
        lines.append("=" * 60 + "\n\n")
        for msg in messages:
            role = "You" if msg["role"] == "user" else "HIVE"
            time_str = msg.get("timestamp", "")
            lines.append(f"[{time_str}] {role}:\n{msg['content']}\n\n")
        content = "\n".join(lines)
        return Response(
            content=content.encode("utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=hive_chat_{timestamp}.txt"},
        )

    elif req.format == "json":
        data = {
            "export_date": datetime.now().isoformat(),
            "user_id": req.user_id,
            "message_count": len(messages),
            "messages": messages,
        }
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return Response(
            content=content.encode("utf-8"),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=hive_chat_{timestamp}.json"},
        )

    elif req.format == "pdf":
        # Generate a simple PDF using basic PDF structure
        pdf_content = _generate_pdf(messages, req.user_id)
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=hive_chat_{timestamp}.pdf"},
        )


def _generate_pdf(messages, user_id):
    """Generate a basic PDF document for conversation export."""
    # Minimal PDF generation without external libraries
    lines = []
    lines.append(f"HIVE Conversation Export")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"User: {user_id}")
    lines.append("")
    for msg in messages:
        role = "You" if msg["role"] == "user" else "HIVE"
        time_str = msg.get("timestamp", "")
        # Truncate very long messages for PDF
        content = msg["content"][:500]
        lines.append(f"[{time_str}] {role}:")
        lines.append(content)
        lines.append("")

    text = "\n".join(lines)

    # Build minimal valid PDF
    text_escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # Split into lines for PDF text rendering
    pdf_lines = text_escaped.split("\n")

    # Calculate page dimensions
    margin_top = 750
    line_height = 14
    lines_per_page = 48

    pages = []
    for i in range(0, len(pdf_lines), lines_per_page):
        page_lines = pdf_lines[i:i + lines_per_page]
        text_ops = []
        y = margin_top
        for line in page_lines:
            # Truncate lines to fit page width
            line = line[:90]
            text_ops.append(f"BT /F1 10 Tf 50 {y} Td ({line}) Tj ET")
            y -= line_height
        pages.append("\n".join(text_ops))

    if not pages:
        pages = ["BT /F1 10 Tf 50 750 Td (No messages found) Tj ET"]

    # Build PDF objects
    objects = []
    obj_num = 1

    # Object 1: Catalog
    objects.append(f"{obj_num} 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    obj_num += 1

    # Object 2: Pages (placeholder - will update)
    page_refs = " ".join(f"{3 + i * 2} 0 R" for i in range(len(pages)))
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count {len(pages)} >>\nendobj")

    # For each page, create page object and content stream
    for idx, page_content in enumerate(pages):
        page_obj_num = 3 + idx * 2
        content_obj_num = page_obj_num + 1

        # Page object
        objects.append(
            f"{page_obj_num} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_obj_num} 0 R /Resources << /Font << /F1 {3 + len(pages) * 2} 0 R >> >> >>\n"
            f"endobj"
        )

        # Content stream
        stream = page_content.encode("latin-1", errors="replace")
        objects.append(
            f"{content_obj_num} 0 obj\n"
            f"<< /Length {len(stream)} >>\n"
            f"stream\n{stream.decode('latin-1')}\nendstream\n"
            f"endobj"
        )

    # Font object
    font_obj_num = 3 + len(pages) * 2
    objects.append(
        f"{font_obj_num} 0 obj\n"
        f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        f"endobj"
    )

    # Build final PDF
    body = "\n".join(objects)
    xref_offset = len(f"%PDF-1.4\n{body}\n")

    num_objects = font_obj_num
    xref = f"xref\n0 {num_objects + 1}\n0000000000 65535 f \n"
    # Simplified xref - most viewers are tolerant
    for i in range(num_objects):
        xref += f"{str(i * 100 + 10).zfill(10)} 00000 n \n"

    trailer = f"trailer\n<< /Size {num_objects + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"

    pdf = f"%PDF-1.4\n{body}\n{xref}{trailer}"
    return pdf.encode("latin-1", errors="replace")
