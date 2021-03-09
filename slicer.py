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

def buildPurchase(results):
    """
    buildPurchase takes the dict of stock-to-percentage
    mappings and constructs a set of slice purchases that
    will total up to the full amount.
    """

    # Find the smallest percentages in the struct.
    inverted = invert(results)
    percents = sorted(inverted.keys())
    purchases = []

    while len(results.keys())> 0:
        # Find the smallest contributor to the final result
        smallest =  percents.pop(0)
        # Buy this much of everything left in result, saving it
        purchases.append({key: smallest for (key, value) in results.items()})
        # subtract percentage from all items in result, dropping zeroed items
        results = {k:v-smallest for (k,v) in results.items() if v != smallest}
        # Reduce percentages left to purchase by amount already purchased
        percents = [v-smallest for v in percents]

    return purchases

def help():
    print("slicer.py -investment dollars -maxslop dollars -file motif.yaml")

def invert(original):
    """
    Invert a dict, making the values the keys. The old keys are
    stored as lists so that collisions are kept.
    """
    inverted = {}
    for k in original.keys():
        if original[k] in inverted.keys():
            inverted[original[k]].append(k)
        else:
            inverted[original[k]] = [k]
    return inverted

def processCLI():
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
    return original, investment, maxSlop

# Initial process: start with the Schwab distribution and
# iterate to the Motif distribution. We operate in percentages
# to prevent propagation of floating-point imprecision.
# Each iteration fixes the stock with the next-highest percentage
# and evenly distributes the remainder until we've reached the
# original Motif distribution. We record each iteration for the
# second pass.
original, investment, maxSlop = processCLI()

# Invert the original distribution so we can iterate
# over the stocks in descending percentage order.
inverted = invert(original)

# Determine priority to purchase stocks. Stocks with the
# highest percentage are considered more important than
# the smaller contributors.
priority = []
for k in sorted(inverted.keys(), reverse=True):
    for stock in inverted[k]:
        priority.append(stock)
# Get a list of the percentages in priority order as well.
percent = []
for k in priority:
    percent.append(original[k])

results = []

# First result is an even split. (Schwab)
fixedPercentage = 100.0 / len(priority)
results.append({k:fixedPercentage for (k,v) in original.items()})

nextResult = 0
fixedPoint = -1
done = False

while not done:
    fixedPoint = fixedPoint + 1

    # Calculate items left to evenly fill.
    size = len(priority) - fixedPoint - 1
    if size == 1:
        break

    # New result set
    result = {}

    # Copy the current fixed points into the new result.
    # Calculate the total fixed percentage as we set it up.
    used = 0
    i = fixedPoint
    for i in range(0, fixedPoint+1):
        stock = priority[i]
        result[stock] = percent[i]
        used = used + percent[i]

    # Calculate the fixed amount spent, and the remaining
    # to be split evenly.
    remaining = 100.0 - used

    # Figure out the even split for the rest of the slice.
    split = remaining / size

    for i in range(fixedPoint+1, len(priority)):
        stock = priority[i]
        result[stock] = split

    # Save the current result.
    results.append(result.copy())

# Add the original version to the result.
results.append(original)

# Show the results, and the purchase strategy for each.
for result in results:
    for stock in priority:
        print("{0}: {1}".format(stock, result[stock]))
    print("-"*80)
    print(buildPurchase(result.copy()))
    print("="*80)

sys.exit(0)
