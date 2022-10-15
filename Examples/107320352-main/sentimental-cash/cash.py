from cs50 import get_float


def main():
    # Get half-pyramid desired height from user
    while True:
        change = round(get_float('Change owed: '), 2)
        if change > 0:
            break
    # print(change)
    coins_cnt = 0

    while change >= 0.01:
        # find number of dollar bills for exchange
        if change >= 0.25:
            coins_cnt += int(change/0.25)
            change -= coins_cnt * 0.25
            change = round(change, 2)
            # print(coins_cnt,change)
        elif change >= 0.1:
            coins_cnt += int(change/0.1)
            change -= int(change/0.1)*0.1
            change = round(change, 2)
            # print(coins_cnt,change)
        elif change >= 0.05:
            coins_cnt += int(change/0.05)
            change -= int(change/0.05)*0.05
            change = round(change, 2)
            # print(coins_cnt,change)
        elif change >= 0.01:
            coins_cnt += int(change/0.01)
            change -= int(change/0.01)*0.01
            change = round(change, 2)
            # print(coins_cnt,change)

    print(coins_cnt)


if __name__ == '__main__':
    main()