from datetime import datetime, timezone, timedelta
import json
import os

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import cache, db
from models import Chapter, Question, Quiz, QuizAttempt, Score, Subject, User
from jobs.tasks import export_user_quiz_attempts, send_conditional_daily_email, send_monthly_activity_report

user_bp = Blueprint('user', __name__, url_prefix='/user')

### 1️⃣ Fetch Available Subjects & Quizzes ###

@user_bp.route('/subjects', methods=['GET'])
@jwt_required()
@cache.cached(timeout=3600, key_prefix='all_subjects')  # Cache for 1 hour
def get_subjects():
    subjects = Subject.query.all()
    return jsonify([{"id": sub.id, "name": sub.name} for sub in subjects])


@user_bp.route('/quizzes/<int:subject_id>', methods=['GET'])
@jwt_required()
@cache.cached(timeout=900, key_prefix=lambda: f'subject_quizzes_{request.view_args["subject_id"]}')  # Cache for 15 minutes
def get_quizzes(subject_id):
    quizzes = Quiz.query.join(Chapter).filter(
        Chapter.subject_id == subject_id).all()
    return jsonify([{
        "id": quiz.id, 
        "date": quiz.date_of_quiz.strftime('%Y-%m-%d') if quiz.date_of_quiz else None, 
        "duration": quiz.time_duration
    } for quiz in quizzes])

### 2️⃣ Start a Quiz Attempt ###

@user_bp.route('/quiz/<int:quiz_id>/start', methods=['POST'])
@jwt_required()
def start_quiz_attempt(quiz_id):
    user_id = get_jwt_identity()
    
    # Check if quiz exists - use cached data if available
    quiz_cache_key = f'quiz_{quiz_id}'
    cached_quiz = None  # Simple cache instead of Redis
    
    if cached_quiz:
        quiz_data = json.loads(cached_quiz.decode('utf-8'))
        quiz_obj = type('Quiz', (), {
            'id': quiz_data['id'],
            'time_duration': quiz_data['time_duration']
        })
    else:
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({"error": "Quiz not found"}), 404
        
        # Cache the quiz data (using in-memory cache)
        quiz_data = {
            'id': quiz.id,
            'time_duration': quiz.time_duration
        }
        quiz_obj = quiz
    
    # Check if user already has an active attempt for this quiz
    active_attempt = QuizAttempt.query.filter_by(
        user_id=user_id, 
        quiz_id=quiz_id, 
        end_time=None
    ).first()
    
    if active_attempt:
        if active_attempt.start_time.tzinfo is None:
            active_attempt.start_time = active_attempt.start_time.replace(tzinfo=timezone.utc)
        # Calculate remaining time
        elapsed = datetime.now(timezone.utc) - active_attempt.start_time
        remaining_seconds = max(0, (quiz_obj.time_duration * 60) - elapsed.total_seconds())
        
        return jsonify({
            "message": "Quiz already started",
            "attempt_id": active_attempt.id,
            "remaining_seconds": remaining_seconds,
            "questions": get_quiz_questions_data(quiz_id)
        })
    
    # Create new attempt
    now = datetime.now(timezone.utc)
    quiz_attempt = QuizAttempt(
        user_id=user_id,
        quiz_id=quiz_id,
        start_time=now
    )
    db.session.add(quiz_attempt)
    db.session.commit()
    
    # Clear user history cache
    cache.delete_memoized(get_user_history, user_id)
    
    return jsonify({
        "message": "Quiz started",
        "attempt_id": quiz_attempt.id,
        "remaining_seconds": quiz_obj.time_duration * 60,
        "questions": get_quiz_questions_data(quiz_id)
    })

@cache.memoize(timeout=900)  # Cache for 15 minutes
def get_quiz_questions_data(quiz_id):
    # Check if questions are cached in Redis
    questions_cache_key = f'quiz_questions_{quiz_id}'
    cached_questions = None  # Simple cache instead of Redis
    
    if cached_questions:
        return json.loads(cached_questions.decode('utf-8'))
    
    # If not cached, fetch from database
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    result = [{
        "id": q.id, 
        "question": q.question_text,
        "options": [q.option1, q.option2, q.option3, q.option4]
    } for q in questions]
    
    # Cache the results (using SimpleCache)
    
    return result

