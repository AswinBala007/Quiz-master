# from app import celery_app
from celery import shared_task
import time
import csv
import os
import io
import json
from datetime import datetime
from sqlalchemy import func
from flask import current_app
# Database imports
from models import User, Quiz, QuizAttempt, Score, Chapter, Subject

@shared_task(ignore_result=True)
def add(x, y):
    time.sleep(10)
    return x + y

@shared_task(ignore_result=True)
def sub(x, y):
    return x - y

@shared_task(bind=True)
def export_user_quiz_statistics(self):
    """
    Celery task to export user quiz statistics as CSV.
    This will create a CSV file with detailed information about users and their quiz performance.
    """
    from extensions import db  # Import here to avoid circular import
    
    # Create directory for exports if it doesn't exist
    export_dir = os.path.join(os.getcwd(), 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate a unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'user_quiz_statistics_{timestamp}.csv'
    filepath = os.path.join(export_dir, filename)
    
    # Set task status to in-progress
    self.update_state(state='PROGRESS', meta={'status': 'Processing data...'})
    
    try:
        # Fetch data: users with count of quizzes taken and average score
        query = db.session.query(
            User.id.label('user_id'),
            User.email.label('email'),
            User.full_name.label('full_name'),
            User.qualification.label('qualification'),
            User.created_at.label('registered_on'),
            User.last_login.label('last_login'),
            func.count(QuizAttempt.id).label('quizzes_taken'),
            func.avg(Score.total_score).label('average_score')
        ).outerjoin(
            QuizAttempt, User.id == QuizAttempt.user_id
        ).outerjoin(
            Score, QuizAttempt.id == Score.quiz_attempt_id
        ).filter(
            User.role == 'user'  # Only include regular users, not admins
        ).group_by(
            User.id
        ).all()
        
        # Write CSV file
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'User ID', 'Email', 'Full Name', 'Qualification', 
                'Registered On', 'Last Login', 'Quizzes Taken', 
                'Average Score (%)', 'Performance Level'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in query:
                # Calculate performance level based on average score
                avg_score = float(row.average_score or 0)
                if avg_score >= 80:
                    performance = 'Excellent'
                elif avg_score >= 60:
                    performance = 'Good'
                elif avg_score >= 40:
                    performance = 'Average'
                else:
                    performance = 'Needs Improvement'
                
                writer.writerow({
                    'User ID': row.user_id,
                    'Email': row.email,
                    'Full Name': row.full_name,
                    'Qualification': row.qualification or 'N/A',
                    'Registered On': row.registered_on.strftime('%Y-%m-%d') if row.registered_on else 'N/A',
                    'Last Login': row.last_login.strftime('%Y-%m-%d %H:%M') if row.last_login else 'Never',
                    'Quizzes Taken': row.quizzes_taken,
                    'Average Score (%)': f"{avg_score:.2f}" if row.average_score else 'N/A',
                    'Performance Level': performance
                })
        
        # Task completed successfully
        result = {
            'status': 'SUCCESS',
            'filename': filename,
            'path': filepath,
            'timestamp': timestamp,
            'record_count': len(query)
        }
        
        # Log to app if available
        return result
    
    except Exception as e:
        # Log error and return error state
        error_message = str(e)
        return {
            'status': 'ERROR',
            'error': error_message
        }

@shared_task(bind=True)
def export_quiz_statistics(self):
    """
    Export detailed statistics for all quizzes in the system.
    Includes quiz ID, name, subject, chapter, number of questions,
    total attempts, average score, etc.
    """
    from extensions import db  # Import here to avoid circular import
    
    # Create exports directory if it doesn't exist
    export_dir = os.path.join(os.getcwd(), 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'quiz_statistics_{timestamp}.csv'
    filepath = os.path.join(export_dir, filename)
    
    # Set task status to in-progress
    self.update_state(state='PROGRESS', meta={'status': 'Processing quiz data...'})
    
    try:
        # Query to fetch quiz statistics
        quiz_stats = db.session.query(
            Quiz.id.label('quiz_id'),
            Quiz.date_of_quiz.label('date'),
            Quiz.time_duration.label('duration'),
            func.count(QuizAttempt.id).label('total_attempts'),
            func.avg(Score.total_score).label('avg_score'),
            func.min(Score.total_score).label('min_score'),
            func.max(Score.total_score).label('max_score')
        ).outerjoin(
            QuizAttempt, Quiz.id == QuizAttempt.quiz_id
        ).outerjoin(
            Score, QuizAttempt.id == Score.quiz_attempt_id
        ).group_by(
            Quiz.id
        ).all()
        
        # Write to CSV
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'Quiz ID', 'Date', 'Duration (minutes)', 
                'Total Attempts', 'Average Score (%)',
                'Minimum Score (%)', 'Maximum Score (%)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for quiz in quiz_stats:
                writer.writerow({
                    'Quiz ID': quiz.quiz_id,
                    'Date': quiz.date.strftime('%Y-%m-%d') if quiz.date else 'Not scheduled',
                    'Duration (minutes)': quiz.duration,
                    'Total Attempts': quiz.total_attempts,
                    'Average Score (%)': f"{float(quiz.avg_score or 0):.2f}",
                    'Minimum Score (%)': f"{float(quiz.min_score or 0):.2f}" if quiz.min_score else 'N/A',
                    'Maximum Score (%)': f"{float(quiz.max_score or 0):.2f}" if quiz.max_score else 'N/A'
                })
        
        # Return success result
        return {
            'status': 'SUCCESS',
            'filename': filename,
            'path': filepath,
            'timestamp': timestamp,
            'record_count': len(quiz_stats)
        }
    
    except Exception as e:
        # Log error
        return {
            'status': 'ERROR',
            'error': str(e)
        }

@shared_task(bind=True)
def export_user_quiz_attempts(self, user_id):
    """
    Export all quizzes completed by a specific user.
    This will create a CSV file with details about each quiz attempt including
    quiz_id, chapter_id, subject, date, score, etc.
    """
    from extensions import db  # Import here to avoid circular import
    
    # Set task status to in-progress
    self.update_state(state='PROGRESS', meta={'status': 'Processing user quiz data...'})
    
    try:
        # Get user info for the filename
        user = User.query.get(user_id)
        if not user:
            return {
                'status': 'ERROR',
                'error': f'User with ID {user_id} not found'
            }
        
        # Fetch data: quizzes completed by the user with chapter and subject info
        quiz_attempts = db.session.query(
            QuizAttempt.id.label('attempt_id'),
            QuizAttempt.start_time.label('start_time'),
            QuizAttempt.end_time.label('end_time'),
            Quiz.id.label('quiz_id'),
            Quiz.date_of_quiz.label('date'),
            Quiz.time_duration.label('duration'),
            Quiz.remarks.label('quiz_remarks'),
            Chapter.id.label('chapter_id'),
            Chapter.name.label('chapter_name'),
            Subject.id.label('subject_id'),
            Subject.name.label('subject_name'),
            Score.total_score.label('score')
        ).join(
            Quiz, QuizAttempt.quiz_id == Quiz.id
        ).join(
            Chapter, Quiz.chapter_id == Chapter.id
        ).join(
            Subject, Chapter.subject_id == Subject.id
        ).outerjoin(  # Use outerjoin for Score as it might be null for in-progress attempts
            Score, QuizAttempt.id == Score.quiz_attempt_id
        ).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.end_time != None  # Only export completed attempts
        ).order_by(
            QuizAttempt.end_time.desc()  # Most recent first
        ).all()
        
        # Create directory for exports if it doesn't exist
        export_dir = os.path.join(os.getcwd(), 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'my_quiz_history_{user.email.split("@")[0]}_{timestamp}.csv'
        filepath = os.path.join(export_dir, filename)
        
        # Write CSV file
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'Quiz Attempt ID', 'Quiz ID', 'Subject', 'Chapter', 
                'Date Taken', 'Start Time', 'End Time', 
                'Duration (minutes)', 'Time Taken', 'Score (%)', 
                'Quiz Notes'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for attempt in quiz_attempts:
                # Calculate time taken in minutes
                time_taken = 'N/A'
                if attempt.start_time and attempt.end_time:
                    time_diff = attempt.end_time - attempt.start_time
                    time_taken = f"{int(time_diff.total_seconds() / 60)} minutes"
                
                writer.writerow({
                    'Quiz Attempt ID': attempt.attempt_id,
                    'Quiz ID': attempt.quiz_id,
                    'Subject': attempt.subject_name,
                    'Chapter': attempt.chapter_name,
                    'Date Taken': attempt.date.strftime('%Y-%m-%d') if attempt.date else 'Not scheduled',
                    'Start Time': attempt.start_time.strftime('%Y-%m-%d %H:%M') if attempt.start_time else 'N/A',
                    'End Time': attempt.end_time.strftime('%Y-%m-%d %H:%M') if attempt.end_time else 'In Progress',
                    'Duration (minutes)': attempt.duration,
                    'Time Taken': time_taken,
                    'Score (%)': attempt.score if attempt.score is not None else 'N/A',
                    'Quiz Notes': attempt.quiz_remarks or 'N/A'
                })
        
        # Task completed successfully
        result = {
            'status': 'SUCCESS',
            'filename': filename,
            'path': filepath,
            'timestamp': timestamp,
            'record_count': len(quiz_attempts),
            'user_email': user.email
        }
        
        return result
    
    except Exception as e:
        # Log error and return error state
        error_message = str(e)
        return {
            'status': 'ERROR',
            'error': error_message
        }