---
layout: post
title:  Solving Damn Vulnerable DeFi Challenges Series (IX). Climber.
excerpt_separator: <!--more-->
category: DeFi
---

Hi there, almost finishing this saga!. Today's post explains how I solved challenge #12 - Climber. So far this level has been the hardest for me. I hope you enjoy the walkthrough. If you want to play with this level, I ported it to Brownie, you can find it [here](https://github.com/nahueldsanchez/dvd_brownie/tree/master/climber).

In this blog post you'll read about:

- Proxies
- Open Zeppelin UUPS proxy implementation
- Timelock contracts

<!--more-->

# Climber challenge writeup

## Quick introduction

We are presented with the following statement:

```
There's a secure vault contract guarding 10 million DVT tokens. The vault is upgradeable, following the UUPS pattern.
The owner of the vault, currently a timelock contract, can withdraw a very limited amount of tokens every 15 days.
On the vault there's an additional role with powers to sweep all tokens in case of an emergency.
On the timelock, only an account with a "Proposer" role can schedule actions that can be executed 1 hour later.
Your goal is to empty the vault.
```

There is a lot of information here. I tried to take the most important facts:

1. There is a contract acting as a vault with holds certain amount of DVT tokens.
2. The contract was deployed behind a proxy following the UUPS pattern. I'll detail what this means below.
3. The owner of the vault contract is another contract, a `timelock`. Again, more on this later.
4. The vault contract limits how much can be withdrawn in a window of time.
5. The timelock contract has different roles, specifically an "Admin" Role that allows for Role management and a "Proposer" role that allows for the scheduling of actions. We'll see later how these work in detail.

Our task is to steal all the DVT tokens from the vault. Before digging deeper in the actual challenge let's review some of the theory I had to read before tackling this level.

## Upgradeable contracts and UUPS pattern

