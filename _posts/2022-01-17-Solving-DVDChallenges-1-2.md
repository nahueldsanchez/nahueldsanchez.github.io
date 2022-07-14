---
layout: post
title:  Solving Damn Vulnerable DeFi Challenges Series. Unstoppable and Naive Receiver
excerpt_separator: <!--more-->
category: DeFi
---

Hello! In today's short blog post I'll quickly explain how I solved [Damn Vulnerable DeFi Challenges](https://www.damnvulnerabledefi.xyz/) "Unstoppable" and "Naive Receiver".

<!--more-->

# Solution for Challenge #1, Unstoppable

if we take a look at [UnstoppableLender](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/unstoppable/UnstoppableLender.sol) contract we'll find a function called `depositTokens` that, between other things, receives the funds for the pool and updates the `poolBalance` variable. Later, when the function in charge of processing the flash loan (`flashLoan` function) is executed, there is an assert in line 40 that checks that `poolBalance` equals `balanceBefore` before transferring the funds to the borrower. If for some reason this is not true the assert does not pass and the transaction is reverted:

```
...
// Ensured by the protocol via the `depositTokens` function
        assert(poolBalance == balanceBefore);
...
```

At first glance it seems that the only way to modify the value of the contract's balance is calling `depositTokens` function, so this assert should be always True, as the poolBalance variable will be always updated.

## The vulnerability 
The vulnerability relies in the fact that the contract does not expect to receive tokens in any other way. An attacker can abuse this assumption, issuing a transfer from an account. In doing so, it will be possible to modify the value of the contract's balance without running the code in charge of updating the `poolBalance` variable, making the assertion in line 40 to fail, as the left operand of the previous mentioned assertion is computed in the following way:

```
...
uint256 balanceBefore = damnValuableToken.balanceOf(address(this));
...
```

In simpler words, the contract's balance is used. As the attacker has deposited Ether, the balance won't be equal to "poolBalance" variable value and therefore the assertion will fail
rendering the contract unusable.

You can check my solution in [my port of this challenge to Brownie](https://github.com/nahueldsanchez/dvd_brownie/tree/master/unstoppable). [Solution here](https://github.com/nahueldsanchez/dvd_brownie/blob/master/unstoppable/scripts/exploit.py)


# Solution for Challenge #2, Naive Receiver

In this case the contract that we need to hack [NaiveReceiverLenderPool](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/naive-receiver/NaiveReceiverLenderPool.sol) has a function called `flashLoan` that takes as parameters two values: An Address `borrower` and an Unsigned Integer `borrowAmount` that represents how much will be borrowed.

The interesting – and potentially dangerous – behavior is that anyone can specify an arbitrary address as borrower. When the function "flashLoan" is executed the contract will try to execute a function called `receiveEther` assuming that the address passed as borrower is a contract that has that function.

The aforementioned behavior, alone, won't present any immediate risks. However, in this scenario, we are given a contract [FlashLoanReceiver](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/naive-receiver/FlashLoanReceiver.sol) that acts as the receiver of the borrowed amount. The problem relies in the fact that the function executed by
this contract, `receiveEther` includes a logic to repay the borrow and also include the fee associated with the transaction (borrowing has a cost of 1 eth in this scenario).

This fee is paid to the pool in the following way

```
...
uint256 amountToBeRepaid = msg.value + fee;
pool.sendValue(amountToBeRepaid);
...
```

## The exploit

An attacker can invoke `flashLoan` in the `NaiveReceiverLenderPool`, sending as borrower the victim address. Doing this, it will trick the pool into calling the function `receiveEther` in the `FlashLoanReceiver` contract, draining 1 Ether back to the pool. This can be repeated N times. However, there is a better alternative to perform this attack. If the attacker deploys a malicious contract, [AttackerContract](https://github.com/nahueldsanchez/dvd_brownie/blob/master/naive-receiver/contracts/AttackerContract.sol) in my solution, the same attack can be performed just with one transaction. The attacker contract will make N calls (messages) to the vulnerable contract.


I hope that you have enjoyed these solutions as much as I enjoyed finding them. In the next series of this topic I'll continue solving challenges #3 and #4. Stay tuned!


