---
layout: post
title:  Solving Damn Vulnerable DeFi Challenges Series (II). Truster and Side entrance
excerpt_separator: <!--more-->
category: DeFi
---

Hello there! Continuing with Damn Vulnerable DeFi Challenges, in today's post I share my solutions for challenges #3 - Truster, and #4 - Side entrance.

<!--more-->

# Solution for Truster Challenge

I started reviewing the [TrusterLenderPool](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/truster/TrusterLenderPool.sol) code and in the `flashLoan` function I identified the following line that caught my attention:

```
...
target.functionCall(data);
...
```

After reading a bit of Solidity documentation I understood that it is possible to make a "target" call an arbitrary function. The idea behind this is: Once the pool lends the tokens to the borrower, this line should be used to call a function in the borrower's code that it should repay the debt before finishing the flash loan.

## The vulnerability

The issue relies on the fact that the "target" it is not fixed, and then, a malicious user can use this code to trick the TrustedLenderPool into executing a call to an arbitrary
function in an arbitrary destination. My next question was, How this behavior can be leveraged by an attacker?

After thinking a lot about this I found the following attack vector:

If an attacker is able to trick the TrusterLenderPool into calling function [approve](https://docs.openzeppelin.com/contracts/2.x/api/token/erc20#IERC20-approve-address-uint256-) from the IERC20 Token `DamnValuableToken` it will be possible for him to allow a transfer of the aforementioned tokens from the TrusterLenderPool back to him.

## Solution

Based on this idea I developed the AttackerContract contract that at high level performs these tasks:

1. Executes the "flashLoan" function from TrustedLenderPool borrowing 0 tokens.
2. As `target` for the `target.functionCall(data)` it sets the address of the DamnValuableToken, and as function to call (data) the `approve(address,uint256)` function. Doing this, it tricks the `TrusterLenderPool` into executing a call to `DamnValuableToken` approving the spending of X tokens to his (attacker) address.
3. Once the flashLoan finishes, it then executes `transferFrom` function from DamnValuableToken, transferring tokens from the `TrustedLenderPool` back to the Attacker. Remember that this was previously allowed in step 2.

All of these steps are executed in the constructor function, so it is only needed one transaction (the deployment of the attacker contract). Kudos to Pablo Artuso that gave me this little hint. You can read his solution for these challenges [here](https://lmkalg.github.io/).

You can find my solution [here](https://github.com/nahueldsanchez/dvd_brownie/blob/master/truster/contracts/AttackerContract.sol).

# Solution for Side entrance challenge

If we take a look at the [SideEntranceLenderPool code](https://github.com/nahueldsanchez/dvd_brownie/blob/master/side-entrance/contracts/SideEntranceLenderPool.sol) and compare it with the previous challenge, we can see this time the arbitrary call that we exploited before has been fixed. In this case the Pool calls a function named `execute` in the contract who executed the `flashLoan` function:

```
...
IFlashLoanEtherReceiver(msg.sender).execute{value: amount}()
...
```

This behavior prevent us from exploiting the contract in the same way we solved the previous challenge. So, where is the problem?.

If we look at the last `require` statement in the `flashLoan` function we can see that it uses `this.balance` to check if the loan has been paid. This allowed me to try to find ways to change the contract's balance and I quickly found that this pool had the `deposit` function implemented and with that I found the root problem.

## The vulnerability

The main problem in my opinion is that the Pool does not distinguish who owns the ethers deposited when verifying balances. An attacker could be able to perform the following steps:

1. He asks for a flashLoan of X ethers.
2. It then proceeds to deposit the borrowed funds into the Lender Pool.
3. The flashLoan continues its execution and the final assert is verified.
4. As the attacker already deposited the funds (this).balance >= balanceBefore
5. But now, the Ether deposited by the attacker (the borrowed Ether) can be withdrawn, as he deposited it, and then, he owns it.

## Solution

With this idea in mind I created attackerContract that performs these steps.

It asks for the Loan and uses the callback made by the LenderPool to deposit the borrowed Ether. When the flash loan finishes, it withdraws the previously deposited funds.

The solution for this challenge is all in [AttackerContract.sol](https://github.com/nahueldsanchez/dvd_brownie/blob/master/side-entrance/contracts/AttackerContract.sol) in my repository.
