from functools import wraps

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
import os
from datetime import datetime

from extensions import cache, db
from models import Chapter, Question, Quiz, Subject, User, QuizAttempt, Score
from jobs.tasks import export_user_quiz_statistics, export_quiz_statistics

# Define Blueprint
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

### 1️⃣ Admin Role Checker Decorator ###
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        
        # Check if user has admin role in database
        user = User.query.get(user_id)
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
            
        return fn(*args, **kwargs)
    return wrapper

### 2️⃣ Admin Dashboard - Welcome Endpoint ###
@admin_bp.route("/statistics", methods=["GET"])
@admin_required
@cache.cached(timeout=300, key_prefix='admin_statistics')  # Cache for 5 minutes
def get_dashboard_statistics():
    # Get counts of various entities
    total_users = User.query.filter_by(role="user").count()
    total_admins = User.query.filter_by(role="admin").count()
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_quizzes = Quiz.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5)
    recent_users_data = [{
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "joined": user.created_at.strftime("%Y-%m-%d")
    } for user in recent_users]

    # Get quiz statistics
    quiz_stats = db.session.query(
        Quiz.id,
        Quiz.date_of_quiz,
        db.func.count(QuizAttempt.id).label('total_attempts'),
        db.func.avg(Score.total_score).label('avg_score')
    ).select_from(Quiz).outerjoin(QuizAttempt).outerjoin(Score).group_by(Quiz.id).limit(5).all()

    quiz_stats_data = [{
        "quiz_id": stat.id,
        "date": stat.date_of_quiz.strftime("%Y-%m-%d") if stat.date_of_quiz else None,
        "total_attempts": int(stat.total_attempts),
        "avg_score": round(float(stat.avg_score if stat.avg_score else 0), 2)
    } for stat in quiz_stats]

    # Get subject-wise chapter counts
    subject_stats = db.session.query(
        Subject.name,
        db.func.count(Chapter.id).label('chapter_count')
    ).outerjoin(Chapter).group_by(Subject.id).all()

    subject_stats_data = [{
        "subject": stat.name,
        "chapters": int(stat.chapter_count)
    } for stat in subject_stats]

    return jsonify({
        "overview": {
            "total_users": total_users,
            "total_admins": total_admins,
            "total_subjects": total_subjects,
            "total_chapters": total_chapters,
            "total_quizzes": total_quizzes
        },
        "recent_users": recent_users_data,
        "quiz_statistics": quiz_stats_data,
        "subject_statistics": subject_stats_data
    }), 200

# ➤ Update User
@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    data = request.json
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update user fields if provided in request
    if "name" in data:
        user.full_name = data["name"]
    if "email" in data:
        # Check if email already exists for another user
        existing_user = User.query.filter(User.email == data["email"], User.id != user_id).first()
        if existing_user:
            return jsonify({"error": "Email already in use"}), 400
        user.email = data["email"]

    try:
        db.session.commit()
        return jsonify({
            "message": "User updated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": user.role
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update user"}), 500


@admin_bp.route("/users", methods=["GET"])
@admin_required
@cache.cached(timeout=600, key_prefix='admin_all_users')
def get_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "email": user.email, "name": user.full_name, "role": user.role} for user in users]), 200


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    return jsonify({"message": "Welcome to the Admin Dashboard"}), 200


### 3️⃣ CRUD Operations ###

# ➤ Create Subject
@admin_bp.route("/subjects", methods=["POST"])
@admin_required
def create_subject():
    data = request.json
    name = data.get("name")
    description = data.get("description", "")

    if not name:
        return jsonify({"error": "Subject name is required"}), 400

    subject = Subject(name=name, description=description)
    db.session.add(subject)
    db.session.commit()
    
    # Clear subject caches
    cache.delete('all_subjects')
    
    return jsonify({"message": "Subject created successfully", "subject_id": subject.id}), 201


# ➤ Get All Subjects
@admin_bp.route("/subjects", methods=["GET"])
@admin_required
@cache.cached(timeout=300, key_prefix='admin_subjects')  # Cache for 5 minutes
def get_subjects():
    subjects = Subject.query.all()
    return jsonify([{"id": s.id, "name": s.name, "description": s.description} for s in subjects]), 200


