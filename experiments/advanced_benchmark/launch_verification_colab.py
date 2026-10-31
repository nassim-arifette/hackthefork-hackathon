"""Run the CLI verification outside Jupyter's argument namespace."""
import subprocess
import sys

result = subprocess.run([sys.executable, '/content/verify_migration_colab.py'],
    capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
result.check_returncode()
