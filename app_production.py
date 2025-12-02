"""
SEMrush Data Processor - Production Flask Version
Enhanced with security and session management
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
import os
import tempfile
import shutil
import secrets
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from functools import wraps

from modules.data_processor import process_csv_files
from config.settings import config

app = Flask(__name__)

# Production-ready secret key
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configuration
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_MB * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/tmp/semrush_uploads')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(directory, max_age_hours=24):
    """Remove files older than max_age_hours from directory"""
    if not os.path.exists(directory):
        return
    
    now = datetime.now()
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        try:
            if os.path.isfile(item_path) or os.path.isdir(item_path):
                file_age = now - datetime.fromtimestamp(os.path.getmtime(item_path))
                if file_age > timedelta(hours=max_age_hours):
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    else:
                        shutil.rmtree(item_path)
        except Exception as e:
            print(f"Error cleaning up {item_path}: {str(e)}")


def generate_session_id():
    """Generate a unique session ID for user isolation"""
    return secrets.token_urlsafe(16)


@app.before_request
def before_request():
    """Initialize session and cleanup old files"""
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
    
    # Periodic cleanup (runs on each request, but checks timestamps)
    cleanup_old_files(app.config['UPLOAD_FOLDER'])
    cleanup_old_files(tempfile.gettempdir())


@app.route('/')
def index():
    return render_template('index.html', config=config)


@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        flash('No files selected')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files')
    
    if not files or all(file.filename == '' for file in files):
        flash('No files selected')
        return redirect(url_for('index'))
    
    # Validate file count
    if len(files) > 10:
        flash('Maximum 10 files allowed at once')
        return redirect(url_for('index'))
    
    # Get form parameters
    try:
        max_position = int(request.form.get('max_position', 11))
        if max_position < 1 or max_position > 100:
            flash('Position must be between 1 and 100')
            return redirect(url_for('index'))
    except ValueError:
        flash('Invalid position value')
        return redirect(url_for('index'))
    
    branded_terms = request.form.get('branded_terms', '').strip()
    
    # Parse branded terms
    branded_list = [term.strip() for term in branded_terms.split(',') if term.strip()] if branded_terms else []
    
    # Create session-specific upload directory
    session_id = session.get('session_id', generate_session_id())
    session_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    
    # Save and validate files
    valid_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to prevent collisions
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            filepath = os.path.join(session_upload_dir, unique_filename)
            file.save(filepath)
            valid_files.append(filepath)
        else:
            flash(f'Invalid file type: {file.filename}. Only CSV files allowed.')
    
    if not valid_files:
        flash('No valid CSV files to process')
        return redirect(url_for('index'))
    
    try:
        # Process the files
        file_objects = [open(filepath, 'rb') for filepath in valid_files]
        
        result_df = process_csv_files(file_objects, max_position, branded_list)
        
        # Close file objects
        for f in file_objects:
            f.close()
        
        # Clean up uploaded files immediately after processing
        for filepath in valid_files:
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing {filepath}: {str(e)}")
        
        # Clean up session upload directory if empty
        try:
            if os.path.exists(session_upload_dir) and not os.listdir(session_upload_dir):
                os.rmdir(session_upload_dir)
        except Exception as e:
            print(f"Error removing session directory: {str(e)}")

        if result_df is not None:
            # Create permanent downloads directory instead of temp
            downloads_dir = '/var/www/semrush-processor/downloads'
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Generate unique filename
            unique_id = secrets.token_urlsafe(16)
            filename = f'{unique_id}_semrush_processed.csv'
            output_path = os.path.join(downloads_dir, filename)
            
            # Save result to CSV
            result_df.to_csv(output_path, index=False)
            
            # Store filename in session (not full path for security)
            session['download_filename'] = filename
            
            # Calculate stats
            summary_stats = {
                'total_keywords': len(result_df),
                'total_traffic': int(result_df['traffic'].sum()) if 'traffic' in result_df.columns else 0,
                'unique_urls': result_df['url'].nunique() if 'url' in result_df.columns else 0,
                'files_processed': len(valid_files)
            }
            
            if 'branded' in result_df.columns:
                summary_stats['branded_keywords'] = int(result_df['branded'].sum())
                summary_stats['non_branded_keywords'] = int((~result_df['branded']).sum())
            
            return render_template(
                'results.html', 
                stats=summary_stats,
                filename=filename,  # ← Pass filename instead of temp_dir
                preview_data=result_df.head(config.PREVIEW_ROWS).to_html(
                    classes='table table-striped', 
                    table_id='preview-table'
                )
            )
        else:
            flash('Failed to process files. Please check the file format and required columns.')
            return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'Error processing files: {str(e)}')
        # Clean up on error
        for filepath in valid_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
        return redirect(url_for('index'))


@app.route('/download/<path:filename>')
def download_file(filename):
    # Security check: ensure filename is from this session
    session_filename = session.get('download_filename')
    if not session_filename or filename != session_filename:
        flash('File not found or access denied')
        return redirect(url_for('index'))
    
    # Build safe file path
    downloads_dir = '/var/www/semrush-processor/downloads'
    file_path = os.path.join(downloads_dir, filename)
    
    if not os.path.exists(file_path):
        flash('File not found')
        return redirect(url_for('index'))
    
    # Use X-Accel-Redirect for efficient file serving
    from flask import make_response
    response = make_response()
    response.headers['X-Accel-Redirect'] = f'/internal-downloads/{filename}'
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=semrush_processed.csv'
    
    # Schedule file cleanup after download
    # (Nginx will handle the actual file transfer)
    @response.call_on_close
    def cleanup():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if 'download_filename' in session:
                session.pop('download_filename')
        except Exception as e:
            print(f"Error cleaning up file: {str(e)}")
    
    return response


@app.errorhandler(413)
def too_large(e):
    flash(f'File too large. Maximum size is {config.MAX_FILE_SIZE_MB}MB')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(e):
    flash('An internal error occurred. Please try again.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Development mode
    app.run(debug=True, host='0.0.0.0', port=9000)