# ➤ Update Subject
@admin_bp.route("/subjects/<int:subject_id>", methods=["PUT"])
@admin_required
def update_subject(subject_id):
    data = request.json
    subject = Subject.query.get(subject_id)

    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    subject.name = data.get("name", subject.name)
    subject.description = data.get("description", subject.description)

    db.session.commit()
    
    # Clear subject caches
    cache.delete('all_subjects')
    cache.delete('admin_subjects')
    
    # Clear related quiz caches
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    for chapter in chapters:
        cache.delete(f'subject_quizzes_{subject_id}')
    
    return jsonify({"message": "Subject updated successfully"}), 200


# ➤ Delete Subject
@admin_bp.route("/subjects/<int:subject_id>", methods=["DELETE"])
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)

    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    db.session.delete(subject)
    db.session.commit()
    
    # Clear subject caches
    cache.delete('all_subjects')
    cache.delete('admin_subjects')
    cache.delete(f'subject_quizzes_{subject_id}')
    
    return jsonify({"message": "Subject deleted successfully"}), 200


# ➤ Create Chapter Under a Subject
@admin_bp.route("/subjects/<int:subject_id>/chapters", methods=["POST"])
@admin_required
def create_chapter(subject_id):
    data = request.json
    name = data.get("name")
    description = data.get("description", "")

    if not name:
        return jsonify({"error": "Chapter name is required"}), 400

    chapter = Chapter(name=name, subject_id=subject_id,
                      description=description)
    db.session.add(chapter)
    db.session.commit()
    
    # Clear related caches
    cache.delete(f'subject_chapters_{subject_id}')
    cache.delete('admin_statistics')
    
    return jsonify({"message": "Chapter created successfully", "chapter_id": chapter.id}), 201


# ➤ Get Chapters of a Subject
@admin_bp.route("/subjects/<int:subject_id>/chapters", methods=["GET"])
@admin_required
@cache.cached(timeout=1800, key_prefix=lambda: f'subject_chapters_{request.view_args["subject_id"]}')  # Cache for 30 minutes
def get_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in chapters]), 200


# ➤ Create Quiz Under a Chapter
@admin_bp.route("/chapters/<int:chapter_id>/quizzes", methods=["POST"])
@admin_required
def create_quiz(chapter_id):
    data = request.json
    time_duration = data.get("time_duration", 30)  # Default 30 minutes
    remarks = data.get("remarks", "")

    quiz = Quiz(chapter_id=chapter_id,
                time_duration=time_duration, remarks=remarks)
    db.session.add(quiz)
    db.session.commit()
    
    # Clear related caches
    chapter = Chapter.query.get(chapter_id)
    if chapter:
        cache.delete(f'subject_quizzes_{chapter.subject_id}')
    cache.delete(f'chapter_quizzes_{chapter_id}')
    cache.delete('admin_statistics')
    
    return jsonify({"message": "Quiz created successfully", "quiz_id": quiz.id}), 201


# ➤ Get Quizzes Under a Chapter
@admin_bp.route("/chapters/<int:chapter_id>/quizzes", methods=["GET"])
@admin_required
@cache.cached(timeout=300, key_prefix=lambda: f'chapter_quizzes_{request.view_args["chapter_id"]}')  # Cache for 5 minutes
def get_quizzes(chapter_id):
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return jsonify([{"id": q.id, "time_duration": q.time_duration, "remarks": q.remarks} for q in quizzes]), 200


# ➤ Create Question Under a Quiz
@admin_bp.route("/quizzes/<int:quiz_id>/questions", methods=["POST"])
@admin_required
def create_question(quiz_id):
    data = request.json
    options = data.get("options")
    question_text = data.get("text")
    option1 = options[0]
    option2 = options[1]
    option3 = options[2]
    option4 = options[3]
    correct_option = data.get("correct_option")

    print(quiz_id)

    print(question_text,"\n", option1, "\n", option2, "\n", option3, "\n", option4, "\n", correct_option)

    if not question_text or len(options) != 4:
        return jsonify({"error": "Missing required question data"}), 400


    question = Question(
        quiz_id=quiz_id,
        question_text=question_text,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=correct_option
    )
    db.session.add(question)
    db.session.commit()
    
    # Clear question cache
    cache.delete(f'quiz_questions_{quiz_id}')
    
    return jsonify({"message": "Question created successfully", "question_id": question.id}), 201


# ➤ Get Questions of a Quiz
@admin_bp.route("/quizzes/<int:quiz_id>/questions", methods=["GET"])
@admin_required
@cache.cached(timeout=1800, key_prefix=lambda: f'admin_quiz_questions_{request.view_args["quiz_id"]}')  # Cache for 30 minutes
def get_questions(quiz_id):
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return jsonify([{
        "id": q.id,
        "question_text": q.question_text,
        "option1": q.option1,
        "option2": q.option2,
        "option3": q.option3,
        "option4": q.option4,
        "correct_option": q.correct_option
    } for q in questions]), 200


