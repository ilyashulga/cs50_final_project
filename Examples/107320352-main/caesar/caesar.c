#include <cs50.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

bool check_input(int argc, string argv[]);
char rotate(char c, int positions);


char LETTERS_UPPER[26] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'};
char LETTERS_LOWER[26] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'};

int main(int argc, string argv[])
{

    // check the arguments were provided correctly to the function (need to be 1 argument and positive integer)

    // introduce a bool variable to indicate the entered key is of positive integer type
    bool pos_int = check_input(argc, argv);
    //printf("%i\n", pos_int);

    // if the function input arguments from user are correct enter main program flow, if not - return 1 (something went wrong)
    if (pos_int)
    {
        // get input string for encoding from user
        string p = get_string("plaintext:  ");
        //printf("%s\n", p);

        // convert a last funtion argument argv[] to int (the number of positions to rotate the letters)
        int rot_pos = atoi(argv[argc - 1]);
        //printf("Rotate %i positions\n", rot_pos);

        // introduce array for storing encoded string
        char encoded_p[strlen(p)];
        // iterate through every symbol inside p string and get new encoded value
        for (int i = 0; i < strlen(p); i++)
        {
            encoded_p[i] = rotate(p[i], rot_pos);
        }
        printf("ciphertext: %s\n", encoded_p);
    }
    else
    {
        // if user entered invalid argumets (wrong argc count or non-positive integer) - main program returns "1" (common convention for fault)
        return true;
    }
}



bool check_input(int argc, string argv[])
{
    // check if number of arguments is equal to 2, if not - return false
    if (!(argc == 2))
    {
        printf("Usage: ./caesar key\n");
        return false;
    }
    else
    {
        for (int i = 0; i < strlen(argv[argc - 1]); i++)
        {
            if (!(isdigit(argv[argc - 1][i])))
            {
                printf("Usage: ./caesar key\n");
                return false;
            }
        }
    }
    return true;
}


char rotate(char c, int positions)
{
    if (isalpha(c))
    {
        // introduce variable to store character numerical positions
        int old_pos = 0;
        int new_pos = 0;
        // find character numerical position in LETTERS string (0-25)
        if (isupper(c))
        {
            while (c != LETTERS_UPPER[old_pos])
            {
                old_pos++;
            }
            //printf("Old char position = %i\n", old_pos);

            // calculate the new position index in the LETTERS_LOWER array, roll over if exceeded it's size (26)
            new_pos = (old_pos + positions) % sizeof LETTERS_UPPER;
            return LETTERS_UPPER[new_pos];
        }
        else
        {
            while (c != LETTERS_LOWER[old_pos])
            {
                old_pos++;
            }
            //printf("Old char position = %i\n", old_pos);

            // Calculate the new position index in the LETTERS_LOWER array, roll over if exceeded it's size (26)
            new_pos = (old_pos + positions) % sizeof LETTERS_LOWER;
            return LETTERS_LOWER[new_pos];
        }
    }
    else
    {
        // return same value as recieved in case of value received in not alphabetical
        return c;
    }
}