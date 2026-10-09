"""
Script to generate fictional demo PDFs for ProofMind AI testing and demonstration.
"""
import os
import fitz  # PyMuPDF

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

def create_pdf(filename: str, pages_content: list[dict]):
    filepath = os.path.join(DEMO_DIR, filename)
    doc = fitz.open()
    
    for page_idx, page_info in enumerate(pages_content):
        page = doc.new_page(width=595, height=842) # A4
        title = page_info.get("title", "")
        header = page_info.get("header", "OAKFIELD UNIVERSITY • ACADEMIC AFFAIRS")
        body_sections = page_info.get("sections", [])
        
        # Insert header
        page.insert_text((50, 40), header, fontsize=9, color=(0.4, 0.4, 0.4))
        page.draw_line((50, 48), (545, 48), color=(0.7, 0.7, 0.7), width=0.8)
        
        # Insert title
        page.insert_text((50, 80), title, fontsize=16, fontname="helv", color=(0.1, 0.1, 0.2))
        
        y = 110
        for sec in body_sections:
            sec_title = sec.get("title", "")
            if sec_title:
                page.insert_text((50, y), sec_title, fontsize=12, fontname="helv", color=(0.15, 0.25, 0.5))
                y += 18
            
            paragraphs = sec.get("text", [])
            for para in paragraphs:
                rect = fitz.Rect(50, y, 545, y + 100)
                rc = page.insert_textbox(rect, para, fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2), align=0)
                y += 55
                if y > 760:
                    break
        
        # Insert footer with page number
        page.draw_line((50, 800), (545, 800), color=(0.8, 0.8, 0.8), width=0.5)
        page.insert_text((50, 815), f"Document: {filename} | Effective: Academic Year 2024-2025", fontsize=8, color=(0.5, 0.5, 0.5))
        page.insert_text((490, 815), f"Page {page_idx + 1} of {len(pages_content)}", fontsize=8, color=(0.5, 0.5, 0.5))
        
    doc.save(filepath)
    doc.close()
    print(f"Created: {filepath}")

