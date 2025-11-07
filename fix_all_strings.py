import re

# Read file
with open('src/signal_detector.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix each line
fixed_lines = []
for line in lines:
    # Pattern: "a" followed by text without closing quote
    # Replace with proper string
    line = re.sub(r'"a"\s+([A-Z][^"]*)"', r'"\1"', line)
    # Pattern: f"...a" followed by text
    line = re.sub(r'f"([^"]*)"a"\s+([A-Z][^"]*)"', r'f"\1\2"', line)
    # Pattern: f"\na" followed by text  
    line = re.sub(r'f"\\na"\s+([A-Z][^"]*)"', r'f"\\n\1"', line)
    
    fixed_lines.append(line)

# Write fixed file
with open('src/signal_detector.py', 'w', encoding='utf-8', newline='') as f:
    f.writelines(fixed_lines)

print("Fixed all string literals")
