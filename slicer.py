import getopt, sys, yaml

"""
This script uses the motif percentages to decide how to
construct a Schwab stock "slice" that exactly duplicates
the distribution that was in the original motif.

The following multi-step process reproduces the distribution:
    - For each step:
        - Find the stock that is the smallest contribution (in percent)
          to the total purchase. This is the percentage we will need to
          spend in this step on the remaining stocks.
        - Display this purchase.
        - Remove the stock and any others at this percentage from the
          list of stocks.
        - Repeat until there is only one stock left, and spend all the
          remaining percentage on it.

This may take a number of steps if the motif had a lot of stocks in it
with different percentages (worst case, there will need to be a step
for each stock in the motif).
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
    dropped = []
    lastBuy = results.keys()

    while len(results.keys())> 0:
        # Find the smallest contributor to the final result
        smallest =  percents.pop(0)
        # Buy this much of everything left in result, saving it
        purchases.append({key: smallest for (key, value) in results.items()})
        # subtract percentage from all items in result, dropping zeroed items
        results = {k:v-smallest for (k,v) in results.items() if v != smallest}
        # Determine items dropped this time
        currentBuy = results.keys()
        dropped.append([v for v in lastBuy if v not in currentBuy])
        lastBuy = currentBuy
        # Reduce percentages left to purchase by amount already purchased
        percents = [v-smallest for v in percents]

    return purchases, dropped

def minPurchase(amount):
    if amount < 5.00:
        return 5.00
    return amount

def help():
    print("slicer.py -investment dollars -file motif.yaml")

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
    shortOpt = 'hi:f:'
    longOpt  = ['investment=', 'file=']
    try:
        arguments, values = getopt.getopt(sys.argv[1:], shortOpt, longOpt)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)

    for arg, val in arguments:
        if arg in ("-i", "-investment"):
            investment = float(val)
        if arg in ('-f', '-file'):
            with open(val) as file:
                original = yaml.full_load(file)
                loaded = True
        if arg in ("-h", '-help'):
            help()
            sys.exit(0)

    if investment is None or not loaded:
        print("Insufficient arguments:")
        help()
        sys.exit(2)
    total = 0
    for k in original.keys():
        total = total + original[k]
    total = float("{0:.1f}".format(total))
    if total != 100.0:
        print ("Autoscaling from {0:.2f}% to 100%".format(total))
        factor = 100.0/total
        for k in original.keys():
            original[k] = original[k] * factor
        investment = investment / factor
        print("Reducing total investment to {0:.2f}".format(investment))
    return original, investment

# Initial process: start with the Schwab distribution and
# iterate to the Motif distribution. We operate in percentages
# to prevent propagation of floating-point imprecision.
# Each iteration fixes the stock with the next-highest percentage
# and evenly distributes the remainder until we've reached the
# original Motif distribution. We record each iteration for the
# second pass.
original, investment = processCLI()

nextResult = 0
fixedPoint = -1
done = False

priority = []
inverted = invert(original)
for p in inverted.keys():
    stocks = inverted[p]
    for stock in stocks:
        priority.append(stock)

# Show the results, and the purchase strategy for each.
for stock in priority:
    print("{0}:\t{1:.1f}%".format(stock, original[stock]))
print("="*80)
purchase, dropped = buildPurchase(original)
step = 0
for buy in purchase:
    step = step + 1
    drops = dropped.pop(0)
    stocks = list(buy.keys())
    stock = stocks[0]
    purchase = buy[stock]*investment/100
    required = minPurchase(buy[stock]*investment/100)
    note = ""
    if purchase != required:
        note = '*'
    print("Step {0}: buy {1} at ${2:.2f}{3}".format(step, ', '.join(stocks), required, note))
    print("\nDrop:\t{0}".format(', '.join(drops)))
    print("-"*80)
print("Summary:")
for stock in priority:
    print("{0}:\t${1:.2f}".format(stock, original[stock]*investment/100))

sys.exit(0)
