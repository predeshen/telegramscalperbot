import re

# Read file
with open('src/signal_detector.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Remove all replacement characters and fix emoji strings
text = text.replace('�', '')
text = text.replace('☺', '')
text = text.replace('Ļ', '')

# Fix known emoji patterns in strings
replacements = {
    '"a" STRATEGY:': '"STRATEGY:',
    '"a"  UPTREND': '"UPTREND',
    '"a"  DOWNTREND': '"DOWNTREND',
    '"a"  PULLBACK': '"PULLBACK',
    '"a"  RALLY': '"RALLY',
    '"a"  VOLUME': '"VOLUME',
    '"a" MOMENTUM:': '"MOMENTUM:',
    '"a"  WHY': '"WHY',
    '"a" BULLISH': '"BULLISH',
    '"a" BEARISH': '"BEARISH',
}

for old, new in replacements.items():
    text = text.replace(old, new)

# Write clean file
with open('src/signal_detector.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("Fixed signal_detector.py")
