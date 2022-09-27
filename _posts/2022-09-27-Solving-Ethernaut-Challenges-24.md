---
layout: post
title:  Ethernaut challenges writeup Part VI (Challenge 24).
excerpt_separator: <!--more-->
category: DeFi
---

Hello everyone! almost finishing my saga for [Ethernaut](https://ethernaut.openzeppelin.com/) challenges. In today's post I'll share my solution for the "Puzzle Wallet" challenge. I hope that you enjoy it!

<!--more-->

# Puzzle wallet write up

By far the hardest level in the Ethernaut series, at least for me. I was stuck in this level for a week without being able to solve it and spent QUITE A LOT OF TIME in it!.

This challenge requires us completing two tasks:

1. Make our address the Owner of the `PuzzleWallet` contract.
2. Make ourselves admins of the `PuzzleProxy` contract.

First goal is to make our address Owner of the `PuzzleWallet` contract. Easy task!. As there is [storage clashing](https://ethereum-blockchain-developer.com/110-upgrade-smart-contracts/06-storage-collisions/) we can use the `proposeNewAdmin` method, part of the `PuzzleProxy` contract to write our address in the `pendingAdmin` variable. This will overwrite the slot where the `owner` variable points, effectively making our address the Owner of the `PuzzleWallet` contract.

Once we are Owners, we can use `addToWhitelist` method and include ourselves as whitelisted address. This provides access to all methods protected by the `onlyWhitelisted` modifier. Based on this we can use `deposit()`, `execute` and `multicall` which we'll need to solve this level.

From this point moving forward the real challenge starts. To be able to call `setMaxBalance`, contract's balance must be 0. The issue is that the contract is deployed with `0.001` Ether that seems impossible to withdraw. Here is where the magic happens. Is it possible to chain multiple calls using the `multicall` function to make the `PuzzeWallet` contract to believe that we have deposited more Ether than the real amount deposited. In doing this we'll be able to call the `execute` method with an `value` parameter higher than what we should, effectively stealing Ether from the contract. This scenario is a simpler version of two real vulnerabilities found in [SushiSwap's MISO smart contracts](https://samczsun.com/two-rights-might-make-a-wrong/) and  [Opyn ETH Put contracts](https://medium.com/opyn/opyn-eth-put-exploit-c5565c528ad2).

The basic concept behind these bugs is that `msg.value` is used inside a `loop` operation. This leads to an scenario where the same value it's used multiple times but the Ether was sent only once. In our case `multicall` has a "protection mechanism" to avoid allowing a malicious user to call `deposit` multiple times. But this mechanism is flawed. It is possible to call `deposit` using `multicall` and then use that inside another `multicall` call, something like this:

```
multicall([deposit(), multicall([deposit()])])
```

When doing this, the protection mechanism is useless as the method selector in regards to the outer call will be the one corresponding to the `multicall`. When this trick is executed the attacker will have an entry in the `mapping(address => uint256) public balances` of X value, but the `address(this).balance` of the contract will be `X/2`. In this way it will be possible to call `execute` method with a value higher than th real amount deposited by the attacker, which will allow him to drain all the contract's balance.

The detailed step by step to perform this is explained below:

```
multicall(deposit(), multicall(deposit()))
execute(xx, ValueOfContractBalance, xx)
```

1. After these two operations the contract's balance is 0.
2. Once the balance is 0, it is possible to call `setMaxBalance`. This method changes the value of `maxBalance`. As side effect overwrites the `admin` variable. To find the `uint256` that represents the address that we want to set as admin we can use the following Solidity snippet:

```
function addressToUint256(address _addr) public returns (uint256) {
    return uint256(uint160(_addr));
}

// addressToUint256(0x922e34D7d34C70Df760DF873BC6F99a10dea516E) --> 834543090099854329743302784494283355453968241006
```

## Further Reading / Useful links

- Online ABI Encoding Service - https://abi.hashex.org/
- https://docs.openzeppelin.com/upgrades-plugins/1.x/proxies
- Understanding Storage Collisions - https://ethereum-blockchain-developer.com/110-upgrade-smart-contracts/06-storage-collisions/
- Opyn Hacks: Root Cause Analysis- https://peckshield.medium.com/opyn-hacks-root-cause-analysis-c65f3fe249db
- Detecting MISO and Opyn’s msg.value reuse vulnerability with Slither - https://blog.trailofbits.com/2021/12/16/detecting-miso-and-opyns-msg-value-reuse-vulnerability-with-slither/
