#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

int jpeg_search(FILE *raw_data);
unsigned char buffer[512];

int main(int argc, char *argv[])
{
    // Check for invalid usage
    if (argc != 2)
    {
        printf("Usage: recover [filename...]\n");
        return 1;
    }


    // Open the raw file for reading
    FILE *inptr = fopen(argv[1], "r");
    if (inptr == NULL)
    {
        printf("Could not open file.\n");
        return 1;
    }



    // handle the pointer to raw file to the jpeg_search function
    jpeg_search(inptr);


    // Close files
    fclose(inptr);
}


int jpeg_search(FILE *raw_data)
{
    // jpeg_search function iterates through each block of 512b and checks 4 first bytes
    // Example 2: reading 512x1bytes(uint8_t) from raw_data and storing them into newly-created block[] with size of 512 using dynamically allocated memory (HEAP)
    uint8_t *block = malloc(sizeof(buffer));
    int blocks_cnt = 0;
    int jpg_cnt = 0;
    bool new_jpg = false;
    FILE *jpg;
    while (fread(block, sizeof(buffer), 1, raw_data))
    {
        if (block[0] == 0xff && block[1] == 0xd8 && block[2] == 0xff && (block[3] == 0xe0
                || block[3] == 0xe1 || block[3] == 0xe2 || block[3] == 0xe3 || block[3] == 0xe4
                || block[3] == 0xe5 || block[3] == 0xe6 || block[3] == 0xe7 || block[3] == 0xe8
                || block[3] == 0xe9 || block[3] == 0xea || block[3] == 0xeb || block[3] == 0xec
                || block[3] == 0xed || block[3] == 0xee || block[3] == 0xef))
        {
            jpg_cnt++;
            new_jpg = true;
        }

        if (new_jpg == true)
        {
            char name[8];
            if (jpg_cnt > 1)
            {
                fclose(jpg);
            }
            // create custom name for each jpg file if the format xxx.jpg, where xxx is the serial number of the jpg file
            if (jpg_cnt >= 11)
            {
                sprintf(name, "0%i.jpg", jpg_cnt - 1);
            }
            else
            {
                sprintf(name, "00%i.jpg", jpg_cnt - 1);
            }
            jpg = fopen(name, "a");
            if (jpg == NULL)
            {
                printf("Could not open file.\n");
                return 1;
            }
            /*for (int i = 0; i < 7; i++)
            {
                printf("%c", name[i]);
            }
            printf("\n");*/
        }
        if (jpg_cnt > 0)
        {
            fwrite(block, sizeof(buffer), 1, jpg);
        }
        blocks_cnt++;
        new_jpg = false;
    }
    //printf("%i\n", blocks_cnt);
    //printf("%i\n", jpg_cnt);
    // jpeg_search opens file for writing with index xxx and extension jpeg
    // jpeg_search writes the jpeg data from raw data till the next jpeg signature if reached
    free(block);
    return 0;
}