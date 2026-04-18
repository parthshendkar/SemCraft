from flask import Flask, render_template, send_file, jsonify, session, redirect, url_for, request
from dotenv import load_dotenv
import backend
import os
import secrets
import io

from supabase_service import SupabaseService

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'semcraft_secret_key')

supabase_service = SupabaseService()


def get_owner_token() -> str:
    if 'owner_token' not in session:
        session['owner_token'] = secrets.token_urlsafe(24)
    return session['owner_token']


def set_session_from_paper(paper_item: dict) -> None:
    session['paper_id'] = paper_item.get('id')
    session['department'] = paper_item.get('department')
    session['paper_data'] = paper_item.get('paper_data')
    session['pdf_file_path'] = paper_item.get('pdf_file_path')
    session['subject'] = paper_item.get('subject')
    session['semester'] = paper_item.get('semester')
    session['total_marks'] = paper_item.get('total_marks')

@app.route('/')
def home():
    feedback_items = supabase_service.get_recent_feedback(limit=6)
    return render_template('home.html', feedback_items=feedback_items)

@app.route('/generate')
def generate_page():
    owner_token = get_owner_token()
    history_items = supabase_service.get_papers_for_owner(owner_token, limit=10)

    return render_template('generate.html', generation_history=history_items)

@app.route('/preview', methods=['GET', 'POST'])
def preview_page(): 
    if request.method == 'POST':
        owner_token = get_owner_token()
        department = request.form.get('department', '').strip()
        subject = request.form.get('subject')
        semester = request.form.get('semester')

        if not department:
            return "Department is required", 400
        
        if not subject:
            return "Subject is required", 400

        subject_data = backend.df[backend.df["Subject"] == subject]

        if subject_data.empty:
            return "Subject not found", 404

        try:
            total_marks = 0
            # Generate paper using backend logic
            if subject_data["Marks"].max() == 5:
                paper_raw = backend.generate_60_marks(subject_data)
                total_marks = 60
            else:
                paper_raw = backend.generate_30_marks(subject_data)
                total_marks = 30
            
            # Convert to serializable format for session and display
            paper_data = backend.convert_to_serializable(paper_raw)

            created_paper = supabase_service.save_generated_paper(
                owner_token=owner_token,
                subject=subject,
                semester=semester,
                department=department,
                total_marks=total_marks,
                paper_data=paper_data,
            )

            if not created_paper:
                return "Failed to store generated paper in Supabase.", 500

            filename = backend.generate_pdf(paper_data, subject, semester, total_marks)
            file_path = os.path.join(os.getcwd(), filename)

            if os.path.exists(file_path):
                with open(file_path, 'rb') as pdf_file:
                    uploaded_pdf_path = supabase_service.upload_paper_pdf(
                        owner_token=owner_token,
                        paper_id=created_paper.get('id'),
                        filename=filename,
                        pdf_bytes=pdf_file.read(),
                    )
                if uploaded_pdf_path:
                    supabase_service.update_paper_pdf_path(owner_token, created_paper.get('id'), uploaded_pdf_path)
                    created_paper['pdf_file_path'] = uploaded_pdf_path

            created_paper['paper_data'] = paper_data
            set_session_from_paper(created_paper)
            
            return render_template('preview.html', 
                                 department=department,
                                 subject=subject, 
                                 semester=semester, 
                                 total_marks=total_marks, 
                                 paper=paper_data)
                                 
        except ValueError as e:
            return str(e), 400
        except Exception as e:
            return str(e), 500
            
    # On GET request, fetch latest paper only for this session owner token.
    owner_token = get_owner_token()
    paper_id = request.args.get('paper_id', '').strip()

    if paper_id:
        selected_paper = None
        try:
            db_paper_id = int(paper_id)
            selected_paper = supabase_service.get_paper_by_id_for_owner(owner_token, db_paper_id)
        except ValueError:
            selected_paper = None

        if selected_paper:
            set_session_from_paper(selected_paper)
            return render_template(
                'preview.html',
                department=session.get('department'),
                subject=session.get('subject'),
                semester=session.get('semester'),
                total_marks=session.get('total_marks'),
                paper=session.get('paper_data')
            )

    if owner_token and supabase_service.is_configured:
        latest_paper = supabase_service.get_latest_paper_for_owner(owner_token)
        if latest_paper:
            set_session_from_paper(latest_paper)

    if 'paper_data' in session:
        return render_template(
            'preview.html',
            department=session.get('department'),
            subject=session.get('subject'),
            semester=session.get('semester'),
            total_marks=session.get('total_marks'),
            paper=session.get('paper_data')
        )
    
    return redirect(url_for('generate_page'))

@app.route('/download')
def download_pdf():
    owner_token = get_owner_token()
    paper_id = request.args.get('paper_id', '').strip()

    if paper_id:
        selected_paper = None
        try:
            db_paper_id = int(paper_id)
            selected_paper = supabase_service.get_paper_by_id_for_owner(owner_token, db_paper_id)
        except ValueError:
            selected_paper = None

        if selected_paper:
            set_session_from_paper(selected_paper)

    if 'paper_data' not in session and owner_token and supabase_service.is_configured:
        latest_paper = supabase_service.get_latest_paper_for_owner(owner_token)
        if latest_paper:
            set_session_from_paper(latest_paper)

    if 'paper_data' not in session:
        return redirect(url_for('generate_page'))
        
    paper_data = session['paper_data']
    subject = session['subject']
    total_marks = session['total_marks']
    semester = session.get('semester', 'Unknown')
    pdf_file_path = session.get('pdf_file_path')
    paper_filename = f"{subject}_{total_marks}_Marks_Paper.pdf".replace(' ', '_')
    
    try:
        if pdf_file_path:
            pdf_bytes = supabase_service.download_paper_pdf(pdf_file_path)
            if pdf_bytes:
                return send_file(
                    io.BytesIO(pdf_bytes),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=paper_filename,
                )

        filename = backend.generate_pdf(paper_data, subject, semester, total_marks)
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            return "File creation failed", 500

        with open(file_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()

        session_paper_id = session.get('paper_id')
        if session_paper_id:
            uploaded_pdf_path = supabase_service.upload_paper_pdf(
                owner_token=owner_token,
                paper_id=session_paper_id,
                filename=filename,
                pdf_bytes=pdf_bytes,
            )
            if uploaded_pdf_path:
                supabase_service.update_paper_pdf_path(owner_token, session_paper_id, uploaded_pdf_path)
                session['pdf_file_path'] = uploaded_pdf_path

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=paper_filename,
        )
        
    except Exception as e:
        return str(e), 500

@app.route('/faq')
def faq_page():
    return render_template('faq.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback_page():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        prn = request.form.get('prn', '').strip()
        feedback = request.form.get('feedback', '').strip()

        if not all([name, department, prn, feedback]):
            return jsonify({"status": "error", "message": "All fields are required."}), 400

        try:
            result = supabase_service.save_feedback(
                name=name,
                department=department,
                prn=prn,
                feedback=feedback,
            )
            if not result.get("success"):
                return jsonify({"status": "error", "message": result.get("message", "Failed to store feedback in Supabase.")}), 500
            return jsonify({"status": "success", "message": result.get("message", "Feedback submitted successfully.")})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return render_template('feedback.html')

@app.route('/blog')
def blog_page():
    return render_template('blog.html')

@app.route('/developer')
def developer_page():
    return render_template('developer.html')

@app.route('/api/subjects')
def get_subjects():
    subjects = backend.df["Subject"].unique().tolist()
    return jsonify(subjects)
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
