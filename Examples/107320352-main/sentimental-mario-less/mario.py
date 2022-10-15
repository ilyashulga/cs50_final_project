from cs50 import get_int


def main():
    # Get half-pyramid desired height from user
    while True:
        h = get_int('Height: ')
        if h > 0 and h < 9:
            break
    # Draw pyramid
    draw_pyr(h, h)


def draw_pyr(height, curr_row):
    # Check recursive base case
    if curr_row < 1:
        return True

    # Recursively build pyramid
    draw_pyr(height, curr_row-1)

    # Draw single row of blocks
    print(' ' * (height-curr_row), end='')
    print('#' * curr_row)


if __name__ == '__main__':
    main()