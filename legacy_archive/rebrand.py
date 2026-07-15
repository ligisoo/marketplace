import os
import glob
import re

replacements = {
    r"\bBetting Tips\b": "Match Predictions",
    r"\bbetting tips\b": "match predictions",
    r"\bBetting tips\b": "Match predictions",
    r"\bTipster\b": "Sports Analyst",
    r"\btipster\b": "sports analyst",
    r"\bTipsters\b": "Sports Analysts",
    r"\btipsters\b": "sports analysts",
    r"\bBetslips\b": "Prediction Slips",
    r"\bbetslips\b": "prediction slips",
    r"\bBetslip\b": "Prediction Slip",
    r"\bbetslip\b": "prediction slip",
    r"\bPossible Win\b": "Projected Value",
    r"\bpossible win\b": "projected value",
}

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = content
    for old, new in replacements.items():
        # Avoid replacing variable names inside {{ }} and {% %}
        # But this is a simple script, we just use regex to replace text, not variables
        # Using word boundaries \b prevents replacing tipster_id
        new_content = re.sub(old, new, new_content)
            
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('/home/walter/Projects/marketplace/templates'):
    for file in files:
        if file.endswith('.html'):
            replace_in_file(os.path.join(root, file))

# Fix SOFT_LAUNCH_GUIDE.md as well
guide_path = '/home/walter/Projects/marketplace/SOFT_LAUNCH_GUIDE.md'
if os.path.exists(guide_path):
    replace_in_file(guide_path)
