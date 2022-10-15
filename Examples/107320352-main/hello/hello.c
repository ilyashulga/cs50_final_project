#include <stdio.h>
#include <cs50.h>

int main(void)
{
    //Ask user to input his/her name
    string my_name = get_string("What's your name?\n");
    printf("hello, %s!\n", my_name);
}