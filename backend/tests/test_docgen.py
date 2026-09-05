import shutil
import pytest
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine
import docx

from app.models import Course, MoodleActivity
from app.workspaces.service import WorkspaceService
from app.workspaces.docgen import DocumentGenerator
from app.config import WORKSPACES_DIR


@pytest.fixture(name="test_session")
def fixture_test_session():
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_document_generator_deterministic(test_session: Session):
    course = Course(
        moodle_course_id="test_csc103",
        full_name="Object Oriented Programming",
        short_name="CSC-103",
        moodle_url="https://lms.shu.edu.pk/course/view.php?id=103",
        is_active=True,
    )
    test_session.add(course)
    test_session.commit()
    test_session.refresh(course)

    activity = MoodleActivity(
        course_id=course.id,
        moodle_item_id="item_docgen_1",
        title="Lab 03: Inheritance & Polymorphism",
        description_text="1. Create base class Shape.\n2. Inherit Circle and Rectangle.\n3. Compute Area.",
        activity_type="assignment",
        moodle_url="https://lms.shu.edu.pk/mod/assign/view.php?id=101",
        has_deadline=True,
    )
    test_session.add(activity)
    test_session.commit()
    test_session.refresh(activity)

    # Initialize workspace
    init_res = WorkspaceService.initialize_workspace(activity.id, test_session)
    workspace_dir = Path(init_res["absolute_path"])

    try:
        # Add a custom code file in src/
        custom_code = """#include <iostream>
class Shape { public: virtual double area() = 0; };
"""
        (workspace_dir / "src" / "shape.cpp").write_text(custom_code, encoding="utf-8")

        # Add a mock 1x1 png image in evidence/
        # Minimal valid 1x1 transparent PNG bytes
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff'
            b'?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        (workspace_dir / "evidence" / "shape_test.png").write_bytes(png_bytes)

        # Generate report
        report_res = DocumentGenerator.generate_report(activity.id, test_session)
        assert report_res["success"] is True
        assert report_res["images_embedded"] == 1
        assert report_res["code_files_embedded"] >= 1

        docx_path = Path(report_res["absolute_path"])
        assert docx_path.exists()
        assert docx_path.stat().st_size > 5000  # Non-trivial docx file

        # Open docx and verify content
        doc = docx.Document(str(docx_path))
        full_text = "\n".join([p.text for p in doc.paragraphs])
        assert "Lab 03: Inheritance & Polymorphism" in full_text
        assert "1. Problem Statement & Lab Objectives" in full_text
        assert "2. Implementation & Source Code" in full_text
        assert "3. Execution Evidence & Output" in full_text
        assert "4. Observations & Conclusions" in full_text

        # Verify activity status updated
        test_session.refresh(activity)
        assert activity.workspace_status == "completed"

    finally:
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)