# ➤ Update Question
@admin_bp.route("/questions/<int:question_id>", methods=["PUT"])
@admin_required
def update_question(question_id):
    data = request.json
    question = Question.query.get(question_id)

    if not question:
        return jsonify({"error": "Question not found"}), 404

    # Update fields
    if "question_text" in data:
        question.question_text = data["question_text"]
    if "option1" in data:
        question.option1 = data["option1"]
    if "option2" in data:
        question.option2 = data["option2"]
    if "option3" in data:
        question.option3 = data["option3"]
    if "option4" in data:
        question.option4 = data["option4"]
    if "correct_option" in data:
        question.correct_option = data["correct_option"]

    db.session.commit()
    
    # Clear question caches
    cache.delete(f'quiz_questions_{question.quiz_id}')
    cache.delete(f'admin_quiz_questions_{question.quiz_id}')
    
    return jsonify({"message": "Question updated successfully"}), 200


# ➤ Delete Question
@admin_bp.route("/questions/<int:question_id>", methods=["DELETE"])
@admin_required
def delete_question(question_id):
    question = Question.query.get(question_id)

    if not question:
        return jsonify({"error": "Question not found"}), 404

    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    
    # Clear question caches
    cache.delete(f'quiz_questions_{quiz_id}')
    cache.delete(f'admin_quiz_questions_{quiz_id}')
    
    return jsonify({"message": "Question deleted successfully"}), 200


# ➤ Update Quiz
@admin_bp.route("/quizzes/<int:quiz_id>", methods=["PUT"])
@admin_required
def update_quiz(quiz_id):
    data = request.json
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    quiz.time_duration = data.get("time_duration", quiz.time_duration)
    quiz.remarks = data.get("remarks", quiz.remarks)

    db.session.commit()
    
    # Clear related caches
    chapter = Chapter.query.get(quiz.chapter_id)
    if chapter:
        cache.delete(f'subject_quizzes_{chapter.subject_id}')
    cache.delete(f'chapter_quizzes_{quiz.chapter_id}')
    cache.delete(f'quiz_{quiz_id}')
    
    return jsonify({"message": "Quiz updated successfully"}), 200


# ➤ Delete Quiz
@admin_bp.route("/quizzes/<int:quiz_id>", methods=["DELETE"])
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    
    chapter_id = quiz.chapter_id
    chapter = Chapter.query.get(chapter_id)
    
    db.session.delete(quiz)
    db.session.commit()
    
    # Clear related caches
    if chapter:
        cache.delete(f'subject_quizzes_{chapter.subject_id}')
    cache.delete(f'chapter_quizzes_{chapter_id}')
    cache.delete(f'quiz_{quiz_id}')
    cache.delete(f'quiz_questions_{quiz_id}')
    cache.delete(f'admin_quiz_questions_{quiz_id}')
    cache.delete('admin_statistics')
    
    return jsonify({"message": "Quiz deleted successfully"}), 200


