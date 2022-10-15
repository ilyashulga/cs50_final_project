#include <cs50.h>
#include <stdio.h>

void draw_pyramid(int height);

int main(void)
{
    //Declare pyramid height variable
    int pyr_height;
    //Ask user for how tall the pyramid should be. Continue only if input 1-8 (inclusive)
    do
    {
        pyr_height = get_int("What should be the pyramid hight?\n");
    }
    while (pyr_height > 8 || pyr_height < 1);

    draw_pyramid(pyr_height);

}

void draw_pyramid(int height)
{
    //Declare character to "fill" the pyramid variables
    char sym1 = ' ';
    char sym2 = '#';

    //Iterate through each row in pyramid from top to bottom
    for (int i = height; i > 0; i--)
    {
        //Begin to fill the row

        //Print ' ' according to raw number
        for (int j = 0; j < i - 1; j++)
        {
            printf("%c", sym1);
        }
        //Print '#' according to raw number
        for (int j = i - 1; j < height; j++)
        {
            printf("%c", sym2);
        }

        //Place spacing between pyramid left and right wall
        printf("  ");

        //Print ' ' according to raw number
        for (int j = i - 1; j < height; j++)
        {
            printf("%c", sym2);
        }
        //Print '#' according to raw number
        /*
        for (int j = 0; j < i - 1; j++)
        {
             printf("%c", sym1);
        }
        */
        printf("\n");
    }
}