As you may know, contracts deployed to the blockchain cannot be changed. This is good for a lot of reasons but has a major downside. It doesn't allow developers to upgrade their applications to add new functionality or fix bugs. to overcome this limitation a clever technique is used, Proxies. I won't go over in detail here about all the theory, for that you can check the following references [here](https://blog.openzeppelin.com/proxy-patterns/) and [here](https://fravoll.github.io/solidity-patterns/proxy_delegate.html).

### Proxy patterns: Transparent Proxy and UUPS

There are several ways to implement these proxies, being the [transparent Proxy pattern](https://blog.openzeppelin.com/the-transparent-proxy-pattern/) and the [Universal Upgradeable Proxy Standard](https://eips.ethereum.org/EIPS/eip-1822) the most commons. There are some differences between these two approaches but the most important is that in the UUPS pattern the logic (code) in charge of the upgrades resides in the logic contract. In contrast, in the transparent proxy pattern the logic for upgrades is implemented in the proxy itself.

As in this challenge the UUPS is used, in the following section we'll review how it is implemented.

### UUPS in Openzeppelin contracts

I decided to take a look and understand how this proxy pattern was implemented. The challenge implements upgradeability using [`UUPSUpgradeable`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/proxy/utils/UUPSUpgradeable.sol), let's take a closer look.

At this point we need to divide our efforts in two parts:

1. Understand how the proxy is implemented.
2. Understand how the upgrade logic is implemented.

#### Part one: Proxy implementation

Fortunately [OpenZeppelin's documentation helps a lot](https://docs.openzeppelin.com/contracts/4.x/api/proxy#ERC1967Proxy). [Looking at the code](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/proxy/utils/UUPSUpgradeable.sol) and also going over the documentation we can understand that UUPS proxies are implemented based on [`ERC1967Proxy` contract](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/3dac7bbed7b4c0dbf504180c33e8ed8e350b93eb/contracts/proxy/ERC1967/ERC1967Proxy.sol).

The [`ERC1967Proxy`](https://docs.openzeppelin.com/contracts/4.x/api/proxy#ERC1967Proxy) contract inherits from two contracts. The first one, a base contract called [`Proxy`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/3dac7bbed7b4c0dbf504180c33e8ed8e350b93eb/contracts/proxy/Proxy.sol). This contract implements the most basic functionality needed for a Proxy, a `delegate` function that forwards all calls performed to it to another contract, the `implementation`. This contract is not upgradeable so far. [`ERC1967Upgrade`](https://docs.openzeppelin.com/contracts/4.x/api/proxy#ERC1967Upgrade) provides internal functions to get and set the storage slots. This functionality is defined as internal and is the responsibility of the implementation contract to provide external functions to allow for upgrades. We'll see how this is implemented in the following section.

All this complexity is hidden during's challenge deployment thanks to the use of OZ's upgrade plugin for hardhat. The following part of the deployment script deploys the proxy contract previously discussed:

```
...
this.vault = await upgrades.deployProxy(
            await ethers.getContractFactory('ClimberVault', deployer),
            [ deployer.address, proposer.address, sweeper.address ],
            { kind: 'uups' }
        );
...
```

This solves our first question, now we need to understand how the upgrade logic is implemented in the contract that implements the logic. Remember that in UUPS proxies it is the responsibility of the implementation contract to include the functionality to allow upgrades.

As I wanted to implement this challenge in Brownie I had to replicate this behavior in a manual way. In the deployment script, you can see that I deployed a [ERC1967Proxy](https://github.com/nahueldsanchez/dvd_brownie/blob/master/climber/scripts/deploy.py#L20)

#### Part two: Upgrade logic implementation

Now, let's review how the upgrade mechanism is implemented. As the contract implementing the logic in our case is [`ClimberVault`](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/master/contracts/climber/ClimberVault.sol) we need to review it. The contract inherits from three contracts: `Initializable`, `OwnableUpgradeable` and the most important for us, `UUPSUpgradeable`. Again, going back to OZ's documentation we can find the following explanation:

```
...
This is where the UUPSUpgradeable contract comes in. Inheriting from it (and overriding the _authorizeUpgrade function with the relevant access control mechanism) will turn your contract into a UUPS compliant implementation.

Note that since both proxies use the same storage slot for the implementation address, using a UUPS compliant implementation with a TransparentUpgradeableProxy might allow non-admins to perform upgrade operations.
...
```

UUPSUpgradeable inherits from `IERC1822Proxiable` and `ERC1967Upgrade`. The first contract comes from an interface and has the definition for function `proxiableUUID`. This function is used to validate that the implementation contract is compatible with the proxy while performing the upgrade. The second contract is the same one that we reviewed before. But in this case contract `UUPSUpgradeable` defines function `upgradeTo` and `upgradeToAndCall` (along with others), all of them defined as external, allowing for external users or contracts to call them via the Proxy.

In this way our `ClimberVault` contract implements the upgrade mechanism. it is important to mention that, as recommended the contract also overrides function `_authorizeUpgrade` adding the `onlyOwner` mechanism.

By now, we have a better understanding about how the proxy and the upgrade mechanism work. Let's talk about timelock contracts in the next section.


## Timelock contracts

Timelock contracts main use is to delay the execution of actions after a certain amount of time has passed, this delay is configurable and is supposed to give enough time to all the involved parties to review the actions proposed for execution and take actions if needed. Actions can be scheduled by a certain group of addresses that have an specific authorization role, normally called "Proposers". These contracts normally implement another role called "Administrators" that allow users belonging to it to perform modifications over the roles and add/remove other people.

In our case the contract implementing the Timelock functionality is [`ClimberTimeLock`](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.2.0/contracts/climber/ClimberTimelock.sol). For access control it uses [OpenZeppelin's access control module](https://docs.openzeppelin.com/contracts/2.x/access-control#role-based-access-control).

We have two roles:

- `ADMIN_ROLE`, controlling who can perform changes to the roles itself.
- `PROPOSER_ROLE`, controlling who can propose new actions.

Critical actions, such as scheduling a new task are modifier by the `onlyRole` modifier that correctly checks if the `msg.sender` has an specific role set up.

## Level architecture

Now, that we have a better understanding of all the parts we can put them together.

First, we have a Proxy contract that will perform two main tasks:

1. Store state.
2. Forward all calls to the implementation contract.

Second, we have an implementation or logic contract `ClimberVault`. This contract has the following interesting features:

1. Implements the `sweepFunds` function that will be useful for our purposes of draining all the funds.
2. Implements the `onlySweeper` modifier. This is used to limit who can call the `sweepFunds` function.
3. Overrides `_authorizeUpgrade` function, including the `OnlyOwner` modifier. With this change, the only account that can perform upgrades will be the `Owner`.
4. Upon initialization, the contract transfers ownership (and thus, the ability to perform upgrades) to the Timelock contract.

Third, we have the Timelock contract:

1. This contract will be the `owner` of the `ClimberVault`. This is important because this determines who can upgrade the `ClimberVault` contract.
2. During setup, in the `constructor`, this contract grants roles `ADMIN_ROLE` and `PROPOSER_ROLE` to itself. This detail will be very important for exploitation purposes.
3. The contract has three interesting functions: `schedule` that can only be called by users holding the `PROPOSER_ROLE` role, `execute` that can be called by anyone, and `updateDelay` that even though it can be externally called, checks that the `msg.sender` is the timelock contract itself.
4. This timelock as a delay time `delay` set to 1 hour. Scheduled actions cannot be execute until this time has passed.


Scheduled operations are stored using an structure with the following fields:

```
// Operation data tracked in this contract
struct Operation {
    uint64 readyAtTimestamp;    // timestamp at which the operation will be ready for execution
    bool known;                 // whether the operation is registered in the timelock
    bool executed;              // whether the operation has been executed
}
```

Also an `Id` is calculated for each operation:

```
...
bytes32 id = getOperationId(targets, values, dataElements, salt);

function getOperationId(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata dataElements,
        bytes32 salt
    ) public pure returns (bytes32) {
        return keccak256(abi.encode(targets, values, dataElements, salt));
    } 
...
```

## The bug

So far we know that only certain addresses can schedule operations and that each operation has an identifier that's based on the result of encoding different parameters and hashing the result. An interesting fact is that the actions itself are not stored. Based on this, `execute` function accepts the same parameters that `schedule`:

```
function execute(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata dataElements,
        bytes32 salt
    ) external payable {
        require(targets.length > 0, "Must provide at least one target");
        require(targets.length == values.length);
        require(targets.length == dataElements.length);

        bytes32 id = getOperationId(targets, values, dataElements, salt);

        for (uint8 i = 0; i < targets.length; i++) {
            targets[i].functionCallWithValue(dataElements[i], values[i]);
        }
        
        require(getOperationState(id) == OperationState.ReadyForExecution);
        operations[id].executed = true;
    }
```

The function receives, and _more importantly, *executes* the actions passed by any user. It finally calculates the `operationId` and validates that the operation was previously scheduled and with state `ReadyForExecution`. At first glance, seems impossible to execute actions that are not scheduled as the require statement is checking that the operation is known, and thus, previously scheduled by an approved address.

But... what if a malicious (or clever) user executes the scheduling of an action!? This could be used to bypass the timelock contract completely.

## The Exploit

I had a lot of headaches while coding the exploit and spent several days on it, but finally made it. The idea that I followed to exploit this challenge was to leverage the `execute` function to perform several actions:

1. Change the required delay, from 1 hour to 0. With this change, actions can be scheduled and executed instantly.
2. Grant the `PROPOSER_ROLE` to an attacker controlled address (a malicious contract used in step 4).
3. Execute an upgrade to change the ClimberVault for a bugged version.
4. Call a function in an attacker controlled contract that will call the `schedule` function in the timelock contract. This function was designed to detect if it was being called for the first time (during the execution in `execute`) or a second time during the `scheduling` phase. This is a key detail as actions that return the same `id` cannot be scheduled more than once.
5. The upgrade is performed to a contract that has a different `sweeper` address set, in this case, an attacker controlled address.
6. Sweep the funds!

I implemented this solution using this [AttackerContract](https://github.com/nahueldsanchez/dvd_brownie/blob/master/climber/contracts/AttackerContract.sol) and this [implementation contract](https://github.com/nahueldsanchez/dvd_brownie/blob/master/climber/contracts/MaliciousClimberVault.sol)

## Sources

- OpenZeppelin Proxy patterns - https://blog.openzeppelin.com/proxy-patterns/
- OpenZeppelin Proxies - https://docs.openzeppelin.com/contracts/4.x/api/proxy
- EIP-1822: Universal Upgradeable Proxy Standard - https://eips.ethereum.org/EIPS/eip-1822
- EIP-1967: Standard Proxy Storage Slots - https://eips.ethereum.org/EIPS/eip-1967
- The transparent Proxy Pattern - https://blog.openzeppelin.com/the-transparent-proxy-pattern/
- Upgrade Plugins - https://docs.openzeppelin.com/upgrades-plugins/1.x/
- Proxy Delegate - https://fravoll.github.io/solidity-patterns/proxy_delegate.html
- Access control - https://docs.openzeppelin.com/contracts/3.x/access-control
- Solidity Arrays - https://www.tutorialspoint.com/solidity/solidity_arrays.htm
- UUPS proxies: Tutorial - https://forum.openzeppelin.com/t/uups-proxies-tutorial-solidity-javascript/7786