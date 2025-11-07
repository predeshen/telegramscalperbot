import string

# Read file as binary
with open('src/signal_detector.py', 'rb') as f:
    data = f.read()

# Keep only printable ASCII + newlines/tabs + extended ASCII for emojis
clean_bytes = bytearray()
for byte in data:
    # Keep: printable ASCII, newline, carriage return, tab
    if (32 <= byte <= 126) or byte in (9, 10, 13):
        clean_bytes.append(byte)
    # Skip control characters and null bytes
    elif byte < 32:
        continue
    # Keep extended ASCII (for UTF-8 sequences)
    elif byte >= 128:
        clean_bytes.append(byte)

# Write clean file
with open('src/signal_detector.py', 'wb') as f:
    f.write(bytes(clean_bytes))

print("Removed all control characters")
