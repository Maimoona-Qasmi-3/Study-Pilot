"""
Workflow profiles and starter templates for Study Pilot.
Defines course-specific and activity-specific workspace scaffolds.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowProfile(BaseModel):
    id: str = Field(description="Unique profile identifier")
    name: str = Field(description="Human-readable profile name")
    description: str = Field(description="Description of what this workflow is used for")
    category: str = Field(description="Category: coding, simulation, writing, math, generic")
    default_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Relative file paths mapped to default starter content"
    )


# Starter Template Definitions
CPP_MAIN = """/**
 * Course: {course_name} ({course_code})
 * Activity: {activity_title}
 * Student: [Your Name] | Roll No: [Your Roll No]
 * Date: {created_date}
 */

#include <iostream>

int main() {
    std::cout << "=== {activity_title} ===" << std::endl;
    // TODO: Implement your solution here
    return 0;
}
"""

CPP_MAKEFILE = """# Simple Makefile for {course_code} - {activity_title}
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
SRC = src/main.cpp
TARGET = output/app.exe

all: $(TARGET)

$(TARGET): $(SRC)
\t@mkdir -p output
\t$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

run: $(TARGET)
\t./$(TARGET)

clean:
\trm -f $(TARGET)
"""

PYTHON_MAIN = '''"""
Course: {course_name} ({course_code})
Activity: {activity_title}
Student: [Your Name] | Roll No: [Your Roll No]
Date: {created_date}
"""

def main():
    print("=== {activity_title} ===")
    # TODO: Implement your solution here


if __name__ == "__main__":
    main()
'''

DIGITAL_LOGIC_NOTES = """# Circuit Design & Simulation Notes

- **Course**: {course_name} ({course_code})
- **Activity**: {activity_title}
- **Date**: {created_date}

## 1. Circuit Specifications
- **Inputs**: 
- **Outputs**: 
- **IC / Gate Requirements**: 

## 2. Truth Table / State Table
| Input A | Input B | Output Y |
| :---: | :---: | :---: |
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

## 3. Boolean Equations & Simplification (K-Map)
$$Y = A \\cdot B$$

## 4. Simulation Instructions
- Open simulation software (Logisim / Proteus).
- Save project files into this `src/` directory.
- Capture waveform and circuit diagram screenshots into `evidence/`.
"""

ACADEMIC_WRITING_DRAFT = """# {activity_title}

**Course**: {course_name} ({course_code})  
**Author**: [Your Name]  
**Roll No**: [Your Roll No]  
**Date**: {created_date}  

---

