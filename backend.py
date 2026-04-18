import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib import colors

FILE_PATH = "QB FSD excel mixed.xlsx"

try:
    df = pd.read_excel(FILE_PATH)
except FileNotFoundError:
    print("❌ Excel file not found. Make sure it is in the same folder.")
    exit()
except Exception as e:
    print(f"❌ An error occurred while reading the Excel file: {e}")
    exit()

def select_questions(data, unit, marks, count):
    filtered = data[(data["Unit"] == unit) & (data["Marks"] == marks)]

    if len(filtered) < count:
        raise ValueError(f"Not enough {marks}-mark questions in {unit}")

    return filtered.sample(n=count)

def generate_60_marks(data):
    paper = []
    units = sorted(data["Unit"].unique())

    for unit in units:
        selected = select_questions(data, unit, 5, 2)
        paper.append((unit, selected))

    return paper

def generate_30_marks(data):
    paper = []

    u1 = pd.concat([
        select_questions(data, "Unit 1", 3, 1),
        select_questions(data, "Unit 1", 4, 1)
    ])
    paper.append(("Unit 1", u1))

    u2 = select_questions(data, "Unit 2", 4, 2)
    paper.append(("Unit 2", u2))

    u3 = pd.concat([
        select_questions(data, "Unit 3", 3, 1),
        select_questions(data, "Unit 3", 4, 1)
    ])
    paper.append(("Unit 3", u3))

    u4 = select_questions(data, "Unit 4", 4, 2)
    paper.append(("Unit 4", u4))

    return paper

def generate_pdf(paper, subject, semester, total_marks):
    filename = f"{subject}_{total_marks}_Marks_Paper.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=12,
        leading=14
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading3'],
        fontSize=12,
        leading=14,
        spaceBefore=10,
        spaceAfter=5
    )
    normal_style = styles['Normal']
    right_align_style = ParagraphStyle(
        'RightAlign',
        parent=normal_style,
        alignment=TA_RIGHT
    )

    # 1. Header Section
    elements.append(Paragraph("<b>Pimpri Chinchwad College of Engineering</b>", title_style))
    elements.append(Paragraph("Department of Artificial Intelligence & Machine Learning", subtitle_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Horizontal Line
    line_table = Table([['']], colWidths=[7.0*inch])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 0.2 * inch))
    
    # 2. Meta Information Table
    # Calculate Time based on marks
    time_str = "2.5 Hours" if total_marks == 60 else "1.0 Hour"
    
    meta_data = [
        [f"Subject: {subject}", f"Semester: {semester}"],
        [f"Time: {time_str}", f"Maximum Marks: {total_marks}"]
    ]
    
    meta_table = Table(meta_data, colWidths=[3.5*inch, 3.5*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.2 * inch))
    
    # 3. Instructions
    instructions = [
        "<b>Instructions:</b>",
        "1. All questions are compulsory.",
        "2. Figures to the right indicate full marks.",
        "3. Assume suitable data if necessary."
    ]
    
    # Create instructions box
    inst_content = []
    for line in instructions:
        inst_content.append(Paragraph(line, normal_style))
    
    # Wrapped in a table for border
    # Using a single cell table containing the list of paragraphs
    inst_table = Table([[inst_content]], colWidths=[7.0*inch])
    inst_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black), # Box border
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(inst_table)
    elements.append(Spacer(1, 0.3 * inch))

    # 4. Questions
    q_number = 1

    for unit_data in paper:
        # Check if input is the old list-of-tuples format or new dict format
        if isinstance(unit_data, tuple):
            unit, questions = unit_data
            elements.append(Paragraph(f"<b>{unit}</b>", heading_style))
            elements.append(Spacer(1, 0.1 * inch))
            
            for _, row in questions.iterrows():
                q_text = f"Q{q_number}. {row['Question']}"
                marks_text = f"[{row['Marks']} Marks]"
                
                # Question Table: Text (Left) | Marks (Right)
                q_table_data = [[Paragraph(q_text, normal_style), Paragraph(marks_text, right_align_style)]]
                q_table = Table(q_table_data, colWidths=[6.0*inch, 1.0*inch])
                q_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                
                elements.append(q_table)
                elements.append(Spacer(1, 0.1 * inch))
                q_number += 1
        else:
            # Dict format from session
            unit = unit_data['unit']
            questions = unit_data['questions']
            elements.append(Paragraph(f"<b>{unit}</b>", heading_style))
            elements.append(Spacer(1, 0.1 * inch))
            
            for q in questions:
                q_text = f"Q{q_number}. {q['question']}"
                marks_text = f"[{q['marks']} Marks]"
                
                # Question Table: Text (Left) | Marks (Right)
                q_table_data = [[Paragraph(q_text, normal_style), Paragraph(marks_text, right_align_style)]]
                q_table = Table(q_table_data, colWidths=[6.0*inch, 1.0*inch])
                q_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                
                elements.append(q_table)
                elements.append(Spacer(1, 0.1 * inch))
                q_number += 1

    doc.build(elements)
    print(f"\n✅ {filename} generated successfully!")
    return filename

def convert_to_serializable(paper):
    """Converts the pandas-based paper structure to a JSON-serializable list of dicts."""
    paper_structure = []
    for unit, questions in paper:
        q_list = []
        for _, row in questions.iterrows():
            q_list.append({
                "question": row['Question'],
                "marks": row['Marks']
            })
        paper_structure.append({
            "unit": unit,
            "questions": q_list
        })
    return paper_structure

def main():

    while True:

        print("\nAvailable Subjects:")
        subjects = df["Subject"].unique()

        for s in subjects:
            print("-", s)

        subject = input("\nEnter subject exactly as shown (or type exit): ")

        if subject.lower() == "exit":
            print("👋 Exiting program.")
            break

        subject_data = df[df["Subject"] == subject]

        if subject_data.empty:
            print("❌ Subject not found!")
            continue

        try:
            if subject_data["Marks"].max() == 5:
                paper = generate_60_marks(subject_data)
                generate_pdf(paper, subject, "Semester 1", 60)
            else:
                paper = generate_30_marks(subject_data)
                generate_pdf(paper, subject, "Semester 1", 30)

        except ValueError as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
