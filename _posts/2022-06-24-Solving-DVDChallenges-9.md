---
layout: post
title:  Solving Damn Vulnerable DeFi Challenges Series (VI). Puppet V2
excerpt_separator: <!--more-->
category: DeFi
---

Hi there! coming back to some writing after a long break. Today's post continues the saga on Damn Vulnerable DeFi Challenges. I solved and ported to my project [Damn Vulnerable DeFi Challenges in Brownie](https://github.com/nahueldsanchez/dvd_brownie),  [challenge #9, "Puppet V2"](https://www.damnvulnerabledefi.xyz/challenges/9.html). I hope that you enjoy it.
<!--more-->

# Solving Puppet v2 Challenge

As with the previous challenge, the most complicated part was to actually deploy Uniswap V2 in Brownie. It took me a lot of work. Luckily the process was a bit similar than for the previous challenge.

Coming back at the challenge itself, we are presented with the following statement:

```
The developers of the last lending pool are saying that they've learned the lesson. And just released a new version!

Now they're using a Uniswap v2 exchange as a price oracle, along with the recommended utility libraries. That should be enough.

You start with 20 ETH and 10000 DVT tokens in balance. The new lending pool has a million DVT tokens in balance. You know what to do ;)
```

The challenge looks similar to the previous one, but this time, developers are using Uniswap's own functions to calculate prices. This should make the system secure, at least, in theory.

I started reviewing how the pool calculated the amount of ETH was needed to be deposited as collateral to borrow DVT tokens. For this, there is a function called `calculateDepositOfWETHRequired`, which calls `_getOracleQuote` and multiplies the returned value by 3.

The underlying idea while doing this is that to borrow some DVT tokens, the user must first deposit a collateral in ETH equivalent to three times the amount of DVT. To calculate this equivalent value, the pool needs to know what's the relationship between ETH and DVT. To know this it uses `_getOracleQuote`, pasted below:


```
function _getOracleQuote(uint256 amount) private view returns (uint256) {
    (uint256 reservesWETH, uint256 reservesToken) = UniswapV2Library.getReserves(
        _uniswapFactory, address(_weth), address(_token)
    );
    return UniswapV2Library.quote(amount.mul(10 ** 18), reservesToken, reservesWETH);
}
```

As you can see, it uses two functions from Uniswap V2: [`getReserves`](https://docs.uniswap.org/protocol/V2/reference/smart-contracts/library#getreserves) and [`quote`](https://docs.uniswap.org/protocol/V2/reference/smart-contracts/library#quote)

According to the [docs](https://docs.uniswap.org/protocol/V2/introduction), `getReserves` expects a pair of tokens (wETH and DVT in our case) and returns the current amount of these tokens in the pool. This is used as input for `quote` that expects the amount of some asset A and its reserves along with the reserves of another token B and returns an amount of these tokens B equivalent to the input value.

Based on all this information I decided to go and check how `quote` worked, as it is finally the key piece that determines how much we need to deposit:

```
// given some amount of an asset and pair reserves, returns an equivalent amount of the other asset

function quote(uint amountA, uint reserveA, uint reserveB) internal pure returns (uint amountB) {
    require(amountA > 0, 'UniswapV2Library: INSUFFICIENT_AMOUNT');
    require(reserveA > 0 && reserveB > 0, 'UniswapV2Library: INSUFFICIENT_LIQUIDITY');
    amountB = amountA.mul(reserveB) / reserveA;
}
```

- `amountA` is the amount of DVT tokens the user plans to borrow.
- `reserveA` is the amount of DVT tokens the pool has.
- `reserveB` is the amount of wETH the pool has.

After looking at this code and thinking what an attacker can control, a solution for this challenge started to take some form. Let's analyze the starting scenario and a potential attack.

To pass the challenge the attacker needs to take all DVT tokens from the lending pool. For us this sets `amountA` to `1.000.000`. `reserveA` is how much DVT tokens UNISWAP's pool has, `100 DVTs` in our case `reserveB` equals to the amount of wETH in UNISWAP, `10 wETH`. Under normal circumstances the equivalent amount of wETH for 1.000.000 DVT tokens will be:

``` wETH = (1.000.000 * 10) / 100 = 100.000 ```

Remember that this value is later multiplied by 3. So, an attacker will need 300.000 wETH to pass the challenge, but it only has 20!, well let's see what it can be done to change the scenario to obtain a better ratio.

## Solution

If the attacker is able to drain Uniswap's wETH reserves and increase the amount of DVT tokens (reserveA, the denominator) the result of the calculation will be lower, making the final value of `amountB` smaller. Turns out that the attacker can do this!, as it has an initial balance of `10.000 DVT tokens` that can be swapped for wETH. Let's see how much ETH the attacker might expect receive for this trade. To calculate this we can use Uniswap's V2 Router function [`getAmountOut`](https://docs.uniswap.org/protocol/V2/reference/smart-contracts/library#getamountout):

This function expects the following arguments:

- An input asset. In our case 10.000 (DVT Tokens)
- The amount of that assets in the reserves. 100 DVTs for us.
- The amount in reserves of the other asset. For us this is 10 (As Uniswap pool has 10 ETH).

```getAmountOut(10000, 100, 10) == 9.900```

_Note: For clarity's sake, I'm simplifying units._

Based on this, if the attacker makes this swap, the scenario used to calculate the collateral after the trade will be:

- `amountA` is the amount of DVT tokens the user plans to borrow. Nothing changes here: 1.000.000
- `reserveA` Now is: 10.100 DVTs.
- `reserveB` Now is: 0.1 wETH.

And based on this, if we recalculate the amount of ETH needed to borrow 1.000.000 DVTs we'll obtain:

``` wETH = (1.000.000 * 0.1) / 10100 = 9.90 ```

This value is later multiplied by 3. Now if we ask the lending pool how much wETH is needed to borrow 1.000.000 DVTs we obtain:

```
>>> lp.calculateDepositOfWETHRequired(1000000)
29
```

As the attacker starts with 20 ETH and swapped his 10.000 DVTs for 9.90 ETh, now it will be possible to borrow all the DVTs from the pool. Challenge passed!

I've implemented this challenge and the proposed solution [here](https://github.com/nahueldsanchez/dvd_brownie/tree/master/puppet-v2).

## Conclusion

I think that this challenge teaches us a very valuable lesson. Even though developers did everything right and used trusted functions to perform calculations, still it was possible for an attacker to drain the pool. It's very important not only focus on securing and hardening the code but also carefully thinking about all potential scenarios involving liquidity and how external parties can interact with it.

I hope you enjoyed the post, if you have any question do not hesitate reaching out.

## Sources

- [Uniswap docs](https://docs.uniswap.org/) - https://docs.uniswap.org/
- [UNPKG](https://unpkg.com/browse/@uniswap/v2-core@1.0.1/build/) - https://unpkg.com/browse/@uniswap/v2-core@1.0.1/build/
- [Uniswap contract walk-through](https://ethereum.org/en/developers/tutorials/uniswap-v2-annotated-code/#uniswapV2library) - https://ethereum.org/en/developers/tutorials/uniswap-v2-annotated-code/#uniswapV2library