import getopt, sys

investment = None
maxSlop = None

def help():
    print("slicer.py -investment=dollars -maxslop=dollars")

shortOpt = 'hi:m:'
longOpt  = ['investment=', 'maxslop=']
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
    if arg in ("-h", '-help'):
        help()
        sys.exit(0)

if investment is None or maxSlop is None:
    print("Insufficient arguments:")
    help()
    sys.exit(2)

original = { "NFLX": 20.1,
          "NKE": 12.4,
          "COST": 10.9,
          "DIS": 8.9,
          "SBUX": 8.8,
          "FDX": 5.3,
          "ILMN": 4.9,
          "CMG": 3.0,
          "HAS": 1.0,
          "PLNT": 0.9,
          "LYFT": 0.9,
          "HCA": 3.2,
          "MASI": 18.4,
          "SFIX": 1.3}
epsilon = 0.0 / 2
deltas = []
first = True
stable = False
lastSlop = -1.00
slop = 0.00
while not stable:
    output = []
    slice = 1
    totalizedInvestment = 0.0
    spendage = {}
    motif = original.copy()
    while motif.keys():
      # Find minimum percentage.
      minstock = ""
      minpercent = 100.0
      for k in motif.keys():
          if motif[k] < minpercent:
              minstock = k
              minpercent = motif[k]
      if first:
          deltas.append(minpercent)
      sliceCost =  investment * minpercent/100
      totalizedInvestment = totalizedInvestment + sliceCost * len(motif.keys())
      output.append("Slice {0}: ${1:.2f}".format(slice, sliceCost))
      dropped = []
      size = len(motif.keys())
      for k in list(motif):
        spendForKey = sliceCost / size
        if k not in spendage:
            spendage[k] = 0
        spendage[k] = spendage[k] + sliceCost
        percent = motif[k]
        if percent >=  minpercent - epsilon and percent <= minpercent + epsilon:
            dropped.append(k)
            motif.pop(k, None)
        else:
            motif[k] = motif[k] - minpercent
      output.append("Drop: {0}".format(', '.join(dropped)))
      slice = slice + 1
    slop = abs(investment - totalizedInvestment)
    output.insert(0,("${0:.2f} ({1:.2f}%) slop\n".format(slop, slop/investment*100)))
    for k in spendage.keys():
        output.append("{0}\t${1:.2f}".format(k, spendage[k]))
    output.append("-"*80)
    first = False
    if slop > lastSlop:
        for line in output:
            print(line)
    lastSlop = slop
    if slop <= maxSlop:
        if len(deltas) > 1:
            epsilon = epsilon + deltas.pop(0)
        else:
            stable = True
    else:
        stable = True
