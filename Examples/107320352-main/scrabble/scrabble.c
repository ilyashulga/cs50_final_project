#include <ctype.h>
#include <cs50.h>
#include <stdio.h>
#include <string.h>

// Points assigned to each letter of the alphabet
int POINTS[] = {1, 3, 3, 2, 1, 4, 2, 4, 1, 8, 5, 1, 3, 1, 1, 3, 10, 1, 1, 1, 1, 4, 4, 8, 4, 10};
// All UPPER-case letters array
char LETTERS_UPPER[] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'};
// All lower-case letters array
char LETTERS_LOWER[] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'};

int compute_score(string word);

int main(void)
{
    // Get input words from both players
    string word1 = get_string("Player 1: ");
    string word2 = get_string("Player 2: ");

    // Score both words
    int score1 = compute_score(word1);
    int score2 = compute_score(word2);

    //Print the winner
    if (score1 > score2)
    {
        printf("Player 1 wins!\n");
    }
    else if (score2 > score1)
    {
        printf("Player 2 wins!\n");
    }
    else if (score2 == score1)
    {
        printf("Tie!\n");
    }
}

int compute_score(string word)
{
    // Introduce variable to store word total score
    int sum = 0;
    // Iterate through each letter in "word" string
    for (int i = 0; i < strlen(word); i++)
    {
        // Iterate through each letter in the word
        // Check whether the letter is upper or lower
        if (isupper((int) word[i]))
        {
            // Iterate though the array of all possible uppercase characters (LETTERS_UPPER)
            for (int j = 0; j < sizeof LETTERS_UPPER; j++)
            {
                // Check if letter with index i present in the list of letters that add score
                if ((char) word[i] == (char) LETTERS_UPPER[j])
                {
                    // Increment the size by corresponding to the current letter score
                    sum += POINTS[j];
                }
            }
        }
        else if (islower((int) word[i]))
        {
            // Iterate though the array of all possible uppercase characters (LETTERS_LOWER)
            for (int j = 0; j < sizeof LETTERS_LOWER; j++)
            {
                // Check if letter with index i present in the list of letters that add score
                if ((char) word[i] == (char) LETTERS_LOWER[j])
                {
                    // Increment the size by corresponding to the current letter score
                    sum += POINTS[j];
                }
            }
        }
    }
    return sum;
}