def generate_all_demo_files():
    # 1. Policy A: General Undergraduate Scholarship Policy 2024
    create_pdf(
        "Policy_A_General_Scholarship_2024.pdf",
        [
            {
                "title": "Oakfield General Undergraduate Scholarship Policy 2024",
                "header": "OAKFIELD UNIVERSITY • FINANCIAL AID OFFICE",
                "sections": [
                    {
                        "title": "1. Purpose and Scope",
                        "text": [
                            "This policy defines the continuing eligibility criteria for undergraduate students awarded the Oakfield General University Scholarship. All matriculated scholarship recipients must satisfy these baseline requirements each term."
                        ]
                    },
                    {
                        "title": "2. Academic Standing & GPA Requirements",
                        "text": [
                            "Recipients are required to maintain a cumulative Grade Point Average (GPA) of 3.00 or higher on a 4.00 grading scale. Academic standing is audited at the conclusion of each spring semester."
                        ]
                    },
                    {
                        "title": "3. Mandatory Attendance Policy (General Regulation)",
                        "text": [
                            "Section 3.1 Attendance Threshold: Students receiving the General University Scholarship must maintain a minimum attendance rate of 75% across all registered lecture and laboratory courses throughout the academic semester.",
                            "Failure to maintain the 75% minimum attendance threshold without an authorized medical waiver will result in immediate suspension of scholarship disbursements for the subsequent term."
                        ]
                    }
                ]
            },
            {
                "title": "Policy A: Verification & Appeal Procedures",
                "header": "OAKFIELD UNIVERSITY • FINANCIAL AID OFFICE",
                "sections": [
                    {
                        "title": "4. Attendance Auditing",
                        "text": [
                            "Departmental registrars report attendance logs bi-weekly. Students falling between 70% and 74.9% may submit an extenuating circumstances petition to the Dean of Students within 14 calendar days."
                        ]
                    },
                    {
                        "title": "5. Relationship to Departmental Riders",
                        "text": [
                            "Where general university guidelines conflict with standard financial aid rules, this general policy serves as the default administrative framework unless a specific program rider explicitly supersedes it."
                        ]
                    }
                ]
            }
        ]
    )

    # 2. Policy B: STEM Honors Scholarship Rider 2024
    create_pdf(
        "Policy_B_STEM_Honors_Rider_2024.pdf",
        [
            {
                "title": "STEM Honors Special Program Scholarship Rider 2024",
                "header": "OAKFIELD UNIVERSITY • DIVISION OF SCIENCES & ENGINEERING",
                "sections": [
                    {
                        "title": "1. Program Authorization & Scope",
                        "text": [
                            "This policy rider applies specifically to all students enrolled in degree programs within the STEM Division (Physics, Chemistry, Computer Science, Engineering, Mathematics) who receive specialized institutional endowment funding."
                        ]
                    },
                    {
                        "title": "2. Rigorous Performance Standards",
                        "text": [
                            "Section 2.4 Honors Attendance Mandate: For all students designated under the STEM Honors Program or majoring in accredited STEM disciplines with departmental award status, the minimum mandatory attendance requirement is 80% per term.",
                            "Attendance is calculated continuously across both theoretical lectures and practical laboratory sessions. The standard institutional threshold of 75% is superseded by this 80% benchmark for STEM scholars."
                        ]
                    },
                    {
                        "title": "3. Enforcement & Probation",
                        "text": [
                            "Any STEM scholar whose term attendance rate falls below 80% is automatically placed on departmental scholarship probation. If the attendance is not raised above 80% within the next reporting cycle, the scholarship stipend is revoked."
                        ]
                    }
                ]
            }
        ]
    )

    # 3. Student Record Alex Rivera (Attendance 78%)
    create_pdf(
        "Student_Record_Alex_Rivera.pdf",
        [
            {
                "title": "Official Student Academic Profile: Alex Rivera",
                "header": "OAKFIELD UNIVERSITY • OFFICE OF THE REGISTRAR",
                "sections": [
                    {
                        "title": "1. Student Identification & Program",
                        "text": [
                            "Student Name: Alex Rivera | Student ID: STU-94821 | Academic Year: 2024-2025\nAcademic Degree Program: Bachelor of Science in Physics (Division of Natural Sciences)\nScholarship Status: Institutional Scholar (Oakfield Undergraduate Award recipient)."
                        ]
                    },
                    {
                        "title": "2. Fall 2024 Academic Performance & Metrics",
                        "text": [
                            "Cumulative GPA: 3.65 / 4.00 (Honor Roll Status)\nTotal Credit Hours Enrolled: 16 credit units\nCumulative Term Attendance Record: 78.0% verified by electronic course check-in logs.",
                            "Course Breakdown: PHYS-301 (82% attendance), MATH-250 (79% attendance), CHEM-210 (74% attendance), PHYS-315L (77% attendance). Aggregate Semester Attendance: 78.0%."
                        ]
                    },
                    {
                        "title": "3. Administrative Notes",
                        "text": [
                            "Record Note: Student is enrolled in a STEM major (Physics). Student file does not specify whether the award contract is governed solely under the General Scholarship Agreement or if the STEM Honors Rider was signed."
                        ]
                    }
                ]
            }
        ]
    )

    # 4. Policy Standard Merit Scholarship 2024 (Non-conflicting)
    create_pdf(
        "Policy_Standard_Merit_2024.pdf",
        [
            {
                "title": "Oakfield Standard Merit Scholarship Regulations 2024",
                "header": "OAKFIELD UNIVERSITY • SCHOLARSHIP COMMITTEE",
                "sections": [
                    {
                        "title": "1. Overview & Guidelines",
                        "text": [
                            "The Standard Merit Scholarship is awarded to students demonstrating academic excellence in humanities and general studies.",
                            "Section 1.3 Baseline Criteria: Recipients must maintain a minimum cumulative GPA of 3.00 and achieve an overall attendance rate of at least 75% in all scheduled courses."
                        ]
                    },
                    {
                        "title": "2. Maintenance of Award",
                        "text": [
                            "Students meeting or exceeding the 75% attendance threshold and 3.00 GPA are automatically certified for renewal for the next academic year without conditional reviews."
                        ]
                    }
                ]
            }
        ]
    )

    # 5. Student Record Jordan Lee (Attendance 88%, Supported Case)
    create_pdf(
        "Student_Record_Jordan_Lee.pdf",
        [
            {
                "title": "Official Student Academic Profile: Jordan Lee",
                "header": "OAKFIELD UNIVERSITY • OFFICE OF THE REGISTRAR",
                "sections": [
                    {
                        "title": "1. Student Profile & Enrollment",
                        "text": [
                            "Student Name: Jordan Lee | Student ID: STU-88204 | Academic Year: 2024-2025\nMajor: Bachelor of Arts in English Literature\nScholarship Award: Standard Merit Scholarship."
                        ]
                    },
                    {
                        "title": "2. Fall 2024 Performance Record",
                        "text": [
                            "Cumulative GPA: 3.82 / 4.00 (Dean's List)\nTerm Attendance Rate: 88.0% across all enrolled seminars and lectures.",
                            "Audit Result: Attendance (88.0%) exceeds the required 75% standard merit threshold. GPA (3.82) satisfies all academic excellence provisions."
                        ]
                    }
                ]
            }
        ]
    )

if __name__ == "__main__":
    generate_all_demo_files()
