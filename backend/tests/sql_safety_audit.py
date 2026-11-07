"""SQL Injection Audit Script."""
import os
import re
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent

def audit_sql_safety():
    print("=" * 60)
    print("SQL SAFETY & PARAMETERIZATION AUDIT")
    print("=" * 60)
    
    issues = []
    py_files = list(backend_dir.glob('**/*.py'))
    
    for f in py_files:
        if 'venv' in str(f) or 'tests' in str(f):
            continue
        with open(f, 'r', encoding='utf-8') as fp:
            lines = fp.readlines()
            for idx, line in enumerate(lines, 1):
                # Check for execute(f"..." or execute(f'...'
                if re.search(r'cursor\.execute\(\s*f["\']', line) or re.search(r'\.execute\(query\s*\+', line):
                    # Check if it uses parameters
                    issues.append((f.relative_to(backend_dir), idx, line.strip()))
                    
    if not issues:
        print("PASS: No unsafe string concatenation found in cursor.execute calls.")
    else:
        print(f"FLAGGED: {len(issues)} potentially unsafe SQL executions:")
        for file, line_no, content in issues:
            print(f"  {file}:{line_no} -> {content}")
            
    print("=" * 60)

if __name__ == '__main__':
    audit_sql_safety()
