import csv
import sys


def main():

    # TODO: Check for command-line usage
    try:
        arg = sys.argv[2]
    except IndexError:
        raise SystemExit(f"Usage: {sys.argv[0]} <STR database *.csv File> <DNA sample sequence *.txt File>")

    # TODO: Read STR database file into a variable
    # Create a variable for storing list of dictionaries
    database = []

    f = open(sys.argv[1])
    reader = csv.DictReader(f)
    for row in reader:
        for sequence in row:
            # print(sequence)
            # Convert the longest syquence to number (from string)
            if sequence != "name":
                row[sequence] = int(row[sequence])
        database.append(row)
        # print(row)
    # TODO: Read DNA sequence file into a variable
    f = open(sys.argv[2])
    dna_sample = f.read()
    # print(dna_sample)

    # TODO: Find longest match of each STR in DNA sequence
    # Create dictionary for sequences longes match
    longest = {}
    # Iterate through each STR from database
    for key in database[0].keys():
        if key != "name":
            # Find longest match in provided DNA sequence
            longest[key] = longest_match(dna_sample, key)
    # print(longest)

    # TODO: Check database for matching profiles
    # Create boolean variable to indicate a match was found
    match = False
    matched_name = 'NULL'
    # Iterate through each row in STR database
    for row in database:
        # Compare each of the STR keys to database
        for key in row:
            if key != "name":
                if row[key] == longest[key]:
                    match = True
                else:
                    match = False
                    break
        if match == True:
            matched_name = row["name"]

    if matched_name == 'NULL':
        print("No match")
    else:
        print(matched_name)

    return


def longest_match(sequence, subsequence):
    """Returns length of longest run of subsequence in sequence."""

    # Initialize variables
    longest_run = 0
    subsequence_length = len(subsequence)
    sequence_length = len(sequence)

    # Check each character in sequence for most consecutive runs of subsequence
    for i in range(sequence_length):

        # Initialize count of consecutive runs
        count = 0

        # Check for a subsequence match in a "substring" (a subset of characters) within sequence
        # If a match, move substring to next potential match in sequence
        # Continue moving substring and checking for matches until out of consecutive matches
        while True:

            # Adjust substring start and end
            start = i + count * subsequence_length
            end = start + subsequence_length

            # If there is a match in the substring
            if sequence[start:end] == subsequence:
                count += 1

            # If there is no match in the substring
            else:
                break

        # Update most consecutive matches found
        longest_run = max(longest_run, count)

    # After checking for runs at each character in seqeuence, return longest run found
    return longest_run


main()
