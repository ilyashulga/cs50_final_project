#include <cs50.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

// Prototype definition
int count_letters(string text);
int count_words(string text);
int count_sentences(string text);

int main(void)
{
    // define variables for this scope
    float L = 0.0;                            // Avarage number of letters per 100 words in the text
    float S = 0.0;                            // Average number of sentences per 100 words in the text
    // prompt to input a text
    string text = get_string("Text: ");
    // print back the inputed string
    /*
    for (int i = 0; i < strlen(text); i++)
    {
        printf("%c", text[i]);
    }
    printf("\n");
    */
    // count number of letters in text
    int letters_number = count_letters(text);
    //printf("%i\n", letters_number);
    // count number of words in text
    int words_number = count_words(text);
    //printf("%i\n", words_number);
    // count number of sentences in text
    int sentences_number = count_sentences(text);
    //printf("%i\n", sentences_number);

    // calcultage L variable
    L = letters_number / (words_number / 100.0);
    // calcultage S variable
    S = sentences_number / (words_number / 100.0);
    // calculate Coleman-Liau index
    float index = 0.0588 * L - 0.296 * S - 15.8;
    /*
    printf("%f\n", L);
    printf("%f\n", S);
    printf("%f\n", index);
    */
    if (index < 1.0)
    {
        printf("Before Grade 1\n");
    }
    else if (index >= 16.0)
    {
        printf("Grade 16+\n");
    }
    else
    {
        printf("Grade %i\n", (int) round(index));
    }
}

int count_letters(string text)
{
    // introduce counter variable
    int count = 0;
    // iterate through every symbol inside text string
    for (int i = 0; i < strlen(text); i++)
    {
        if (isalpha((int) text[i]))
        {
            count++;
        }
    }
    return count;
}

int count_words(string text)
{
    // introduce counter variable
    int count = 1;
    // iterate through every symbol inside text string
    for (int i = 0; i < strlen(text); i++)
    {
        //if (isalnum((int) text[i-1]) && !(isalnum((int) text[i]) || text[i] == '-' || (int) text[i] == 39) && !(text[i+1] == '"'))
        if (text[i] == ' ')
        {
            count++;
        }
    }
    return count;
}

int count_sentences(string text)
{
    // introduce counter variable
    int count = 0;
    // iterate through every symbol inside text string
    for (int i = 0; i < strlen(text); i++)
    {
        if (isalnum((int) text[i - 1]) && (text[i] == '!' || text[i] == '?' || text[i] == '.'))
        {
            count++;
        }
    }
    return count;
}