### 3️⃣ Get Quiz Questions ###
@user_bp.route('/quiz/<int:quiz_id>', methods=['GET'])
@jwt_required()
def get_quiz_questions(quiz_id):
    user_id = get_jwt_identity()
    
    # Check if user has an active attempt
    active_attempt = QuizAttempt.query.filter_by(
        user_id=user_id, 
        quiz_id=quiz_id, 
        end_time=None
    ).first()
    
    if not active_attempt:
        return jsonify({"error": "No active quiz attempt found"}), 400
        
    # Check if time has expired
    quiz = Quiz.query.get(quiz_id)
    elapsed = datetime.now(timezone.utc) - active_attempt.start_time
    remaining_seconds = max(0, (quiz.time_duration * 60) - elapsed.total_seconds())
    
    if remaining_seconds <= 0:
        # Auto-submit with empty answers if time expired
        active_attempt.end_time = datetime.now(timezone.utc)
        db.session.commit()
        
        # Clear user history cache
        cache.delete_memoized(get_user_history, user_id)
        
        return jsonify({"error": "Quiz time has expired"}), 400
    
    questions = get_quiz_questions_data(quiz_id)
    return jsonify({
        "attempt_id": active_attempt.id,
        "remaining_seconds": remaining_seconds,
        "questions": questions
    })

### 4️⃣ Submit Quiz Attempt ###
@user_bp.route('/quiz/submit', methods=['POST'])
@jwt_required()
def submit_quiz_attempt():
    user_id = get_jwt_identity()
    data = request.json
    attempt_id = data.get('attempt_id')
    answers = data.get('answers', {})  # Format: {question_id: selected_option}

    if not attempt_id:
        return jsonify({"error": "Attempt ID required"}), 400

    # Get the attempt
    quiz_attempt = QuizAttempt.query.get(attempt_id)
    if not quiz_attempt:
        return jsonify({"error": "Quiz attempt not found"}), 404
        
    # Check if this attempt belongs to the current user
    if quiz_attempt.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    # Check if already submitted
    if quiz_attempt.end_time is not None:
        return jsonify({"error": "Quiz already submitted"}), 400
    
    # Check if time has expired
    quiz = Quiz.query.get(quiz_attempt.quiz_id)
    if quiz_attempt.start_time.tzinfo is None:
        quiz_attempt.start_time = quiz_attempt.start_time.replace(tzinfo=timezone.utc)
    elapsed = datetime.now(timezone.utc) - quiz_attempt.start_time
    if elapsed.total_seconds() > (quiz.time_duration * 60):
        # Time expired - give zero score
        quiz_attempt.end_time = datetime.now(timezone.utc)
        
        score = Score(
            quiz_attempt_id=quiz_attempt.id,
            user_id=user_id,
            total_score=0
        )
        db.session.add(score)
        db.session.commit()
        
        # Clear user history cache
        cache.delete_memoized(get_user_history, user_id)
        
        return jsonify({
            "message": "Quiz time expired",
            "score": 0
        }), 200

    # Set end time
    quiz_attempt.end_time = datetime.now(timezone.utc)
    
    # Calculate score
    correct_answers = 0
    total_questions = Question.query.filter_by(quiz_id=quiz_attempt.quiz_id).count()
    
    if total_questions == 0:
        total_questions = 1  # Avoid division by zero
    
    for qid, selected_option in answers.items():
        question = Question.query.get(int(qid))
        if question and int(selected_option-1) == question.correct_option:
            correct_answers += 1

    # Create score record
    score_value = int((correct_answers / total_questions) * 100)
    score = Score(
        quiz_attempt_id=quiz_attempt.id, 
        user_id=user_id,
        total_score=score_value
    )
    db.session.add(score)
    db.session.commit()
    
    # Clear user history cache
    cache.delete_memoized(get_user_history, user_id)

    return jsonify({
        "message": "Quiz submitted successfully", 
        "score": score_value,
        "correct": correct_answers,
        "total": total_questions
    })

### 5️⃣ Fetch User Quiz History ###

