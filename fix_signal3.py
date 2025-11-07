import re

# Read file
with open('src/signal_detector.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix broken string patterns
fixes = [
    (r'"a"\s+STRATEGY:', '"STRATEGY:'),
    (r'"a"\s+UPTREND', '"UPTREND'),
    (r'"a"\s+DOWNTREND', '"DOWNTREND'),
    (r'"a"\s+PULLBACK', '"PULLBACK'),
    (r'"a"\s+RALLY', '"RALLY'),
    (r'"a"\s+VOLUME', '"VOLUME'),
    (r'"a"\s+MOMENTUM:', '"MOMENTUM:'),
    (r'"a"\s+WHY', '"WHY'),
    (r'"a"\s+BULLISH', '"BULLISH'),
    (r'"a"\s+BEARISH', '"BEARISH'),
]

for pattern, replacement in fixes:
    text = re.sub(pattern, replacement, text)

# Write fixed file
with open('src/signal_detector.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("Fixed all broken strings")
