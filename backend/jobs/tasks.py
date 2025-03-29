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
from models import User, Quiz, QuizAttempt, Score

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
