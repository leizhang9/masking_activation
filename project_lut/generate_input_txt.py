import random

# Open a file named 'input.txt' in write mode
with open('input.txt', 'w') as file:
    # dataset Q0 for fixed number 41
    for _ in range(2000):
        file.write(f"{format(41, '08b')}\n")
        # Write a line with a random number between 0 and 250
        file.write(f"{format(random.randint(0, 250), '08b')}\n")

    # dataset Q1 for randomm number
    for _ in range(4000):
        file.write(f"{format(random.randint(0, 250), '08b')}\n")

