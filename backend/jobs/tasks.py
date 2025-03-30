# from app import celery_app
from celery import shared_task
import time
import csv
import os
import io
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, desc
from flask import current_app, render_template
# Database imports
from models import User, Quiz, QuizAttempt, Score, Chapter, Subject, UserPreference
import calendar

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

@shared_task(ignore_result = True)
def email_reminder(to, subject, content):
    """
    Send an email reminder.
    
    Args:
        to: Recipient's email address
        subject: Email subject
        content: Email content
    """
    # Create a simple text-only version
    html_content = f"<html><body>{content}</body></html>"
    send_html_email(to, subject, html_content, content)

@shared_task(bind=True)
def send_monthly_activity_report(self):
    """
    Celery task to generate and send monthly activity reports to all users.
    This task is scheduled to run on the 1st day of each month.
    Reports include quiz performance metrics for the previous month.
    """
    from extensions import db  # Import here to avoid circular import
    
    try:
        # Get the previous month's date range
        today = date.today()
        first_day_of_current_month = date(today.year, today.month, 1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = date(last_day_of_previous_month.year, last_day_of_previous_month.month, 1)
        
        # Month and year for the report
        report_month = calendar.month_name[last_day_of_previous_month.month]
        report_year = last_day_of_previous_month.year
        
        # Get all users with role 'user'
        users = User.query.filter_by(role='user').all()
        
        # Calculate average scores and rankings for all users for the previous month
        user_rankings = []
        for user in users:
            # Find all completed quiz attempts for this user in the previous month
            month_attempts = db.session.query(QuizAttempt).join(Score).filter(
                QuizAttempt.user_id == user.id,
                QuizAttempt.end_time != None,
                QuizAttempt.end_time >= first_day_of_previous_month,
                QuizAttempt.end_time <= last_day_of_previous_month
            ).all()
            
            # Calculate average score if there are attempts
            total_score = 0
            highest_score = 0
            
            if month_attempts:
                for attempt in month_attempts:
                    if attempt.score and attempt.score.total_score > highest_score:
                        highest_score = attempt.score.total_score
                    if attempt.score:
                        total_score += attempt.score.total_score
                
                avg_score = round(total_score / len(month_attempts), 1)
            else:
                avg_score = 0
            
            user_rankings.append({
                'user_id': user.id,
                'average_score': avg_score,
                'attempts': len(month_attempts)
            })
        
        # Sort users by average score to determine rankings
        user_rankings.sort(key=lambda x: x['average_score'], reverse=True)
        
        # Assign rankings
        rank = 1
        prev_score = None
        for i, user_rank in enumerate(user_rankings):
            if prev_score is not None and user_rank['average_score'] < prev_score:
                rank = i + 1
            user_rank['rank'] = rank
            prev_score = user_rank['average_score']
        
        # Create a lookup for quick rank retrieval
        ranking_lookup = {ur['user_id']: ur for ur in user_rankings}
        
        # Get the total number of active users who attempted a quiz in the past month
        total_active_users = db.session.query(func.count(func.distinct(QuizAttempt.user_id))).filter(
            QuizAttempt.end_time != None,
            QuizAttempt.end_time >= first_day_of_previous_month,
            QuizAttempt.end_time <= last_day_of_previous_month
        ).scalar()
        
        # Find new quizzes created in the last month
        new_quizzes = db.session.query(Quiz, Chapter, Subject).join(
            Chapter, Quiz.chapter_id == Chapter.id
        ).join(
            Subject, Chapter.subject_id == Subject.id
        ).filter(
            Quiz.date_of_quiz >= first_day_of_previous_month,
            Quiz.date_of_quiz <= last_day_of_previous_month
        ).all()
        
        # Format new quizzes for display
        formatted_new_quizzes = []
        for quiz, chapter, subject in new_quizzes:
            formatted_new_quizzes.append({
                'id': quiz.id,
                'subject': subject.name,
                'chapter': chapter.name
            })
        
        reports_sent = 0
        
        # Generate and send report for each user
        for user in users:
            # Skip users with no activity in the past month and no new quizzes
            if user.id not in ranking_lookup and not formatted_new_quizzes:
                continue
            
            # Get user's quiz attempts from the past month
            user_attempts = db.session.query(
                QuizAttempt, Quiz, Chapter, Subject, Score
            ).join(
                Quiz, QuizAttempt.quiz_id == Quiz.id
            ).join(
                Chapter, Quiz.chapter_id == Chapter.id
            ).join(
                Subject, Chapter.subject_id == Subject.id
            ).join(
                Score, QuizAttempt.id == Score.quiz_attempt_id
            ).filter(
                QuizAttempt.user_id == user.id,
                QuizAttempt.end_time != None,
                QuizAttempt.end_time >= first_day_of_previous_month,
                QuizAttempt.end_time <= last_day_of_previous_month
            ).order_by(
                QuizAttempt.end_time.desc()
            ).all()
            
            # Format the attempts for the template
            formatted_attempts = []
            subject_scores = {}
            
            for attempt, quiz, chapter, subject, score in user_attempts:
                formatted_attempts.append({
                    'date': attempt.end_time.strftime('%Y-%m-%d %H:%M'),
                    'subject': subject.name,
                    'chapter': chapter.name,
                    'score': score.total_score
                })
                
                # Track scores by subject for improvement recommendations
                if subject.name not in subject_scores:
                    subject_scores[subject.name] = []
                subject_scores[subject.name].append(score.total_score)
            
            # Identify subjects that need improvement (below 70% average)
            improvement_areas = []
            for subject, scores in subject_scores.items():
                subject_avg = sum(scores) / len(scores)
                if subject_avg < 70:
                    improvement_areas.append(subject)
            
            # Get user's ranking information
            user_ranking = ranking_lookup.get(user.id, {
                'average_score': 0,
                'attempts': 0,
                'rank': 'N/A'
            })
            
            # Prepare template context
            context = {
                'user': user,
                'report_month': report_month,
                'report_year': report_year,
                'total_attempts': user_ranking['attempts'],
                'average_score': user_ranking['average_score'],
                'highest_score': max([a['score'] for a in formatted_attempts]) if formatted_attempts else 0,
                'ranking': user_ranking['rank'] if user_ranking['attempts'] > 0 else None,
                'total_users': total_active_users,
                'quiz_attempts': formatted_attempts,
                'improvement': improvement_areas,
                'new_quizzes': formatted_new_quizzes
            }
            
            # Render the HTML and text versions of the email
            html_content = render_template('email/monthly_report.html', **context)
            text_content = render_template('email/monthly_report.txt', **context)
            
            # Send the report email
            subject = f"Your Quiz Master Activity Report - {report_month} {report_year}"
            
            # Send email with both HTML and text versions
            sent = send_html_email(user.email, subject, html_content, text_content)
            
            if sent:
                reports_sent += 1
        
        return {
            'status': 'SUCCESS',
            'reports_sent': reports_sent,
            'month': report_month,
            'year': report_year
        }
        
    except Exception as e:
        # Log error and return error state
        print(f"Error sending monthly reports: {str(e)}")
        return {
            'status': 'ERROR',
            'error': str(e)
        }

def send_html_email(email, subject, html_content, text_content):
    """
    Send an HTML email with a text fallback using SMTP (compatible with MailHog).
    
    Args:
        email: Recipient's email address
        subject: Email subject
        html_content: HTML content of the email
        text_content: Plain text version of the email
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # MailHog default configuration
        smtp_host = "localhost"
        smtp_port = 1025  # Default MailHog SMTP port
        sender_email = "quizmaster@example.com"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        
        # Attach text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        # The email client will try to render the last part first
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email using SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.sendmail(sender_email, email, msg.as_string())
            
        print(f"Monthly report email sent to {email} via MailHog")
        return True
    except Exception as e:
        print(f"Error sending HTML email: {str(e)}")
        return False