## Abstract / Executive Summary
[Provide a concise 150-250 word summary of the paper's thesis and findings]

## 1. Introduction
- Background context
- Problem statement
- Objectives and scope

## 2. Literature Review / Theoretical Framework
- Core concepts and existing academic discourse

## 3. Analysis & Discussion
- Key arguments, case studies, or evaluation

## 4. Conclusion & Recommendations
- Summary of conclusions and prospective implications

---

## References
1. Author, A. (Year). *Title of work*. Publisher.
"""

LINEAR_ALGEBRA_SOLUTION = '''"""
Course: {course_name} ({course_code})
Activity: {activity_title}
Computational Solution & Matrix Verification
"""

import numpy as np

def solve():
    print("=== Linear Algebra Verification: {activity_title} ===")
    # Example Matrix definition:
    # A = np.array([[1, 2], [3, 4]], dtype=float)
    # print("Determinant:", np.linalg.det(A))
    # print("Eigenvalues:", np.linalg.eigvals(A))

if __name__ == "__main__":
    solve()
'''

GENERIC_LAB_NOTES = """# Lab Task: {activity_title}

- **Course**: {course_name} ({course_code})
- **Date**: {created_date}

## Objectives
- [ ] Review instructions in `instructions.md`
- [ ] Implement solution
- [ ] Capture evidence screenshots into `evidence/`
- [ ] Generate university deliverable

## Notes & Observations
[Document experimental observations and results here]
"""

GITIGNORE_CODE = """# Workspace temporary and build files
output/*.exe
output/*.out
output/*.o
__pycache__/
*.pyc
.DS_Store
Thumbs.db
"""

PROFILES: Dict[str, WorkflowProfile] = {
    "cpp_coding": WorkflowProfile(
        id="cpp_coding",
        name="C++ Programming",
        description="Scaffold for C++ object-oriented and systems programming with Makefile and clean output build",
        category="coding",
        default_files={
            "src/main.cpp": CPP_MAIN,
            "Makefile": CPP_MAKEFILE,
            ".gitignore": GITIGNORE_CODE,
        }
    ),
    "python_scripting": WorkflowProfile(
        id="python_scripting",
        name="Python Scripting & Solvers",
        description="Scaffold for Python algorithms, discrete structures, and data processing",
        category="coding",
        default_files={
            "src/main.py": PYTHON_MAIN,
            "requirements.txt": "# Add any project requirements here\n",
            ".gitignore": GITIGNORE_CODE,
        }
    ),
    "digital_logic": WorkflowProfile(
        id="digital_logic",
        name="Digital Logic Design (Circuits)",
        description="Scaffold for logic design, truth tables, K-map documentation, and circuit simulations",
        category="simulation",
        default_files={
            "src/circuit_notes.md": DIGITAL_LOGIC_NOTES,
            "evidence/README.md": "# Place circuit screenshots and waveform captures here\n",
            ".gitignore": GITIGNORE_CODE,
        }
    ),
    "academic_writing": WorkflowProfile(
        id="academic_writing",
        name="Academic Writing & Essay",
        description="Scaffold for academic essays, expository writing, and formal business reports",
        category="writing",
        default_files={
            "src/draft.md": ACADEMIC_WRITING_DRAFT,
            "evidence/README.md": "# Place supporting figures, graphs, or citations here\n",
        }
    ),
    "linear_algebra": WorkflowProfile(
        id="linear_algebra",
        name="Linear Algebra & Numerical Math",
        description="Scaffold for matrix operations, vector space calculations, and NumPy verification",
        category="math",
        default_files={
            "src/solution.py": LINEAR_ALGEBRA_SOLUTION,
            "src/notes.md": GENERIC_LAB_NOTES,
            ".gitignore": GITIGNORE_CODE,
        }
    ),
    "generic_lab": WorkflowProfile(
        id="generic_lab",
        name="General Lab Deliverable",
        description="Standard lab workspace suitable for any coursework or mixed task",
        category="generic",
        default_files={
            "src/notes.md": GENERIC_LAB_NOTES,
            "evidence/README.md": "# Save screenshots or test evidence in this directory\n",
            ".gitignore": GITIGNORE_CODE,
        }
    ),
}


def get_all_profiles() -> List[WorkflowProfile]:
    """Return all registered workflow profiles."""
    return list(PROFILES.values())


def get_profile(profile_id: str) -> Optional[WorkflowProfile]:
    """Retrieve a workflow profile by ID."""
    return PROFILES.get(profile_id)


def get_default_profile_for_course(course_code_or_name: str) -> WorkflowProfile:
    """
    Infer the default workflow profile based on course code or title.
    Can always be overridden at the individual activity level.
    """
    text = course_code_or_name.upper()
    if "CSC-103" in text or "OBJECT ORIENTED" in text or "OOP" in text:
        return PROFILES["cpp_coding"]
    if "CSC-210" in text or "DISCRETE" in text:
        return PROFILES["python_scripting"]
    if "ELE-205" in text or "DIGITAL LOGIC" in text or "DLD" in text:
        return PROFILES["digital_logic"]
    if "ENG-102" in text or "EXPOSITORY" in text or "WRITING" in text:
        return PROFILES["academic_writing"]
    if "MGT-302" in text or "ENTREPRENEURSHIP" in text or "MANAGEMENT" in text:
        return PROFILES["academic_writing"]
    if "MTH-208" in text or "LINEAR ALGEBRA" in text or "MATH" in text:
        return PROFILES["linear_algebra"]
    
    return PROFILES["generic_lab"]
