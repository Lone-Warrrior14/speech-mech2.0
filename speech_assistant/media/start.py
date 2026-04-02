from backend import entertainment_mode
from input_handler import get_input

print("System ready")

while True:

    command = get_input()

    if not command:
        continue

    if "entertainment" in command:

        entertainment_mode()