# ➤ Get User Quiz Attempts for Admin
@admin_bp.route("/users/<int:user_id>/attempts", methods=["GET"])
@admin_required
@cache.memoize(timeout=30)
def get_user_attempts(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
    attempts_data = []

    for attempt in attempts:
        try:
            quiz = Quiz.query.get(attempt.quiz_id)
            score_value = attempt.score.total_score if attempt.score else None

            attempts_data.append({
                "attempt_id": attempt.id,
                "quiz_id": attempt.quiz_id,
                "quiz_name": f"Quiz #{quiz.id}" if quiz else "Unknown",
                "start_time": attempt.start_time.strftime("%Y-%m-%d %H:%M") if attempt.start_time else None,
                "end_time": attempt.end_time.strftime("%Y-%m-%d %H:%M") if attempt.end_time else None,
                "score": score_value
            })
        except Exception as e:
            # Skip invalid attempts
            continue

    return jsonify(attempts_data), 200


# ➤ Search Users
@admin_bp.route("/search/users", methods=["GET"])
@admin_required
def search_users():
    query = request.args.get("q", "")
    if not query or len(query) < 2:
        return jsonify({"error": "Search query must be at least 2 characters"}), 400

    users = User.query.filter(
        (User.email.like(f"%{query}%")) |
        (User.full_name.like(f"%{query}%"))
    ).limit(10).all()

    return jsonify([{
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    } for user in users]), 200


# ➤ Search Subjects
@admin_bp.route("/search/subjects", methods=["GET"])
@admin_required
def search_subjects():
    query = request.args.get("q", "")
    if not query or len(query) < 2:
        return jsonify({"error": "Search query must be at least 2 characters"}), 400

    subjects = Subject.query.filter(
        Subject.name.like(f"%{query}%")
    ).limit(10).all()

    return jsonify([{
        "id": subject.id,
        "name": subject.name
    } for subject in subjects]), 200


# ➤ Search Quizzes
@admin_bp.route("/search/quizzes", methods=["GET"])
@admin_required
def search_quizzes():
    query = request.args.get("q", "")
    if not query or len(query) < 1:  # Allow searching by quiz ID, which might be just one digit
        return jsonify({"error": "Search query required"}), 400

    # Search by ID if the query is a number
    if query.isdigit():
        quizzes = Quiz.query.filter_by(id=int(query)).all()
    else:
        # Otherwise search by remarks
        quizzes = Quiz.query.filter(
            Quiz.remarks.like(f"%{query}%")
        ).limit(10).all()

    result = []
    for quiz in quizzes:
        chapter = Chapter.query.get(quiz.chapter_id)
        subject = Subject.query.get(chapter.subject_id) if chapter else None

        result.append({
            "id": quiz.id,
            "remarks": quiz.remarks,
            "chapter": chapter.name if chapter else "Unknown",
            "subject": subject.name if subject else "Unknown"
        })

    return jsonify(result), 200

### Export Endpoints ###

@admin_bp.route("/exports/users/trigger", methods=["POST"])
@admin_required
def trigger_user_export():
    """Trigger an asynchronous task to export user statistics to CSV"""
    try:
        # Launch the export task
        task = export_user_quiz_statistics.delay()
        
        return jsonify({
            "message": "User statistics export task started",
            "task_id": task.id,
            "status": "PENDING"
        }), 202
    except Exception as e:
        return jsonify({
            "error": f"Failed to start export task: {str(e)}"
        }), 500

@admin_bp.route("/exports/quizzes/trigger", methods=["POST"])
@admin_required
def trigger_quiz_export():
    """Trigger an asynchronous task to export quiz statistics to CSV"""
    try:
        # Launch the export task
        task = export_quiz_statistics.delay()
        
        return jsonify({
            "message": "Quiz statistics export task started",
            "task_id": task.id,
            "status": "PENDING"
        }), 202
    except Exception as e:
        return jsonify({
            "error": f"Failed to start export task: {str(e)}"
        }), 500

@admin_bp.route("/exports/status/<task_id>", methods=["GET"])
@admin_required
def get_export_status(task_id):
    """Check the status of an export task"""
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task.status,
    }
    
    if task.status == "SUCCESS":
        # If task completed successfully, include result info
        if task.result:
            response["result"] = task.result
    elif task.status == "FAILURE":
        # If task failed, include error info
        response["error"] = str(task.result) if task.result else "Unknown error"
    elif task.status == "PROGRESS" and task.info:
        # If task is in progress, include progress info
        response["progress"] = task.info
    
    return jsonify(response), 200

@admin_bp.route("/exports/download/<filename>", methods=["GET"])
@admin_required
def download_export(filename):
    """Download a generated export file"""
    try:
        export_dir = os.path.join(os.getcwd(), 'exports')
        file_path = os.path.join(export_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "Export file not found"}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype="text/csv"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500

@admin_bp.route("/exports/list", methods=["GET"])
@admin_required
def list_exports():
    """List all available export files"""
    try:
        export_dir = os.path.join(os.getcwd(), 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
            
        files = []
        for filename in os.listdir(export_dir):
            if filename.endswith('.csv'):
                # Get file stats
                file_path = os.path.join(export_dir, filename)
                file_stat = os.stat(file_path)
                
                # Determine export type
                export_type = "Unknown"
                if "user_quiz_statistics" in filename:
                    export_type = "User Statistics"
                elif "quiz_statistics" in filename:
                    export_type = "Quiz Statistics"
                
                files.append({
                    "filename": filename,
                    "type": export_type,
                    "size_bytes": file_stat.st_size,
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                })
                
        return jsonify({
            "exports": sorted(files, key=lambda x: x["created_at"], reverse=True)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to list export files: {str(e)}"}), 500
