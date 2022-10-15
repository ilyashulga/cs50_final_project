# Simulate a sports tournament

import csv
import sys
import random

# Number of simluations to run
N = 1000


def main():

    # Ensure correct usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python tournament.py FILENAME")

    teams = []
    # TODO: Read teams into memory from file - teams[] is a list of dictionaries
    f = open(sys.argv[1])
    reader = csv.DictReader(f)
    for row in reader:
        row["rating"] = int(row["rating"])
        teams.append(row)
        # print(row)

    counts = {}  # counts is a dictionary
    # Populate dictionart will all teams and reset scores
    for row in teams:
        counts[row['team']] = 0
        # print(row['team'])
    # print(counts)
    # Iterate N times (N tournaments)
    for i in range(N):
        winning_team = simulate_tournament(teams)
        counts[winning_team] += 1
    # print(winning_team)

    # Print each team's chances of winning, according to simulation
    for team in sorted(counts, key=lambda team: counts[team], reverse=True):
        print(f"{team}: {counts[team] * 100 / N:.1f}% chance of winning")


def simulate_game(team1, team2):
    """Simulate a game. Return True if team1 wins, False otherwise."""
    rating1 = team1["rating"]
    rating2 = team2["rating"]
    probability = 1 / (1 + 10 ** ((rating2 - rating1) / 600))
    return random.random() < probability


def simulate_round(teams):
    """Simulate a round. Return a list of winning teams."""
    winners = []

    # Simulate games for all pairs of teams
    for i in range(0, len(teams), 2):
        if simulate_game(teams[i], teams[i + 1]):
            winners.append(teams[i])
        else:
            winners.append(teams[i + 1])

    return winners


def simulate_tournament(teams):
    """Simulate a tournament. Return name of winning team."""
    # TODO: Simulate N tournaments and keep track of win counts
    round_winners = teams
    # Simulate rounds until 1 team is left in the round_winners
    while True:
        # Simulate round
        round_winners = simulate_round(round_winners)
        # print(len(round_winners))
        if len(round_winners) == 1:
            # print(round_winners)
            return round_winners[0]['team']
            # print(counts)


if __name__ == "__main__":
    main()
