from speech_to_text import listen

print("Starting test...")
for i in range(5):
    print(f"\nIteration {i+1}")
    result = listen(prompt="Test listen... Speak or wait 10s")
    print(f"Result: {result}")
