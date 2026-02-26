import subprocess
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Commands to run in each terminal
project1_cmd = f'start cmd /k "cd /d {current_dir}\\main && venv\\Scripts\\activate && python manage.py runserver 8000"'
project2_cmd = f'start cmd /k "cd /d {current_dir}\\sub-main && venv\\Scripts\\activate && python manage.py runserver 5000"'

# Execute both commands
subprocess.Popen(project1_cmd, shell=True)
subprocess.Popen(project2_cmd, shell=True)

print("✅ Both servers started!")
print("📌 Project 1: http://127.0.0.1:8000")
print("📌 Project 2: http://127.0.0.1:5000")
print("\n⚠️  Close the terminal windows to stop the servers")