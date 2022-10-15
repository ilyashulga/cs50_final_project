// Implements a dictionary's functionality

#include <ctype.h>
#include <stdbool.h>
#include <strings.h>
#include <ctype.h>
#include "dictionary.h"

// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
}
node;

//void search(node* curr_node, const char *word);
// TODO: Choose number of buckets in hash table
//const unsigned int N = 26;
const unsigned int N = 1500;

// Dictionary loaded flag
bool loaded = false;

// Word found flag
bool word_found = false;

// Number of words in dictionary
unsigned int count = 0;

// Hash table
node *table[N];

// Returns true if word is in dictionary, else false
bool check(const char *word)
{
    // Calculate relevant hash table index to look in
    long word_hash = hash(word);
    // Introduce traversal node
    node *cursor = table[word_hash];

    while (cursor != NULL)
    {
        if (strcasecmp(word, cursor->word) == 0)
        {
            return true;
        }
        cursor = cursor->next;
    }
    return false;
    //printf("%s\n", word);



}

/*void search(node* next_node, const char *word)
{
    //printf("%s\n", next_node->word);
    //printf("%s\n", word);
    printf("%i\n", strcasecmp(word, next_node->word));
    if (next_node->next == NULL && (strcasecmp(word, next_node->word)))
    {

        return;
    }
    else if (!strcasecmp(word, next_node->word))
    {
        printf("%s\n", word);
        word_found = true;
    }
    else
    {
        //printf("%s\n", word);
        search(next_node->next, word);
    }

}*/

// Hashes word to a number
unsigned long hash(const char *word)
{
    // TODO: Improve this hash function
    //return toupper(word[0]) - 'A';
    if (strlen(word) > 1)
    {
        if ((toupper(word[0]) - 'A') > (toupper(word[1]) - 'A') && isalpha(word[1]))
        {
            //printf("%u\n", (toupper(word[0]) - 'A') * (toupper(word[1]) - 'A') + 26);
            //printf("%u\n", (toupper(word[0]) - 'A'));
            //printf("%u\n", (toupper(word[1]) - 'A'));
            //printf("%c\n", word[1]);
            return (toupper(word[0]) - 'A') * (toupper(word[1]) - 'A') + 26;
        }
        else if (isalpha(word[1]))
        {
            return (toupper(word[0]) - 'A') * (toupper(word[1]) - 'A') + 676 + 26;
        }
        else
        {
            return toupper(word[0]) - 'A';
        }
    }
    else
    {
        return toupper(word[0]) - 'A';
    }

}

// Loads dictionary into memory, returning true if successful, else false
bool load(const char *dictionary)
{
    // TODO
    // Open dictionary file location passed by user or default DICTIONARY location in speller.c
    //printf("%s\n", dictionary);
    FILE *buffer = fopen(dictionary, "r");
    if (buffer == NULL)
    {
        printf("Could not open dictionary file.\n");
        return 1;
    }
    // Allocate memory for single string
    char word[LENGTH + 1];


    // Read strings from file one at a time
    while (fscanf(buffer, "%s", word) != EOF)
    {
        count++;
        // Allocate memory for new node
        node *new_node = malloc(sizeof(node));
        // Copy each read string into new_node word location
        //string[strcspn(string, "\n")] = 0; // remove /n from strings
        strcpy(new_node->word, word);
        new_node->next = NULL;
        // If suitable hash table section is empty - place the first node into it while "next" pointer is still null
        if (table[hash(new_node->word)] == NULL)
        {
            table[hash(new_node->word)] = new_node;
            //(table[hash(new_node->word)])->next = NULL;
            //printf("1: ");
            //printf("%s", new_node->word);
        }
        else // If the section of a hash table is not empty, save the existing node's pointer into newly creaded node and replace the pointer to the first element inside hash table to the new_node (create linked list in every hash table section)
        {
            new_node->next = table[hash(new_node->word)];
            table[hash(new_node->word)] = new_node;
            //printf("2: ");
            //printf("%s", new_node->word);
        }

    }
    // Debug: print first 3 hash table linked list elements
    /*
    printf("%s", (table[hash("a")])->word);
    printf("%s", ((table[hash("a")])->next)->word);
    printf("%s", (((table[hash("c")])->next)->next)->word);
    printf("%s", ((table[hash("d")])->next)->word);
    */
    loaded = true;
    fclose(buffer);
    return true;
}

// Returns number of words in dictionary if loaded, else 0 if not yet loaded
unsigned int size(void)
{
    // TODO
    if (loaded)
    {
        //printf("Dictionary words count: %u\n", count-1);
        return count;
    }
    else
    {
        return 0;
    }
    return 1;
}

// Unloads dictionary from memory, returning true if successful, else false
bool unload(void)
{


    for (int i = 0; i < N; i++)
    {
        // create traverse node
        node *head = table[i];
        node *cursor = head;
        node *tmp = head;
        while (cursor != NULL)
        {
            tmp = cursor;
            cursor = cursor->next;
            free(tmp);
        }
    }
    return true;
}
