import random

# Open a file named 'input.txt' in write mode
# trace numeber: 1000
x = 30  # fixed input x = 30
size = 64  # galois field size: 32, 64, 128, 256
with open('input.txt', 'w') as file:
    # dataset Q0 for fixed number 41
    for _ in range(500):
        file.write(f"{format(x, '08b')}\n")
        # Write a line with a random number between 0 and 250
        file.write(f"{format(random.randint(0, size), '08b')}\n")

    # dataset Q1 for randomm number
    for _ in range(1000):
        file.write(f"{format(random.randint(0, size), '08b')}\n")