@user_bp.route('/history', methods=['GET'])
@jwt_required()
def get_user_history_route():
    user_id = get_jwt_identity()
    return jsonify(get_user_history(user_id))

@cache.memoize(timeout=300)  # Cache for 5 minutes
def get_user_history(user_id):
    attempts = QuizAttempt.query.filter_by(user_id=user_id).all()

    history = []
    for attempt in attempts:
        try:
            entry = {
                "quiz_id": attempt.quiz_id,
                "start_time": attempt.start_time.strftime('%Y-%m-%d %H:%M') if attempt.start_time else "N/A",
                "end_time": attempt.end_time.strftime('%Y-%m-%d %H:%M') if attempt.end_time else "In Progress",
                "score": attempt.score.total_score if attempt.score else "N/A"
            }
            history.append(entry)
        except Exception as e:
            # Skip any attempts with missing data
            continue

    return history

### 6️⃣ User Quiz Export Endpoints ###

@user_bp.route('/exports/quiz-history/trigger', methods=['POST'])
@jwt_required()
def trigger_quiz_history_export():
    """Trigger an asynchronous task to export the user's quiz history to CSV"""
    user_id = get_jwt_identity()
    
    try:
        # Launch the export task with the user's ID
        task = export_user_quiz_attempts.delay(user_id)
        
        return jsonify({
            "message": "Quiz history export started",
            "task_id": task.id,
            "status": "PENDING"
        }), 202
    except Exception as e:
        return jsonify({
            "error": f"Failed to start export: {str(e)}"
        }), 500

@user_bp.route('/exports/status/<task_id>', methods=['GET'])
@jwt_required()
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

@user_bp.route('/exports/download/<filename>', methods=['GET'])
@jwt_required()
def download_export(filename):
    """Download a generated export file"""
    user_id = get_jwt_identity()
    
    try:
        export_dir = os.path.join(os.getcwd(), 'exports')
        file_path = os.path.join(export_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "Export file not found"}), 404
        
        # Security check - only allow downloading files that contain the user's ID
        # or email in the filename to prevent accessing other users' exports
        user = User.query.get(user_id)
        user_identifier = user.email.split('@')[0]
        
        # Check if the filename contains the user identifier or user ID
        if not (user_identifier in filename or f"_{user_id}_" in filename):
            return jsonify({"error": "You don't have permission to access this file"}), 403
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype="text/csv"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500

