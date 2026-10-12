import os

BASE = os.path.dirname(os.path.abspath(__file__))
interp_file = os.path.join(BASE, 'advak_interpreter.py')
lines = open(interp_file, encoding='utf-8').readlines()

# Find ALL occurrences of AdvakInstance member access
print("Buscando blocos com AdvakInstance em member access:")
for i, line in enumerate(lines, 1):
    if 'isinstance(obj, AdvakInstance)' in line:
        print(f"\n  Linha {i}: {line.rstrip()}")
        # Show surrounding context
        for j in range(max(0,i-8), min(len(lines), i+20)):
            marker = ">>>" if j == i-1 else "   "
            print(f"  {marker} {j+1}: {lines[j].rstrip()}")

print("\n\nBuscando 'async def eval':")
for i, line in enumerate(lines, 1):
    if 'async def eval' in line:
        print(f"  Linha {i}: {line.rstrip()}")

print("\n\nBuscando \"t == 'member'\":")
for i, line in enumerate(lines, 1):
    if "t == 'member'" in line:
        print(f"  Linha {i}: {line.rstrip()}")
        for j in range(i-1, min(len(lines), i+30)):
            print(f"    {j+1}: {lines[j].rstrip()}")
        print()
