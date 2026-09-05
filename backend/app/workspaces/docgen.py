"""
Deterministic Academic DOCX Report Generator for Study Pilot.
Consumes workspace source files, evidence screenshots, metadata, and raw Moodle instructions.
Zero AI/LLM dependencies; 100% deterministic local generation.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from sqlmodel import Session

from ..config import WORKSPACES_DIR
from ..models import MoodleActivity, Course, SystemSetting
from .service import WorkspaceService, slugify, clean_course_code


def set_cell_background(cell, fill_hex: str):
    """Set background color of a docx table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for a table cell (values in dxa: 20 dxa = 1 pt)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tc_mar.append(node)
    tc_pr.append(tc_mar)


class DocumentGenerator:
    @staticmethod
    def generate_report(activity_id: str, session: Session) -> Dict[str, Any]:
        """
        Generate a standardized university lab/assignment deliverable in DOCX format.
        Consumes:
          - raw Moodle instructions (from instructions.md or database)
          - files in src/
          - screenshots in evidence/
          - student and course metadata
        """
        activity = session.get(MoodleActivity, activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        course = session.get(Course, activity.course_id)
        if not course:
            raise ValueError(f"Course {activity.course_id} not found")

        # Resolve student settings if configured
        student_name = "Student Name"
        student_roll = "Roll Number"
        try:
            from sqlmodel import select
            settings = session.exec(select(SystemSetting)).all()
            for s in settings:
                if s.key == "student_name" and s.value:
                    student_name = s.value
                elif s.key == "student_roll" and s.value:
                    student_roll = s.value
        except Exception:
            pass

        course_code = clean_course_code(course.short_name or course.full_name)

        # Ensure workspace exists
        if not activity.workspace_path:
            WorkspaceService.initialize_workspace(activity_id, session)
            session.refresh(activity)

        workspace_dir = WORKSPACES_DIR / activity.workspace_path
        if not workspace_dir.exists():
            raise FileNotFoundError(f"Workspace path {workspace_dir} not found on disk")

        src_dir = workspace_dir / "src"
        evidence_dir = workspace_dir / "evidence"
        output_dir = workspace_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Document
        doc = docx.Document()

        # Page setup: Standard Letter, 1-inch margins
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # Base Palette
        navy_color = RGBColor(0x0F, 0x29, 0x42)  # #0f2942
        slate_color = RGBColor(0x47, 0x55, 0x69) # #475569

        # ==========================================
        # 1. Institutional Header & Title Block
        # ==========================================
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_before = Pt(0)
        title_p.paragraph_format.space_after = Pt(4)
        run_course = title_p.add_run(f"{course.full_name.upper()} ({course_code})\n")
        run_course.font.size = Pt(11)
        run_course.font.bold = True
        run_course.font.color.rgb = slate_color

        run_title = title_p.add_run(activity.title)
        run_title.font.size = Pt(22)
        run_title.font.bold = True
        run_title.font.color.rgb = navy_color

        # Metadata Table
        meta_table = doc.add_table(rows=2, cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_table.autofit = True

        cells = meta_table.rows[0].cells
        p0 = cells[0].paragraphs[0]
        r0 = p0.add_run("Student Name: ")
        r0.bold = True
        p0.add_run(student_name)

        p1 = cells[1].paragraphs[0]
        r1 = p1.add_run("Roll Number: ")
        r1.bold = True
        p1.add_run(student_roll)

        cells2 = meta_table.rows[1].cells
        p2 = cells2[0].paragraphs[0]
        r2 = p2.add_run("Due Date: ")
        r2.bold = True
        p2.add_run(activity.due_date.strftime("%B %d, %Y - %I:%M %p") if activity.due_date else "N/A")

        p3 = cells2[1].paragraphs[0]
        r3 = p3.add_run("Generated: ")
        r3.bold = True
        p3.add_run(datetime.now(timezone.utc).strftime("%B %d, %Y"))

        for row in meta_table.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.space_before = Pt(2)
                    for r in p.runs:
                        r.font.size = Pt(9.5)

        # Horizontal separator
        div_p = doc.add_paragraph()
        div_p.paragraph_format.space_before = Pt(8)
        div_p.paragraph_format.space_after = Pt(16)
        div_run = div_p.add_run("―" * 48)
        div_run.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)

        # ==========================================
        # 2. Section: Problem Statement & Objectives
        # ==========================================
        h1 = doc.add_heading("1. Problem Statement & Lab Objectives", level=1)
        h1.paragraph_format.space_before = Pt(12)
        h1.paragraph_format.space_after = Pt(6)

        # Check raw instructions
        instr_md_path = workspace_dir / "instructions.md"
        raw_instructions = activity.description_text
        if instr_md_path.exists():
            try:
                lines = instr_md_path.read_text(encoding="utf-8").split("## Instructions & Brief")
                if len(lines) > 1 and lines[1].strip():
                    raw_instructions = lines[1].strip()
            except Exception:
                pass

        if raw_instructions and raw_instructions.strip():
            for line in raw_instructions.splitlines():
                line_str = line.strip()
                if line_str:
                    p = doc.add_paragraph(line_str)
                    p.paragraph_format.space_after = Pt(4)
                    p.paragraph_format.line_spacing = 1.15
        else:
            p = doc.add_paragraph("Refer to the official Moodle portal activity for specific instructions.")
            p.italic = True

        # ==========================================
        # 3. Section: Implementation & Source Code
        # ==========================================
        h2 = doc.add_heading("2. Implementation & Source Code", level=1)
        h2.paragraph_format.space_before = Pt(16)
        h2.paragraph_format.space_after = Pt(6)

        code_extensions = [".cpp", ".c", ".h", ".hpp", ".py", ".java", ".sql", ".md", ".txt"]
        found_code_files: List[Path] = []
        if src_dir.exists():
            for f in sorted(src_dir.rglob("*")):
                if f.is_file() and f.suffix.lower() in code_extensions:
                    found_code_files.append(f)

        if found_code_files:
            for code_file in found_code_files:
                rel_name = code_file.relative_to(workspace_dir)
                subh = doc.add_paragraph()
                subh.paragraph_format.space_before = Pt(10)
                subh.paragraph_format.space_after = Pt(2)
                subh_run = subh.add_run(f"Listing: {rel_name}")
                subh_run.bold = True
                subh_run.font.size = Pt(10)

                # Code listing box (single-cell shaded table)
                table = doc.add_table(rows=1, cols=1)
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                table.autofit = False

                cell = table.cell(0, 0)
                cell.width = Inches(6.5)
                set_cell_background(cell, "F8FAFC")  # slate-50 light background
                set_cell_margins(cell, top=120, bottom=120, left=160, right=160)

                code_p = cell.paragraphs[0]
                code_p.paragraph_format.space_before = Pt(0)
                code_p.paragraph_format.space_after = Pt(0)
                code_p.paragraph_format.line_spacing = 1.05

                code_content = code_file.read_text(encoding="utf-8", errors="replace")
                code_run = code_p.add_run(code_content)
                code_run.font.name = "Consolas"
                code_run.font.size = Pt(9.0)
                code_run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        else:
            p = doc.add_paragraph("No source code files located in src/ directory.")
            p.italic = True

        # ==========================================
        # 4. Section: Execution Evidence & Results
        # ==========================================
        h3 = doc.add_heading("3. Execution Evidence & Output", level=1)
        h3.paragraph_format.space_before = Pt(16)
        h3.paragraph_format.space_after = Pt(6)

        image_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"]
        found_evidence_images: List[Path] = []
        if evidence_dir.exists():
            for f in sorted(evidence_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in image_extensions:
                    found_evidence_images.append(f)

        if found_evidence_images:
            for idx, img_file in enumerate(found_evidence_images, 1):
                img_p = doc.add_paragraph()
                img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                img_p.paragraph_format.space_before = Pt(8)
                img_p.paragraph_format.space_after = Pt(4)

                try:
                    # Embed image, fit to max 5.8 inches width
                    doc.add_picture(str(img_file), width=Inches(5.8))
                    
                    cap_p = doc.add_paragraph()
                    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cap_p.paragraph_format.space_after = Pt(12)
                    cap_run = cap_p.add_run(f"Figure {idx}: Execution Screenshot ({img_file.name})")
                    cap_run.font.size = Pt(9.0)
                    cap_run.italic = True
                    cap_run.font.color.rgb = slate_color
                except Exception as e:
                    err_p = doc.add_paragraph(f"[Could not render image {img_file.name}: {e}]")
                    err_p.italic = True
        else:
            note_p = doc.add_paragraph(
                "[No execution screenshots found in evidence/ directory. Place test captures or waveform diagrams in the evidence/ folder to automatically embed them.]"
            )
            note_p.italic = True
            note_p.paragraph_format.space_after = Pt(8)

        # ==========================================
        # 5. Section: Observations & Conclusions
        # ==========================================
        h4 = doc.add_heading("4. Observations & Conclusions", level=1)
        h4.paragraph_format.space_before = Pt(16)
        h4.paragraph_format.space_after = Pt(6)

        conc_p = doc.add_paragraph(
            "The deliverables specified in this assignment were implemented, verified, and documented in accordance with the course requirements."
        )
        conc_p.paragraph_format.space_after = Pt(12)

        # Save Document to output/
        clean_title = slugify(activity.title, max_length=30)
        report_filename = f"{clean_title}_Report.docx"
        report_path = output_dir / report_filename

        doc.save(str(report_path))

        # Update activity workspace status
        activity.workspace_status = "completed"
        session.add(activity)
        session.commit()
        session.refresh(activity)

        return {
            "success": True,
            "activity_id": activity.id,
            "filename": report_filename,
            "relative_path": str(report_path.relative_to(WORKSPACES_DIR)).replace("\\", "/"),
            "absolute_path": str(report_path),
            "file_size_bytes": report_path.stat().st_size,
            "images_embedded": len(found_evidence_images),
            "code_files_embedded": len(found_code_files),
        }
