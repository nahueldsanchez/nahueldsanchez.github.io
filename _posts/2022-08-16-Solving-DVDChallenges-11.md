---
layout: post
title:  Solving Damn Vulnerable DeFi Challenges Series (VIII). Backdoor.
excerpt_separator: <!--more-->
category: DeFi
---

Hello everyone, I'm continuing with Damn Vulnerable DeFi challenges. In today's post I'll be solving challenge #11 - Backdoor.

This was a very interesting challenge that allowed me to learn and play with the following topics:

- Gnosis Safe contracts. A powerful multisig wallet. I learned how to deploy and used it.
- Proxy pattern and their different use cases.
- Solidity's delegatecall powers and how carefully you have to be while using it.
- Encoding, ABIs, and so on.

I also ported this challenge to my [project DVD Brownie, you can solve it using Python](https://github.com/nahueldsanchez/dvd_brownie/tree/master/backdoor).

I hope you enjoy the read!.

<!--more-->

# Backdoor challenge writeup

## Quick introduction

In this challenge we are presented with the following statement:

```
To incentivize the creation of more secure wallets in their team, someone has deployed a registry of Gnosis Safe wallets. When someone in the team deploys and registers a wallet, they will earn 10 DVT tokens.

To make sure everything is safe and sound, the registry tightly integrates with the legitimate Gnosis Safe Proxy Factory, and has some additional safety checks.

Currently there are four people registered as beneficiaries: Alice, Bob, Charlie and David. The registry has 40 DVT tokens in balance to be distributed among them.

Your goal is to take all funds from the registry. In a single transaction.
```

The idea is that there is a contract "Registry" that keeps tracks of wallets being created using Gnosis Safe. This contract has a list of whitelisted users that once they create their wallet, are rewarded with 10 DVTs that are transferred to their Gnosis Safe wallets. After reviewing the [`Wallet Registry` contract](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.2.0/contracts/backdoor/WalletRegistry.sol), I think that's interesting to detail some of its inner workings:

Most of the interesting functionality lives in function `proxyCreated`. This is an special function called when an Gnosis Safe wallet is created with an specific configuration. We'll see this mechanism in detail later, for know keep in mind that any user can create a Gnosis Safe wallet and trigger the execution of this function.

The function has two important mappings: `beneficiaries` and `wallets`. The first one keeps tracks of the addresses allowed to register in the registry contract. In our case will be Alice, Bob, Charlie and David. Any other address trying to register will be rejected by the `require` statement [in line #86](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/3e2a3675f4a733557ee9417b97fee104c0110618/contracts/backdoor/WalletRegistry.sol#L86). `Wallets` mapping contains the address of each owner wallet (the Gnosis Safe). This address is used to transfer the DVT tokens.

After reviewing the function everything looked safe. Let's do a quick review of how it works:

The function receives the address of the newly created wallet via the `proxy` parameter, the address of the `Gnosis Safe Master Copy` (more on this on the next section) in the `singleton` and array of bytes in the `initializer` parameter that are the `calldata` received by the function.

The function has the following sanity checks:

1. It verifies that who has called it `msg.sender`, matches the address of the `Gnosis safe Factory`. We'll discuss the wallet creation process in detail later.
2. It verifies that the `singleton` address matches the trusted address for the `Gnosis safe` Master copy.
3. Verifies that the first four bytes of the `calldata` (initializer) matches the signature of the `GnosisSafe.setup` function. This is done to validate that the function initializing the safe was executed.
4. After these steps it validates that the wallet created has only one owner and a configured threshold of one.
5. Lastly, it validates that the owner of the Gnosis Safe Wallet is registered as a beneficiary.

So, nothing out of normal. It seems that the Wallet Registry contract looks safe. Let's review how an Gnosis Safe Wallet is created.

## Deploying a Gnosis Safe Wallet

After reviewing the Wallet Registry code and not finding anything unusual I decided to review how the Gnosis Safe wallet code worked. I didn't expect to find any security issues within the code itself, as it is a widely known project used by hundreds of users. My guess was that there could be an issue in the way it was used or in some configuration.

I started reviewing how the Safe is deployed, summarizing the process in the following steps:

1. As the challenge explains, Gnosis Safe wallet implements the [EIP-1167: Minimal Proxy Contract](https://eips.ethereum.org/EIPS/eip-1167) allowing cheaper deployment costs. The idea is that when you need to deploy a Safe wallet, what you actually do is deploy a minimal contract (Proxy) that delegates all the call that it receives to a "master copy" contract that holds all the logic. The proxy contract will store state (balances and so on). In our specific case the [Proxy contract](https://github.com/safe-global/safe-contracts/blob/v1.3.0/contracts/proxies/GnosisSafeProxy.sol) is deployed via a "Factory". [The factory is an special contract that returns Proxy instances](https://github.com/safe-global/safe-contracts/blob/v1.3.0/contracts/proxies/GnosisSafeProxyFactory.sol).

2. To deploy our proxy, we will perform a call to function `createProxyWithCallback` part of the `GnosisSafeProxyFactory` contract. This function allows for the creation of a `Proxy` but also executes a `callback function` called `proxyCreated` on an arbitrary address once the Proxy is successfully created. We'll use this feature to execute the code in the `WalletRegistry` contract.

3. Function `createProxyWithCallback` receives the following arguments: `address singleton`, `bytes initializer`, `uint256 nonce`, `address callback`. `Singleton` holds the address of the Gnosis Safe Master code, `initializer` will contain the functions that must be executed to initialize the proxy (function that has to be executed right after the proxy is created), `nonce` is used to calculate the address of the proxy (check the CREATE2 opcode for more information) and finally, `callback` will be the address of the contract that implements the `proxyCreated` function.

4. Once our Safe Wallet is created (the Proxy), the [`setup`](https://github.com/safe-global/safe-contracts/blob/v1.3.0/contracts/GnosisSafe.sol#L75) has to be executed. In our case this will be done in step 3 via the `initializer` code. The `setup` function configures various aspects of the safe such as: Owners, the amount of required signatures to approve a TX (threshold), and others.

5. After step four we have our wallet created. In case that our address is registered as a beneficiary, we'll be registered in the `Wallet Registry` contract.


## The Problem

Once I reviewed the contracts both from the Gnosis Safe and the wallet registry, and as I expected everything seemed OK. The idea to setup this challenge was:

1. Deploy the Gnosis Safe wallet project.
2. When configuring the wallet you have to pass to the `setup` function an specific configuration to be able to registry in the `Wallet Registry` contract. In our case the owner must be only one and should be one of the whitelisted users (Alice, Bob, Charlie, David). The threshold level must be one.
3. If everything is OK, the `Wallet Registry` contract will transfer 10 DVT tokens to the newly created wallet.

Everything looked fine, so I decided to review again how the setup process worked, taking a better look at the `setup` function. Let's analyze it:

```
function setup(
    address[] calldata _owners,
    uint256 _threshold,
    address to,
    bytes calldata data,
    address fallbackHandler,
    address paymentToken,
    uint256 payment,
    address payable paymentReceiver
) external {
```

Besides the already explained parameters there was one that caught my attention: `address fallbackHandler`. I reviewed the documentation to understand its usage:

```
...
/// @param fallbackHandler Handler for fallback calls to this contract
...
```

Interesting... I reviewed how it was used later in the code:

```
...
if (fallbackHandler != address(0)) internalSetFallbackHandler(fallbackHandler);
...
```

I reviewed where the `internalSetFallbackHandler` was defined and found it in `FallbackManager` contract:

```
...
function internalSetFallbackHandler(address handler) internal {
    bytes32 slot = FALLBACK_HANDLER_STORAGE_SLOT;
    // solhint-disable-next-line no-inline-assembly
    assembly {
        sstore(slot, handler)
    }
}
...
```

Based on the documentation I understood that you can specify an address that will be used as a fallback when calls performed to the Gnosis Safe wallet cannot be resolved within its code. I checked how the `fallback()` function was implemented for the Gnosis Safe contract. I found that this contract inherits from `FallbackManager` and the `fallback()` function is defined there:

```
...
// solhint-disable-next-line payable-fallback,no-complex-fallback
fallback() external {
    bytes32 slot = FALLBACK_HANDLER_STORAGE_SLOT;
    // solhint-disable-next-line no-inline-assembly
    assembly {
        let handler := sload(slot)
        if iszero(handler) {
            return(0, 0)
        }
        calldatacopy(0, 0, calldatasize())
        // The msg.sender address is shifted to the left by 12 bytes to remove the padding
        // Then the address without padding is stored right after the calldata
        mstore(calldatasize(), shl(96, caller()))
        // Add 20 bytes for the address appended add the end
        let success := call(gas(), handler, 0, 0, add(calldatasize(), 20), 0, 0)
        returndatacopy(0, 0, returndatasize())
        if iszero(success) {
            revert(0, returndatasize())
        }
        return(0, returndatasize())
    }
}
...
```

As it is possible to see in the code, if an address is stored in `FALLBACK_HANDLER_STORAGE_SLOT` a function `call` will be executed to that address.

Well, this looks very interesting. Let's do a quick recap on what we can do from an attacker's point of view:

1. Deploy an Gnosis Safe wallet for an arbitrary user (Alice, Bob, Charlie, David).
2. Set an arbitrary address to be used as a fallback for this wallet (!!!).
3. Register this wallet in the Wallet Registry Contract.
4. The Registry wallet will transfer 10 DVT back to the wallet.

Now with a clearer scenario we can think about a potential attack... What could happen if a malicious user sets as fallback address the address of the Damn Valuable Token contract and calls the Gnosis Safe Wallet with the `transfer()` method!?. Well, the idea is that as this method does not exist in the wallet contract, it will be passed to the fallback address which will end up transfer the funds to an attacker controlled address!. Remember that the owner of the DVT tokens is the wallet and the `call` to `transfer()` is performed by it.

## The Exploit

The exploit that I developed performs the following steps:

1. For each victim (Alice, Bob, Charlie and David) it encodes the function call to `Gnosis.Safe::Setup()`, passing as `fallback()` handler the address of the DVT token.
2. After step 1, it calls `createProxyWithCallback`, passing as arguments the previously encoded data into `initializer` parameter and as `callback` address the wallet registry contract address.
3. Finally it triggers the attack, calling `transfer()` into the wallet address. As this function does not exists in the contract. It will be passed to the fallback handler, namely, the Damn Valuable Token contract set in step 1. This will transfer the DVT tokens to an address chosen by the attacker.

I implemented this attack in the [following contract](https://github.com/nahueldsanchez/dvd_brownie/blob/master/backdoor/contracts/AttackerContract.sol).

## Conclusions

I enjoyed this level because it forced me to go over a unknown codebase and learn how to use it. Very often useful functionality can be abused if it isn't considered when designing solutions that integrate different complex parts. In this case none of the contracts involved had vulnerabilities and still it was possible to steal funds.

## Sources

- Gnosis Safe SMART CONTRACT DEEP DIVE - https://hackmd.io/@kyzooghost/HJMi2Nllq?print-pdf#/
- Gnosis Safe Developer Portal - https://safe-docs.dev.gnosisdev.com/safe/
- Solidity Tutorial : all about Bytes - https://jeancvllr.medium.com/solidity-tutorial-all-about-bytes-9d88fdb22676
- Solidity Arrays - https://www.tutorialspoint.com/solidity/solidity_arrays.htm
- Solidity Tutorial: all about ABI - https://coinsbench.com/solidity-tutorial-all-about-abi-46da8b517e7
- Multisig transactions with Gnosis Safe - https://medium.com/gauntlet-networks/multisig-transactions-with-gnosis-safe-f5dbe67c1c2d#:~:text=Gnosis%20Safe%20implements%20the%20proxy,not%20match%20any%20defined%20function.
- Solidity by Example, call - https://solidity-by-example.org/call/
- Brownie Package Manager - https://eth-brownie.readthedocs.io/en/stable/package-manager.html
- Solidity DelegateProxy contracts - https://blog.gnosis.pm/solidity-delegateproxy-contracts-e09957d0f201
