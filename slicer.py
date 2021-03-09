import getopt, sys, yaml

"""
This script uses the motif percentages to decide how to
construct a Schwab stock "slice" that exactly duplicates
the distribution that was in the original motif.

The following multi-step process reproduces the distribution:
    - For each step:
        - Find the stock that is the smallest contribution (in percent)
          to the total purchase, and calculate how much that percentage
          is in dollars. This is the amount we'll need to spend on each
          of the remaining stocks in this step.
        - Display this purchase.
        - Remove the stock and any others at this percentage from the
          list of stocks.
        - Repeat until there is only one stock left, and spend all the
          remaining percentage on it.

This may take a number of steps if the motif had a lot of stocks in it
with different percentages (worst case, there will need to be a step
for each stock in the motif).

The script will allow you to compensate for this by specifying a
maximum "slop" amount. The "slop" is expressed as a dollar amount you're
willing to accept as over or under the original motif's dollar cost;
the script can keep increasing the window size it uses to determine
"stock is at the same percentage", matching more stocks per step and
thereby reducing the number of steps required to complete the purchase,
at the expense of less-precisely duplicating the original motif's
percentages.

If a slop amount is provided, the script will keep recalculating sets
of purchase steps until either it reaches the slop amount or it runs
out of steps to compress, and just makes a one-step buy that divides
the amount spent equally across all the stocks (the same as if you'd
created the slice, and then spent the requisite amount on it).
"""

# Ensure our variables are marked uninitialized
investment = None
maxSlop = None
loaded = False

def help():
    print("slicer.py -investment dollars -maxslop dollars -file motif.yaml")

shortOpt = 'hi:m:f:'
longOpt  = ['investment=', 'maxslop=', 'file=']
try:
    arguments, values = getopt.getopt(sys.argv[1:], shortOpt, longOpt)
except getopt.error as err:
    print(str(err))
    sys.exit(2)

for arg, val in arguments:
    if arg in ("-i", "-investment"):
        investment = float(val)
    if arg in ("-m", "-maxslop"):
        maxSlop = float(val)
    if arg in ('-f', '-file'):
        with open(val) as file:
            original = yaml.full_load(file)
            loaded = True
            total = 0
            for k in original.keys():
                total = total + original[k]
            total = float("{0:.1f}".format(total))
            if total > 100.0 or total < 100.0:
                print("Percentages sum to {0:.2f}".format(total))
                sys.exit(2)
    if arg in ("-h", '-help'):
        help()
        sys.exit(0)

if investment is None or not loaded:
    print("Insufficient arguments:")
    help()
    sys.exit(2)

# Initial process: start with the Schwab distribution and
# iterate to the Motif distribution. We operate in percentages
# to prevent propagation of floating-point imprecision.
# Each iteration fixes the stock with the next-highest percentage
# and evenly distributes the remainder until we've reached the
# original Motif distribution. We record each iteration for the
# second pass.

# Calculate an even distribution over the keys.
slots = len(original.keys())
spendPerSlot = investment / slots

# Invert the original distribution so we can iterate
# over the stocks in descending precentage order.
inverted = {}
for k in original.keys():
    if original[k] in inverted.keys():
        inverted[original[k]].append(k)
    else:
        inverted[original[k]] = [k]

# Now go through the inverted Motif in order of
# percentage descending. Ties are broken arbitrarily
# but will occur together.
priority = []
for k in sorted(inverted.keys(), reverse=True):
    for stock in inverted[k]:
        priority.append(stock)
percent = []
for k in priority:
    percent.append(original[k])

results = []

# First result is an even split. (Schwab)
results.append({})
for s in priority:
    results[0][s] = 100.0 / len(priority)
# Last result splits by percentages given. (Motif)
motif = {}
for s in priority:
    motif[s] = original[s]

# Subsequent results fix the spend in priority order,
# then divide the remaining investment into the rest
# of the slots.
nextResult = 0
fixedPoint = -1
done = False

while not done:
    nextResult = nextResult + 1
    fixedPoint = fixedPoint + 1

    # Calculate items left to evenly fill.
    size = len(priority) - fixedPoint - 1
    if size == 1:
        break

    # New result set
    results.append({})

    # Copy the current fixed points into the new result.
    used = 0
    i = fixedPoint
    for i in range(0, fixedPoint+1):
        stock = priority[i]
        results[nextResult][stock] = percent[i]
        used = used + percent[i]

    # Calculate the fixed amount spent, and the remaining
    # to be split evenly.
    remaining = 100.0 - used

    slice = remaining / size

    for i in range(fixedPoint+1, len(priority)):
        stock = priority[i]
        results[nextResult][stock] = slice

results.append(motif)

for result in results:
    for stock in priority:
        print("{0}: {1}".format(stock, result[stock]))
    print("-"*80)


sys.exit(0)
