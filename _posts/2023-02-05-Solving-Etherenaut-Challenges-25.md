---
layout: post
title:  Ethernaut challenges writeup Part VII (Challenge 25).
excerpt_separator: <!--more-->
category: DeFi
---

# Motorbike Walkthrough

## Introduction

This challenge recreates in an simpler mode a [vulnerability found in September 2021 in the UUPS Proxy contract library](https://forum.openzeppelin.com/t/uupsupgradeable-vulnerability-post-mortem/15680). The idea is that we have to find a way to execute the `selfdestruct()` operation in the `implementation` or `logic` contract.

<!--more-->

I won't explain here how this Proxy pattern work, you can check the "Further Reading" section for more information. The basic idea to exploit this level is to know that if the logic contract is not initialized, this means that its `initialize()` method was not executed, a malicious attacker can initialize it. This shouldn't be a major issue as the implementation contract's storage doesn't matter. However in the vast majority of cases additional logic is included when the logic contract is initialized, commonly granting some kind of special privileges to the address that initialized it, including control to perform upgrades. In this specific case `initialize` executes the following action: `upgrader = msg.sender;` which will allow the user to execute `upgradeToAndCall`.

Having access to perform upgrades a malicious actor could set the address of the `logic` contract to point to a contract that selfs destruct, rendering the Proxy contract unusable (remember that in the UUPS pattern the upgrade logic resides on the logic contract side). In the real scenario, this malicious contract had to bypass a small rollback check that was not designed for security purposes and hence was [easily bypasseable](https://geeksg.medium.com/my-journey-to-disclosing-a-vulnerability-that-can-lock-up-millions-in-ethereum-dcb5754ad9bc).

To solve this level I performed the following actions:

1. I found the address of the logic contract. To do this I executed:

```
await  web3.eth.getStorageAt(instance,"0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc")

-> 0x000000000000000000000000957d470866f5109255936bd66dab27869e35316c
```
This reads the standard slot defined to store the [address of the contract holding the logic](https://eips.ethereum.org/EIPS/eip-1967)

2. I used Remix and deployed both contracts with their respective addresses.
3. I executed `initialize` method on the `Engine` Contract. This set my address as `upgrader`.
4. Being listed as `upgrader` I was able to call `upgradeToAndCall` and set the address of the new logic to the contract shown below:

```
contract BrokenEngine {
    fallback() external payable {
        selfdestruct(address(0));
    }
}
```

5. I submitted the instance and the `fallback()` was executed, rendering the Proxy contract unusable.

## Source Code

Challenge:

```
// SPDX-License-Identifier: MIT

pragma solidity <0.7.0;

import "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/087d314daf9c7d8205e9eeaade287d853bb3350d/contracts/utils/Address.sol";
import "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-upgrades/master/packages/core/contracts/Initializable.sol";

contract Motorbike {
    // keccak-256 hash of "eip1967.proxy.implementation" subtracted by 1
    bytes32 internal constant _IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    
    struct AddressSlot {
        address value;
    }
    
    // Initializes the upgradeable proxy with an initial implementation specified by `_logic`.
    constructor(address _logic) public {
        require(Address.isContract(_logic), "ERC1967: new implementation is not a contract");
        _getAddressSlot(_IMPLEMENTATION_SLOT).value = _logic;
        (bool success,) = _logic.delegatecall(
            abi.encodeWithSignature("initialize()")
        );
        require(success, "Call failed");
    }

    // Delegates the current call to `implementation`.
    function _delegate(address implementation) internal virtual {
        // solhint-disable-next-line no-inline-assembly
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), implementation, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }

    // Fallback function that delegates calls to the address returned by `_implementation()`. 
    // Will run if no other function in the contract matches the call data
    fallback () external payable virtual {
        _delegate(_getAddressSlot(_IMPLEMENTATION_SLOT).value);
    }

    // Returns an `AddressSlot` with member `value` located at `slot`.
    function _getAddressSlot(bytes32 slot) internal pure returns (AddressSlot storage r) {
        assembly {
            r_slot := slot
        }
    }
}

contract Engine is Initializable {
    // keccak-256 hash of "eip1967.proxy.implementation" subtracted by 1
    bytes32 internal constant _IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;

    address public upgrader;
    uint256 public horsePower;

    struct AddressSlot {
        address value;
    }

    function initialize() external initializer {
        horsePower = 1000;
        upgrader = msg.sender;
    }

    // Upgrade the implementation of the proxy to `newImplementation`
    // subsequently execute the function call
    function upgradeToAndCall(address newImplementation, bytes memory data) external payable {
        _authorizeUpgrade();
        _upgradeToAndCall(newImplementation, data);
    }

    // Restrict to upgrader role
    function _authorizeUpgrade() internal view {
        require(msg.sender == upgrader, "Can't upgrade");
    }

    // Perform implementation upgrade with security checks for UUPS proxies, and additional setup call.
    function _upgradeToAndCall(
        address newImplementation,
        bytes memory data
    ) internal {
        // Initial upgrade and setup call
        _setImplementation(newImplementation);
        if (data.length > 0) {
            (bool success,) = newImplementation.delegatecall(data);
            require(success, "Call failed");
        }
    }
    
    // Stores a new address in the EIP1967 implementation slot.
    function _setImplementation(address newImplementation) private {
        require(Address.isContract(newImplementation), "ERC1967: new implementation is not a contract");
        
        AddressSlot storage r;
        assembly {
            r_slot := _IMPLEMENTATION_SLOT
        }
        r.value = newImplementation;
    }
}
```

Solution:

```
contract BrokenEngine {
    fallback() external payable {
        selfdestruct(address(0));
    }
}
```

## Further Reading

- UUPS Proxies: Tutorial - https://forum.openzeppelin.com/t/uups-proxies-tutorial-solidity-javascript/7786
- Proxies - https://docs.openzeppelin.com/contracts/4.x/api/proxy#ERC1967Upgrade-_upgradeTo-address-
- Writing upgradable contracts, potential unsafe operations - https://docs.openzeppelin.com/upgrades-plugins/1.x/writing-upgradeable#potentially-unsafe-operations
- My journey to disclosing a vulnerability that can lock up millions in Ethereum - https://geeksg.medium.com/my-journey-to-disclosing-a-vulnerability-that-can-lock-up-millions-in-ethereum-dcb5754ad9bc
- EIP-1967: Standard Proxy Storage Slots - https://eips.ethereum.org/EIPS/eip-1967
