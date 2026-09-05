import os
import shutil
import pytest
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine
from app.models import Course, MoodleActivity
from app.workspaces.profiles import (
    get_all_profiles,
    get_profile,
    get_default_profile_for_course,
)
from app.workspaces.service import (
    WorkspaceService,
    clean_course_code,
    slugify,
)
from app.config import WORKSPACES_DIR


@pytest.fixture(name="test_session")
def fixture_test_session():
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_workflow_profiles():
    profiles = get_all_profiles()
    assert len(profiles) >= 6
    profile_ids = [p.id for p in profiles]
    assert "cpp_coding" in profile_ids
    assert "python_scripting" in profile_ids
    assert "digital_logic" in profile_ids
    assert "academic_writing" in profile_ids
    assert "linear_algebra" in profile_ids

    # Course defaults
    assert get_default_profile_for_course("CSC-103 (2601-1185) OOP").id == "cpp_coding"
    assert get_default_profile_for_course("CSC-210 Discrete Structures").id == "python_scripting"
    assert get_default_profile_for_course("ELE-205 Digital Logic Design").id == "digital_logic"
    assert get_default_profile_for_course("ENG-102 Expository Writing").id == "academic_writing"
    assert get_default_profile_for_course("MTH-208 Linear Algebra").id == "linear_algebra"
    assert get_default_profile_for_course("Unknown Course").id == "generic_lab"


def test_slugify_and_clean_course_code():
    assert clean_course_code("CSC-103 (2601-1185)") == "CSC-103"
    assert clean_course_code("ELE-205") == "ELE-205"
    assert clean_course_code("Linear Algebra") == "LINEAR-ALGEBRA"

    assert slugify("Lab 01: Classes & Objects") == "lab-01-classes-objects"
    assert slugify("Special !@#$%^&*() Characters") == "special-characters"


def test_workspace_initialization_and_preservation(test_session: Session):
    # Setup test course and activity
    course = Course(
        moodle_course_id="test_103",
        full_name="Object Oriented Programming",
        short_name="CSC-103 (2601-1185)",
        moodle_url="https://lms.shu.edu.pk/course/view.php?id=103",
        is_active=True,
    )
    test_session.add(course)
    test_session.commit()
    test_session.refresh(course)

    activity = MoodleActivity(
        course_id=course.id,
        moodle_item_id="item_9999",
        title="Lab 02: Operator Overloading",
        description_text="Write a Vector3 class with overloaded + and * operators.",
        description_html="<p>Write a <b>Vector3</b> class with overloaded + and * operators.</p>",
        activity_type="assignment",
        moodle_url="https://lms.shu.edu.pk/mod/assign/view.php?id=9999",
        has_deadline=True,
    )
    test_session.add(activity)
    test_session.commit()
    test_session.refresh(activity)

    # Initialize workspace
    result = WorkspaceService.initialize_workspace(
        activity_id=activity.id,
        session=test_session,
    )

    assert result["success"] is True
    workspace_dir = Path(result["absolute_path"])
    assert workspace_dir.exists()

    try:
        # Check subdirectories
        assert (workspace_dir / "src").is_dir()
        assert (workspace_dir / "evidence").is_dir()
        assert (workspace_dir / "output").is_dir()

        # Check starter C++ file
        cpp_main = workspace_dir / "src" / "main.cpp"
        assert cpp_main.exists()
        original_cpp_code = cpp_main.read_text(encoding="utf-8")
        assert "Vector3" not in original_cpp_code  # Starter code contains activity title

        # Check raw instructions files
        instr_md = workspace_dir / "instructions.md"
        assert instr_md.exists()
        assert "Write a Vector3 class" in instr_md.read_text(encoding="utf-8")

        instr_html = workspace_dir / "instructions.html"
        assert instr_html.exists()
        assert "<b>Vector3</b>" in instr_html.read_text(encoding="utf-8")

        # Check workspace.json
        meta_file = workspace_dir / "workspace.json"
        assert meta_file.exists()

        # Verify idempotency / user file preservation:
        # Simulate user writing their code
        modified_code = "// User's custom implementation\n#include <iostream>\nint main() { return 42; }"
        cpp_main.write_text(modified_code, encoding="utf-8")

        # Run initialize again
        reinit_result = WorkspaceService.initialize_workspace(
            activity_id=activity.id,
            session=test_session,
        )

        assert "src/main.cpp" in reinit_result["preserved_files"]
        assert cpp_main.read_text(encoding="utf-8") == modified_code  # NOT overwritten!

        # Check workspace info query
        info = WorkspaceService.get_workspace_info(activity.id, test_session)
        assert info["initialized"] is True
        assert "main.cpp" in info["src_files"]
        assert info["has_report"] is False

    finally:
        # Cleanup test workspace folder
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)


def test_launcher_path_security():
    from app.workspaces.launcher import validate_workspace_path, WindowsLauncher

    # Reject non-existent
    with pytest.raises(FileNotFoundError):
        validate_workspace_path(WORKSPACES_DIR / "non_existent_folder_xyz")

    # Reject outside workspace root
    with pytest.raises(ValueError, match="Security error"):
        validate_workspace_path(Path("C:/Windows"))

    # Valid folder within WORKSPACES_DIR
    test_folder = WORKSPACES_DIR / "test_sec_check"
    test_folder.mkdir(parents=True, exist_ok=True)
    try:
        validated = validate_workspace_path(test_folder)
        assert validated == test_folder.resolve()

        with pytest.raises(ValueError, match="Unsupported launcher tool"):
            WindowsLauncher.launch(test_folder, "unsupported_tool")
    finally:
        if test_folder.exists():
            shutil.rmtree(test_folder)
