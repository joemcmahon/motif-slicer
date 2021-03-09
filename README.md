# motif-slicer
Converts Motif fractional investment setups to buys of Schwab "slices"

    python slicer.py -i $dollar-amount -f motif.yml

where `motif.yml` defines a mapping of stock symbols to percentages:

    # For illustrative purposes only; make your own calls on investments!
    AAPL: 25.4
    MSFT: 33.2
    FB:   10.1
    AMZN: 32.3

## Sample output

    Autoscaling from 101.00% to 100%
    Increasing total investment to 10100.00
    AAPL:	25.1%
    MSFT:	32.9%
    FB:	10.0%
    AMZN:	32.0%
    ================================================================================
    Step 1: buy AAPL, MSFT, FB, AMZN at $1010.00

    Drop:	FB
    --------------------------------------------------------------------------------
    Step 2: buy AAPL, MSFT, AMZN at $1530.00

    Drop:	AAPL
    --------------------------------------------------------------------------------
    Step 3: buy MSFT, AMZN at $690.00

    Drop:	AMZN
    --------------------------------------------------------------------------------
    Step 4: buy MSFT at $90.00

    Drop:	MSFT
    --------------------------------------------------------------------------------
    Summary:
    AAPL:	$2540.00
    MSFT:	$3320.00
    FB:	$1010.00
    AMZN:	$3230.00

# Disclaimer
I am not a financial advisor. Anything you do with your money is your own responsibility.
I've just built this for my own convenience. If you find it useful, great! Its only
real value is if you specifically want to duplicate the _proportions_ of what you were
doing on Motif in a Schwab investment account. How wise your choices are is up to you.

# Why this script?
When Motif closed down, we lost a really useful investment platform.
Motif allowed you to essentially set up your own mutual funds: add stocks, ETFs,
funds, etc. to a "motif", setting the percentage of the fund that would be directed
to each investment. You could add and remove stocks, and then buy and sell everything as a unit.

The closest reasonable equivalent right now is either Schwab's "slices" or Fidelity's "baskets".
Schwab's slices are more restricted in what you can invest in, but more flexible in buying and selling.

Slices require you to select a set of stocks to invest in; you then put anything from $5 to $50,000 into
that slice, and the money is divided evenly across all the stocks. You then own some fractional multiple
of those stocks -- the expensive ones may be less than 1, and the cheaper say 7.9 and so on. 

Once you've purchased the slice (slices are always market transactions and fire immediately), they're
effectively cut loose from the actual slices; you can then trade the stocks just as if you'd purchased them individually.
The only restriction is that you can't split a fraction -- that is, if you have 0.7 shares of something, 
you can't sell 0.5 shares; it's the whole 0.7 or nothing.

So if we want to come as close as possible to the Motif experience, we'll have to figure out how to map
the Motif arbitrarily-divided purchase into multiple evenly-divided purchases. 

## Mapping from Motif to Schwab
Let's say we had a motif that was 70% AAPL and 30% AMZN, with AAPL selling at $121.42 and AMZN at $3000.46.
At Motif, we could buy $2000 worth of this: 70% would go into AAPL = 70%*$2000/$121.42 = 11.5302 shares of AAPL,
30% * $1000/$3000.46 = 0.0999 shares of AMZN.

At Schwab, a slice with AAPL and AMZN would end up being split 50-50 between the two. We'd need to do this
in multiple steps to get the same result: make an AMZN+AAPL slice and put 30% of the investment into that, then
make another AAPL-only slice at 40% of the investment to get the same result. Note that since we're working with
percentages, the actual buy amounts can easily be calculated for whatever investment value we choose.

This script reads a YAML file containing the stock-to-percentage mappings, and accepts an investment amount.

It then finds the smallest percentage to purchase, creates a dict mapping all the stocks in the original dict
to this smallest percentage, and then both deletes all the stocks with this percentage and reduces the remaining
ones by this percentage. Repeat until all of the percentages are used up and there are no more entries in the
original dict.

# Other considerations
Schwab (as of 03-2021) only allows stocks in the S&P 500 to be purchased in slices; Motif allowed you to pretty
much purchase anything. To make the conversion process easier, the script allows the sum of the percentages to
not be exactly 100% and autoscales the percentages up and the investment down to result in the same final amount
invested as was invested on Motif.

# Shortcomings
This makes the buy process mechanically easy, but the selling process is still relatively labor-intensive.
Unlike Motif, the stocks are no longer associated after purchase, so selling off (say) half of a motif buy
on Schwab will be one sell per stock. 

Luckily, this script can be reused to transform the percentages into
a sell-off amount; just multiply the current value of the stocks in total by the percentage you want to sell
and run the script with the sale amount as the `-investment` argument. 

The last part of the output will show
the amounts spent to buy that investment amount with the percentages used to create the motif, and you can
make the sales based on that.
