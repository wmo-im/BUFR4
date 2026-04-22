
# This script checks Table B and Table D files modified in a pull request.
# It ensures all FXY/FXY1 values are in the format FXXYYY, where XX is in the range 0–47 and YYY is in the range 0–191.

import re
import sys
import csv
import subprocess


def get_changed_files():
    """Get list of changed files."""
    result = subprocess.run(
        ['git', 'diff', '--name-only', 'origin/master..HEAD'],
        capture_output=True,
        text=True,
        check=True
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def get_changed_lines(changed_file):
    """Get changed line numbers by tracking modified rows in new file."""
    changed_file = changed_file.strip().replace('\\', '/')
    result = subprocess.run(
        ['git', 'diff', '--unified=0', 'origin/master..HEAD', '--', changed_file],
        capture_output=True,
        text=True,
        check=True
    )

    changed_lines = set()
    current_line = None
    
    for line in result.stdout.splitlines():
        # Parse hunk headers (new-file side)
        hunk_match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            continue

        if current_line is None:
            continue

        if line.startswith('+') and not line.startswith('+++'):
            if re.search(r',\d{6}[,]', line):
                changed_lines.add(current_line)
            current_line += 1
        elif line.startswith(' ') and not line.startswith('@@'):
            current_line += 1

    return changed_lines


def validate_fxy(file_path, table_name, column_name):
    errors = []
    # Get changed lines for this file.
    changed_lines = get_changed_lines(file_path)

    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            if i not in changed_lines:
                continue
            fxy = row.get(column_name, '')
            if not re.match(r'^\d{6}$', fxy):
                errors.append(f"{table_name} Line {i}: Invalid {column_name} '{fxy}' (not 6 digits)")
                continue
            xx = int(fxy[1:3])
            yyy = int(fxy[3:])
            if not (0 <= xx <= 47 and 0 <= yyy <= 191):
                errors.append(f"{table_name} Line {i}: {column_name} '{fxy}' out of range (XX={xx}, YYY={yyy})")
    return errors

# Get changed files
changed_files = get_changed_files()

# Get changed table D files
d_files = [
    f for f in changed_files
    if f.replace('\\', '/').split('/')[-1].startswith('BUFR_TableD_en_')
    and f.replace('\\', '/').split('/')[-1].endswith('.csv')
]
# Check Table D files
d_errors = []
if d_files:
    for d_file in sorted(d_files):
        version = re.search(r'BUFR_TableD_en_(\d+)\.csv$', d_file)
        version_str = f" (version {version.group(1)})" if version else ""
        d_errors.extend(validate_fxy(d_file, f'TableD{version_str}', 'FXY1'))

# Get changed table B files
b_files = [
    f for f in changed_files
    if f.replace('\\', '/').split('/')[-1].startswith('BUFRCREX_TableB_en_')
    and f.replace('\\', '/').split('/')[-1].endswith('.csv')
]

# Check Table B files
b_errors = []
if b_files:
    for b_file in sorted(b_files):
        version = re.search(r'BUFRCREX_TableB_en_(\d+)\.csv$', b_file)
        version_str = f" (version {version.group(1)})" if version else ""
        b_errors.extend(validate_fxy(b_file, f'TableB{version_str}', 'FXY'))
    

all_errors = d_errors + b_errors
if all_errors:
    for err in all_errors:
        print(err)
    sys.exit(1)
else:
    sys.exit(0)
