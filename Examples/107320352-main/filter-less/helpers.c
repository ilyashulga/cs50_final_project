#include "helpers.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// Convert image to grayscale
void grayscale(int height, int width, RGBTRIPLE image[height][width])
{
    // image is a pointer to two dimensional array of RGBTRIPLE type values

    /*if (height == 1 && width == 1)
    {
        image[0][0].rgbtRed = (image[0][0].rgbtRed + image[0][0].rgbtGreen + image[0][0].rgbtBlue) / 3 ;
        image[0][0].rgbtGreen = image[0][0].rgbtRed;
        image[0][0].rgbtBlue = image[0][0].rgbtRed;
    }*/
    // iterate through each RGBTRIPLE element
    for (int i = 0; i <= height; i++)
    {
        for (int j = 0; j <= width; j++)
        {
            // Calculate avarage of R, G, B values and replace their values with AVG
            double rgb_avg = 0.0;
            rgb_avg = (image[i][j].rgbtRed + image[i][j].rgbtGreen + image[i][j].rgbtBlue) / 3.0 ;
            //printf("%d", rgb_avg);
            image[i][j].rgbtRed = round(rgb_avg);
            image[i][j].rgbtGreen = round(rgb_avg);
            image[i][j].rgbtBlue = round(rgb_avg);
        }

    }
    return;
}

// Convert image to sepia
void sepia(int height, int width, RGBTRIPLE image[height][width])
{
    // iterate through each RGBTRIPLE element
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            // introduce variables to store new rgbt values
            double new_rgbtRed = 0;
            double new_rgbtGreen = 0;
            double new_rgbtBlue = 0;

            // Calculate sepic values of R, G, B and replace original
            new_rgbtRed = .393 * image[i][j].rgbtRed + .769 * image[i][j].rgbtGreen + .189 * image[i][j].rgbtBlue;

            new_rgbtGreen = .349 * image[i][j].rgbtRed + .686 * image[i][j].rgbtGreen + .168 * image[i][j].rgbtBlue;

            new_rgbtBlue = .272 * image[i][j].rgbtRed + .534 * image[i][j].rgbtGreen + .131 * image[i][j].rgbtBlue;
            if (new_rgbtRed > 255.0)
            {
                new_rgbtRed = 255.0;
            }
            if (new_rgbtGreen > 255.0)
            {
                new_rgbtGreen = 255.0;
            }
            if (new_rgbtBlue > 255.0)
            {
                new_rgbtBlue = 255.0;
            }
            image[i][j].rgbtRed = round(new_rgbtRed);
            image[i][j].rgbtGreen = round(new_rgbtGreen);
            image[i][j].rgbtBlue = round(new_rgbtBlue);
        }

    }
    return;
}

// Reflect image horizontally
void reflect(int height, int width, RGBTRIPLE image[height][width])
{
    // allocate space to store mirrored image
    RGBTRIPLE(*mirrored_image)[width] = calloc(height, width * sizeof(RGBTRIPLE));

    // iterate through each RGBTRIPLE element
    for (int i = 0; i < height; i++)
    {
        // for each row - store each j element of image in width-1-j element of mirrored image
        for (int j = 0; j < width; j++)
        {
            mirrored_image[i][width - 1 - j] = image[i][j];
        }
        // replace the image i raw to the mirrored version
        for (int j = 0; j < width; j++)
        {
            image[i][j] = mirrored_image[i][j];
        }
    }

    free(mirrored_image);
    return;
}

// Blur image
void blur(int height, int width, RGBTRIPLE image[height][width])
{
    double r_sum = 0;
    double g_sum = 0;
    double b_sum = 0;
    // total count of pixels inside valid range
    int count = 0;
    // allocate space to store mirrored image
    RGBTRIPLE(*blured_image)[width] = calloc(height, width * sizeof(RGBTRIPLE));

    // iterate through each RGBTRIPLE element in two dimantional array
    for (int i = 0; i < height; i++)
    {
        // for each row -
        for (int j = 0; j < width; j++)
        {
            r_sum = 0.0;
            g_sum = 0.0;
            b_sum = 0.0;
            count = 0;
            // do if pixel is not on the edge
            if (i > 0 && i < height - 1 && j > 0 && j < width - 1)
            {
                for (int k = i - 1; k <= i + 1; k++)
                {
                    for (int l = j - 1; l <= j + 1; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is on the left edge but not in the corner
            else if (j == 0 && i != 0 && i != height - 1)
            {
                for (int k = i - 1; k <= i + 1; k++)
                {
                    for (int l = j; l <= j + 1; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is on the right edge but not in the corner
            else if (j == width - 1 && i != 0 && i != height - 1)
            {
                for (int k = i - 1; k <= i + 1; k++)
                {
                    for (int l = j - 1; l <= j; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is on the top edge but not in the corner
            else if (i == 0 && j != 0 && j != width - 1)
            {
                for (int k = i; k <= i + 1; k++)
                {
                    for (int l = j - 1; l <= j + 1; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is on the bottom edge but not in the corner
            else if (i == height - 1 && j != 0 && j != width - 1)
            {
                for (int k = i - 1; k <= i; k++)
                {
                    for (int l = j - 1; l <= j + 1; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is in the top left  corner
            else if (i == 0 && j == 0)
            {
                for (int k = i; k <= i + 1; k++)
                {
                    for (int l = j; l <= j + 1; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is in the bottom right  corner
            else if (i == height - 1 && j == width - 1)
            {
                for (int k = i - 1; k <= i; k++)
                {
                    for (int l = j - 1; l <= j; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is in the botton left corner
            else if (i == height - 1 && j == 0)
            {
                for (int k = i - 1; k <= i; k++)
                {
                    for (int l = j; l <= j + 1; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            // if pixel is in the top right corner
            else if (i == 0 && j == width - 1)
            {
                for (int k = i; k <= i + 1; k++)
                {
                    for (int l = j - 1; l <= j; l++)
                    {
                        r_sum += image[k][l].rgbtRed;
                        g_sum += image[k][l].rgbtGreen;
                        b_sum += image[k][l].rgbtBlue;
                        count++;
                    }
                }
            }
            blured_image[i][j].rgbtRed = round(r_sum / count);
            blured_image[i][j].rgbtGreen = round(g_sum / count);
            blured_image[i][j].rgbtBlue = round(b_sum / count);
        }

    }
    for (int k = 0; k < height; k++)
    {
        for (int l = 0; l < width; l++)
        {
            image[k][l] = blured_image[k][l];
        }
    }
    free(blured_image);
    return;
}
