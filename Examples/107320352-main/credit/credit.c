#include <cs50.h>
#include <stdio.h>

int count_digits(long number);
int digit(long number, int place);
int sum_all_digits(int number);

int main(void)
{
    //Declare variable for credit card storage
    long card_num;
    //Ask user to enter credit card number. Continue only if input is 13-16 digits long
    do
    {
        card_num = get_long("Credit card number: ");

    }
    while (card_num > 9999999999999999 || card_num < 1000000000);


    int sum_mult = 0;
    int sum = 0;
    int total_sum = 0;
    //Multiply every other digit by 2, starting with the number’s second-to-last digit, than sum each multiplication resulting number digits
    for (int i = count_digits(card_num) - 1; i >= 1; i -= 2)
    {
        int digit_n_value = digit(card_num, i);
        //printf("%i\n", digit_n_value);
        int mult_digit = digit_n_value * 2;
        int digits_sum = sum_all_digits(mult_digit);
        //printf("%i\n", digits_sum);
        sum_mult += digits_sum;
    }
    //Sum all remaining digits in number starting from the last
    for (int i = count_digits(card_num); i >= 1; i -= 2)
    {
        int digit_n_value = digit(card_num, i);
        //printf("%i\n", digit_n_value);
        sum += digit_n_value;
    }
    total_sum = sum_mult + sum;
    //printf("%i\n", total_sum);

    if (total_sum % 10 == 0 && count_digits(card_num) >= 13)
    {
        //printf("the card is valid\n");
        int digit_n_value;
        if (digit(card_num, 1) == 3 && (digit(card_num, 2) == 4 || digit(card_num, 2) == 7))
        {
            printf("AMEX\n");
        }
        else if (digit(card_num, 1) == 5 && (digit(card_num, 2) == 1 || digit(card_num, 2) == 2 || digit(card_num, 2) == 3
                                             || digit(card_num, 2) == 4 || digit(card_num, 2) == 5))
        {
            printf("MASTERCARD\n");
        }
        else if (digit(card_num, 1) == 4)
        {
            printf("VISA\n");
        }
        else
        {
            printf("INVALID\n");
        }
    }
    else
    {
        printf("INVALID\n");
    }



}

int count_digits(long number)
{
    int counter = 0;
    //Divide credit card number by 10 maximum 16 times - if result is not 0 - increase digits count
    for (int i = 0; i <= 16; i++)
    {
        long x = number;
        for (int j = i; j > 0; j--)
        {
            x = x / 10;
        }
        if (x >= 1)
        {
            counter++;
        }
    }

    return counter;
}


int digit(long number, int place)
{
    //Define variable to store digit that was fount in the requested place
    int digit_in_place = 0;
    //Count how long is the credit card number
    int digits_count = count_digits(number);
    //Define local variable to store intermediate results after division by 10
    long x = number;
    for (int j = digits_count - place; j > 0; j--)
    {
        x = x / 10;
    }
    //Divide one more time by 10 and return remainder as a requested digit
    digit_in_place = x % 10;
    return digit_in_place;
}

int sum_all_digits(int number)
{
    int sum_all = 0;
    int digit_n_value = 0;
    for (int i = 1; i <= count_digits(number); i++)
    {
        digit_n_value = digit(number, i);
        sum_all += digit_n_value;
    }
    //printf("%i\n", sum_all);
    return sum_all;
}