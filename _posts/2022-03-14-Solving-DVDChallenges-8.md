---
layout: post
title:  Solving Damn Vulnerable Defi Challenges Series (V). Puppet
excerpt_separator: <!--more-->
---

Hello, coming back from some holidays! I had some time to continue solving Damn Vulnerable Defi Challenges. Today's post explains the way I approached and solved [Challenge 8 - Puppet](https://www.damnvulnerabledefi.xyz/challenges/8.html). Enjoy!.

<!--more-->

# Solving Puppet Challenge

This challenge was harder to deploy in Brownie than solving it!, at least for me. It required to deploy an instance of [Uniswap](https://es.cointelegraph.com/explained/what-is-uniswap-and-how-does-it-work) V1 to work. I had to invest some time learning how to deploy it and also [learning how others done it](https://github.com/wuwe1/damn-vulnerable-defi-brownie/blob/ec115648cc319811ef09519c433bce9772753cd9/tests/test_puppet.py).

In this challenge we are presented with the following statement:

```
There's a huge lending pool borrowing Damn Valuable Tokens (DVTs), where you first need to deposit twice the borrow amount in ETH as collateral. The pool currently has 100000 DVTs in liquidity.

There's a DVT market opened in an Uniswap v1 exchange, currently with 10 ETH and 10 DVT in liquidity.

Starting with 25 ETH and 1000 DVTs in balance, you must steal all tokens from the lending pool.
```

Based on the statement and looking at the [Pool's contract](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/puppet/PuppetPool.sol) I looked how the pool performed the most critical actions:

## Borrowing function analysis

First I reviewed how the borrowing function worked:

```
// Allows borrowing `borrowAmount` of tokens by first depositing two times their value in ETH
    function borrow(uint256 borrowAmount) public payable nonReentrant {
        uint256 depositRequired = calculateDepositRequired(borrowAmount);
        
        require(msg.value >= depositRequired, "Not depositing enough collateral");
        
        if (msg.value > depositRequired) {
            payable(msg.sender).sendValue(msg.value - depositRequired);
        }

        deposits[msg.sender] = deposits[msg.sender] + depositRequired;

        // Fails if the pool doesn't have enough tokens in liquidity
        require(token.transfer(msg.sender, borrowAmount), "Transfer failed");

        emit Borrowed(msg.sender, depositRequired, borrowAmount);
    }
```

As we can see it first calculates how much the user has to deposit as collateral via `calculateDepositRequired` (more on this later).

Later, it checks that these amount was sent by the user via `msg.value`.

If everything is OK, in tries to transfer the borrowed amount back to the user (it will fail if the pool does not have enough tokens).

So nothing extrange here. Once I finished with this function I decided to take a look at `calculateDepositRequired` which is another critical function that defines how much the user needs to deposit!, let's take a look at it.

## Calculating deposits required as collateral

Function `calculateDepositRequired` is implemented like this:

```
function calculateDepositRequired(uint256 amount) public view returns (uint256) {
        return amount * _computeOraclePrice() * 2 / 10 ** 18;
    }
```

So, nothing complicated, I assumed that some price was returned from an Oracle, and took a look at the `_computeOraclePrice()` function:

```
function _computeOraclePrice() private view returns (uint256) {
        // calculates the price of the token in wei according to Uniswap pair
        return uniswapPair.balance * (10 ** 18) / token.balanceOf(uniswapPair);
    }
```

This is interesting!.  The price returned by this function depends on two things:

1. The balance of `uniswapPair`.
2. The amount of DVT tokens that `uniswapPair` has.

So it was key to understand what `uniswapPair` was. Looking at the contract's code we can see that this variable is passed upon initialization in the contract's constructor:

```
    constructor (address tokenAddress, address uniswapPairAddress) {
        token = DamnValuableToken(tokenAddress);
        uniswapPair = uniswapPairAddress;
    }
```

Looking at the code in charge of deploying the contract we finally uderstand that this variable holds the address of the Uniswap Exchange:

```
// Deploy the lending pool
        this.lendingPool = await PuppetPoolFactory.deploy(
            this.token.address,
            this.uniswapExchange.address
        );
```

Now with all the parts in place, let's analyze the problem again:

The goal for the attacker is to steal all the DVT tokens from the pool. The problem is that to borrow 100000 DVTs, and under normal circumnstances, *twice* the amount in ETH is needed to be deposited as collateral. The attacker only has 25 ETH.

To be true the fact that twice the amount of ETH has to be deposited, `_computeOraclePrice()` must return `1`. This is true only if the relationship between `uniswapPair.balance` and `token.balanceOf(uniswapPair)` is 1:1. By default, the pool has 10 ETH and 10 DVT, and hence, the function returns 1.

And here relies the key issue that we will exploit to solve the challenge!

## Solution

The attacker can manipulate this relationship. If the exchange's ETH balance (uniswapPair.balance) is 0 (or close), the result of the division `uniswapPair.balance * (10 ** 18) / token.balanceOf(uniswapPair)` will be 0 or a very small number.

To perform this attack,  an attacker could swap his DVT tokens for ETH, lowering the Exchange's ETH balance to a small number (or 0) and then borrow all the Pool's DVT tokens having to deposit as collateral nearly 0 ETH.

I implemented this solution [here](https://github.com/nahueldsanchez/dvd_brownie/tree/master/puppet). I also ported this challenge to Brownie, you can find it [here](https://github.com/nahueldsanchez/dvd_brownie/) along with all the previous ones.

Thanks for reading!.

## Sources

- https://es.cointelegraph.com/explained/what-is-uniswap-and-how-does-it-work
- https://github.com/wuwe1/damn-vulnerable-defi-brownie
