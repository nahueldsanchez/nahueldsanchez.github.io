---
layout: post
title:  Solving Damn Vulnerable Defi Challenges Series (III). The rewarder and Selfie
excerpt_separator: <!--more-->
---

Hello!. Today's post continues with the Damn Vulnerable Defi Challenges saga. I'll share my solutions for challenges #5 - The rewarder and #6 - Selfie. I hope that you find it useful!.

<!--more-->

# The rewarder, Solution

I started reviewing how the Contract in charge of paying rewards [TheRewarderPool](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/the-rewarder/TheRewarderPool.sol) worked. I found that it used the concept of snapshots to take "pictures" of the balances that users have at certain point in time.

This pool used the [AccountingToken contract](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/the-rewarder/AccountingToken.sol) for this purpose based on OpenZeppelin's [ERC20Snapshot](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/extensions/ERC20Snapshot.sol). I didn't find any issues there so I continued looking.

## Snapshots... who and when?

I reviewed how these snapshots were taken and, more important, when. I found that there was a private method `_recordSnapshot()` that triggered the snapshot mechanism. This method is also called via public function `snapshot()`, part of [AccountingToken](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/the-rewarder/AccountingToken.sol#L37). But this public function implements access controls, which means that to be able to take an snapshot using it, the attacker needs the `SNAPSHOT_ROLE` role.

`_recordSnapshot()` was also called by the Contract's constructor (not useful for an attacker), and finally,  from `distributeRewards` Public method!. This last part presented an interesting posibility from an attacker's point of view.

`distributeRewards` was the method used by the Rewarder Pool to pay the rewards to the users who deposited the liquidity tokens and waited the required amount of time. The method checked [if it was time for a new rewards round](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/the-rewarder/TheRewarderPool.sol#L68) and if it was, took and snapshot. After this step, *it performed all calculations based on the balances of that snapshot*. As this is a
public method anyone can call it. Having this in mind and based on the problem statement:

_But in the upcoming round, you must claim most rewards for yourself._

## The Solution

I started to see a potential attack path:

1. The attacker waits until the next rewards Round starts.
2. As soon as this happens asks for a flash Loan.
3. It deposits the Borrowed DVTs into the RewardPool.
4. It calls "distributeRewards". If he's the first to call it a new snapshot will be
taken, taking into account the deposited DVTs from the flash Loan!.
5. It receives the rewards (as the checks performed in TheRewarderPool's line 86
will pass, due to the fact that the attacker did not retrieve rewards before).
6. The attacker proceeds to withdraw the previously deposited DVTs to pay the flashLoan.
7. The attacker repays the Flash Loan.

Due to the way the Reward Pool calculates rewards, ie:

```
...
rewards = (amountDeposited * 100 * 10**18) / totalDeposits;
...
```

And considering the attacker borrowed and deposited 1.000.000 DVTs, in comparison with what the other users have deposited (100 DVTs), practically, all rewards will go for the attacker, as he deposited x1000 times more tokens than each user.

I developed this attack in the ["AttackerContract" Contract](https://github.com/nahueldsanchez/dvd_brownie/blob/master/the-rewarder/contracts/AttackerContract.sol).

# Selfie challenge, Solution

I started reviewing the [SelfiePool](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/selfie/SelfiePool.sol) contract. I quickly found the method `drainAllFunds` very interesting as in practically performed the actions needed to complete the challenge.

This method has a modifier called `onlyGovernance` that restricts who can call this function. In this case the only address allowed to call it it's the Governance Contract
(governanceAddress). This led me to start reviewing the [SimpleGovernance contract](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.0.0/contracts/selfie/SimpleGovernance.sol).

## A simple governance mechanism

SimpleGovernance implements a governance mechanism. A super simplified explanation of
what this means is that this contract implements a series of rules to allow the queuing and execution of actions that can have certain impact on something. In this specific case in the SelfiePool.

## The problem

So... How all of this can be interesting from an attacker's point of view?

Well, lets ignore all the details for now and asumme that an attacker is able to queue
an action and later execute it. This behavior could be leveraged to drain all the funds of the SelfiePool just queuing the `drainAllFunds` action with the attacker's address as the receiver.

Let's review what the attacker needs to be able to do that.

## The exploit

SimpleGovernance establishes that for a user to be able to propose an action it has
to have enough votes. This condition is checked by function `_hasEnoughVotes`.

```
function _hasEnoughVotes(address account) private view returns (bool) {
    uint256 balance = governanceToken.getBalanceAtLastSnapshot(account);
    uint256 halfTotalSupply = governanceToken.getTotalSupplyAtLastSnapshot() / 2;
    return balance > halfTotalSupply;
}
```

`_hasEnoughVotes` retrieves the caller's balance from the last snapshot (!) and establishes that if that balance is higher than half the total supply of governance Tokens the caller has enough votes to propose an action.

I then proceeded to check how the Snapshots worked.

## Snapshots and who can take them

Snapshots are implemented in DamnValuableTokenSnapshot. This contract inherits from
Open Zeppeling's [ERC20Snapshot](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/extensions/ERC20Snapshot.sol)
I reviewed how Snapshots are taken and found the following interesting documentation
in the code:

```
...
* {_snapshot} is `internal` and you have to decide how to expose it externally. Its usage may be restricted to a
* set of accounts, for example using {AccessControl}, or it may be open to the public.
*
...
```

Then I checked how this was done in `DamnValuableTokenSnapshot`. I found function "Snapshot", code below:

```
function snapshot() public returns (uint256) {
    lastSnapshotId = _snapshot();
    return lastSnapshotId;
}
```

*As you can see, the function is public and can be called by anyone. This is a big difference in comparison with the previous challenge, that implemented an access control mechanism to allow accounts to take snapshots.*

## Solution

Based on this, the attack path that an attacker can follow is:

1. A flash loan is triggered by an attacker asking for an amount of tokens that  will
allow it to have the required voting right.
2. When the loan is received, it then proceeds to taken an Snapshot.
3. The borrowed money is returned.
4. Having the snapshot taken in step 3 and considering that balances are calculated
based on Snapshots, it would be possible for the attacker to propose actions calling
function "queueAction".
5. Leveraging step 4, it will be possible to propose as action the execution of
function "drainAllFunds" by the SelfiePool.
6. After the action is proposed the attacker must wait ACTION_DELAY_IN_SECONDS before
executing the queued action.
7. After ACTION_DELAY_IN_SECONDS passed the attacker can call "executeAction" and
execute action queued in step 5.

I implemented this attack in [AttackerContract](https://github.com/nahueldsanchez/dvd_brownie/blob/master/selfie/contracts/AttackerContract.sol).

I found very interesting that similar problems were found and exploited in real implementations as you can see in the link below:

https://forum.makerdao.com/t/urgent-flash-loans-and-securing-the-maker-protocol/4901