@user_bp.route('/exports/list', methods=['GET'])
@jwt_required()
def list_exports():
    """List export files available for the current user"""
    user_id = get_jwt_identity()
    
    try:
        export_dir = os.path.join(os.getcwd(), 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
            
        files = []
        user = User.query.get(user_id)
        user_identifier = user.email.split('@')[0]
        
        for filename in os.listdir(export_dir):
            # Only include files that belong to this user (contain user ID or email prefix in name)
            if filename.endswith('.csv') and (user_identifier in filename or f"_{user_id}_" in filename):
                file_path = os.path.join(export_dir, filename)
                file_stat = os.stat(file_path)
                
                # Determine export type
                export_type = "Quiz History"
                
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

### 7️⃣ User Notification Preferences ###
# @user_bp.route('/preferences/notification', methods=['GET'])
# @jwt_required()
# def get_notification_preferences():
#     """Get the user's notification preferences."""
#     user_id = get_jwt_identity()
    
#     # Find or create user preferences
#     user_pref = UserPreference.query.filter_by(user_id=user_id).first()
    
#     if not user_pref:
#         # Create default preferences if not exist
#         user_pref = UserPreference(
#             user_id=user_id,
#             reminder_enabled=True,
#             reminder_time=datetime.now().time().replace(hour=18, minute=0, second=0, microsecond=0),
#             contact_method='email'
#         )
#         db.session.add(user_pref)
#         db.session.commit()
    
#     # Format the time as string
#     reminder_time_str = user_pref.reminder_time.strftime('%H:%M') if user_pref.reminder_time else '18:00'
    
#     return jsonify({
#         'reminder_enabled': user_pref.reminder_enabled,
#         'reminder_time': reminder_time_str,
#         'contact_method': user_pref.contact_method,
#         'contact_value': user_pref.contact_value
#     })

# @user_bp.route('/preferences/notification', methods=['PUT'])
# @jwt_required()
# def update_notification_preferences():
#     """Update the user's notification preferences."""
#     user_id = get_jwt_identity()
#     data = request.json
    
#     # Validate input
#     reminder_enabled = data.get('reminder_enabled', True)
#     reminder_time_str = data.get('reminder_time', '18:00')
#     contact_method = data.get('contact_method', 'email')
#     contact_value = data.get('contact_value', '')
    
#     # Validate time format
#     try:
#         hour, minute = map(int, reminder_time_str.split(':'))
#         reminder_time = datetime.time(hour=hour, minute=minute)
#     except (ValueError, TypeError):
#         return jsonify({'error': 'Invalid time format. Use HH:MM (24-hour format)'}), 400
    
#     # Validate contact method
#     if contact_method not in ['email', 'sms', 'gchat']:
#         return jsonify({'error': 'Invalid contact method. Use "email", "sms", or "gchat"'}), 400
    
#     # Find or create user preferences
#     user_pref = UserPreference.query.filter_by(user_id=user_id).first()
    
#     if not user_pref:
#         user_pref = UserPreference(user_id=user_id)
#         db.session.add(user_pref)
    
#     # Update preferences
#     user_pref.reminder_enabled = reminder_enabled
#     user_pref.reminder_time = reminder_time
#     user_pref.contact_method = contact_method
#     user_pref.contact_value = contact_value
#     user_pref.updated_at = datetime.now(timezone.utc)
    
#     db.session.commit()
    
#     return jsonify({
#         'message': 'Notification preferences updated successfully',
#         'reminder_enabled': user_pref.reminder_enabled,
#         'reminder_time': user_pref.reminder_time.strftime('%H:%M'),
#         'contact_method': user_pref.contact_method,
#         'contact_value': user_pref.contact_value
#     })

# @user_bp.route('/test-reminder', methods=['POST'])
# @jwt_required()
# def test_reminder():
#     """Send a test reminder to the user."""
#     user_id = get_jwt_identity()
    
#     # Get the user
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({'error': 'User not found'}), 404
    
#     # Get the user's preferences
#     user_pref = UserPreference.query.filter_by(user_id=user_id).first()
#     if not user_pref:
#         # Create default preferences if not exist
#         user_pref = UserPreference(
#             user_id=user_id,
#             reminder_enabled=True,
#             reminder_time=datetime.now().time().replace(hour=18, minute=0, second=0, microsecond=0),
#             contact_method='email'
#         )
#         db.session.add(user_pref)
#         db.session.commit()
    
#     # Craft a test message
#     message = (
#         f"Hello {user.full_name},\n\n"
#         f"This is a test reminder from Quiz Master.\n"
#         f"Your notification preferences are set to receive reminders at "
#         f"{user_pref.reminder_time.strftime('%H:%M')} "
#         f"via {user_pref.contact_method}.\n\n"
#         f"If you received this message, your notification settings are working correctly."
#     )
    
#     # Send the notification
#     success = send_notification(user, user_pref, message)
    
#     if success:
#         return jsonify({'message': 'Test reminder sent successfully'})
#     else:
#         return jsonify({'error': 'Failed to send test reminder'}), 500

@user_bp.route('/test-monthly-report', methods=['POST'])
@jwt_required()
def test_monthly_report():
    """Generate and send a test monthly activity report to the current user."""
    user_id = get_jwt_identity()
    
    # Check if the user is authorized
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Start the task to generate and send the report
    task = send_monthly_activity_report.delay()
    
    return jsonify({
        'message': 'Monthly report generation started',
        'task_id': task.id
    })

@user_bp.route('/test-daily-reminder', methods=['POST'])
@jwt_required()
def test_daily_reminder():
    """Generate and send a test daily reminder to the current user."""
    user_id = get_jwt_identity()

    # Check if the user is authorized
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Start the task to generate and send the report
    task = send_conditional_daily_email.delay()  
    return jsonify({
        'message': 'Daily reminder generation started',
        'task_id': task.id
    })