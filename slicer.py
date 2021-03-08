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
    if arg in ("-h", '-help'):
        help()
        sys.exit(0)

if investment is None or not loaded:
    print("Insufficient arguments:")
    help()
    sys.exit(2)

# If no slop is specified, we'll just do what we need to do to
# duplicate the original buy.
if maxSlop is None:
    maxSlop = 0.00

# width of the percentage window
epsilon = 0.0

# Saves deltas between the percentage sizes
deltas = []

# First run through we capture the deltas;
# subsequent times we'll pop one off and use it.
# We stop when we're at the final (no changes) delta.
first = True
done = False

# Lets us skip displaying an iteration if the slop hasn't
# increased.
lastSlop = -1.00
slop = 0.00

while not done:
    # Capture the output instead of printing. If the
    # slop doesn't increase with the increased epsilon,
    # there's no point in showing the output.
    output = []

    # Step counter shows us the step we're at in buying the
    # slices to recreate the motif distribution.
    step = 1

    # Sums up the amount spent in purchasing the slice using
    # the current plan. Compared to the investment amount to
    # see how much slop has been introduced.
    totalizedInvestment = 0.0

    # Used to print the final summary report of the distribution
    # for each iteration.
    spendage = {}

    # Always start with a copy of the original distribution.
    motif = original.copy()

    # Find and remove the lowest percentages in the epsilon
    # window until there are no stocks left to purchase.
    while motif.keys():
      # Find minimum percentage.
      minstock = ""
      minpercent = 100.0
      for k in motif.keys():
          if motif[k] < minpercent:
              minstock = k
              minpercent = motif[k]
      # Record the deltas on the initial iteration.
      if first:
          deltas.append(minpercent)
      # The step cost is how much this iteration's purchase of
      # the slice should cost.
      stepCost =  investment * minpercent/100

      # Schwab rule: the minimum spend on a slice is $5.00.
      # If the step cost would be less than that, we've got
      # to add some slop to make this step bigger.

      # Add the current steps's cost to the total.
      totalizedInvestment = totalizedInvestment + stepCost * len(motif.keys())

      # Save the step header.
      output.append("Step {0}: ${1:.2f}".format(step, stepCost))
      dropped = []

      # Calcualte the amount we should spend for each stock in this
      # step of the slice purchase.
      size = len(motif.keys())
      spendForKey = stepCost / size

      # Add this to the total spent for each of the stocks so far.
      # Drop any stock whose percentage is in the current minimum
      # percentage window.
      for k in list(motif):
        if k not in spendage:
            spendage[k] = 0
        spendage[k] = spendage[k] + stepCost
        percent = motif[k]
        if percent >=  minpercent - epsilon and percent <= minpercent + epsilon:
            dropped.append(k)
            motif.pop(k, None)
        else:
            motif[k] = motif[k] - minpercent
      # Add a report of the stocks to remove from the slice for the next
      # purchase.
      output.append("Drop: {0}".format(', '.join(dropped)))

      # Moving on to the next step.
      step = step + 1

    # Iteration complete. Figure out how close we were to the desired investment.
    # Add this to the top to make it easy to decide how good this iteration was.
    slop = abs(investment - totalizedInvestment)
    output.insert(0,("${0:.2f} ({1:.2f}%) slop\n".format(slop, slop/investment*100)))
    # Show how much was spent per stock symbol.
    for k in spendage.keys():
        output.append("{0}\t${1:.2f}".format(k, spendage[k]))
    # Divider line.
    output.append("-"*80)

    # Turn off recording of the deltas, since we've already got all of them.
    first = False

    # If the slop has increased  over the last time around, print the report.
    # Record the current slop so we can check if it increased on the next iteration.
    if slop > lastSlop:
        for line in output:
            print(line)
    lastSlop = slop

    # If the slop hasn't exceeded the limit, make the window bigger (causing us
    # to delete more stocks on each loop doing the spend). This will eventually
    # increase the slop to the limit, or if the limit is set too high, we'll
    # eventually stop when we run out of deltas.
    if slop <= maxSlop:
        if len(deltas) > 0:
            epsilon = epsilon + deltas.pop(0)
        else:
            done = True
    else:
        done = True
