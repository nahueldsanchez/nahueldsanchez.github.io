---
layout: post
title:  Solving Damn Vulnerable DeFi Challenges Series (IV). Compromised
excerpt_separator: <!--more-->
category: DeFi
---

Hello there, I missed Monday for the second time, but it's better late than never!. I had some time during the weekend to continue with Damn Vulnerable DeFi Challenges. This time I solved challenge #7, titled "Compromised". So far is the challenge that I enjoyed the most. I'll share the way approached it, enjoy!.

<!--more-->

# Compromised, Solution

I started trying to understand what those bytes provided in the challenge description were. I suspected that were a hint or some useful information

_note: I know... I'm also surprised of how smart I am :P_

Based on a quick read I thought that most of them where in the range of ASCII printable and decided to decode them. For that I used a few cheap and dirty Python lines.

```python
bytes_one = '4d 48 68 6a 4e 6a 63 34 5a 57 59 78 59 57 45 30 4e 54 5a 6b 59 54 59 31 59 7a 5a 6d 59 7a 55 34 4e 6a 46 6b 4e 44 51 34 4f 54 4a 6a 5a 47 5a 68 59 7a 42 6a 4e 6d 4d 34 59 7a 49 31 4e 6a 42 69 5a 6a 42 6a 4f 57 5a 69 59 32 52 68 5a 54 4a 6d 4e 44 63 7a 4e 57 45 35'

bytes_two = '4d 48 67 79 4d 44 67 79 4e 44 4a 6a 4e 44 42 68 59 32 52 6d 59 54 6c 6c 5a 44 67 34 4f 57 55 32 4f 44 56 6a 4d 6a 4d 31 4e 44 64 68 59 32 4a 6c 5a 44 6c 69 5a 57 5a 6a 4e 6a 41 7a 4e 7a 46 6c 4f 54 67 33 4e 57 5a 69 59 32 51 33 4d 7a 59 7a 4e 44 42 69 59 6a 51 34'

l_one = bytes_one.split()
l_one = [chr(int(x, 16)) for x in l_one]
l_two = bytes_two.split()
l_two = [chr(int(x, 16)) for x in l_two]

print(''.join(l_one))
print(''.join(l_two))
```

This provided me two strings that looked `base64` encoded. I proceeded to decode them:

`echo -n <string> | base64 -d`

This process returned these two strings:

```
0xc678ef1aa456da65c6fc5861d44892cdfac0c6c8c2560bf0c9fbcdae2f4735a9
0x208242c40acdfa9ed889e685c23547acbed9befc60371e9875fbcd736340bb48
```
After reviewing the contracts' code, I suspected that this challenge somehow had to allow me to alter the prices sent by the Oracle.

Based on this idea I continued trying to understand what meant these two strings.

[After reading a bit](https://medium.com/@tunatore/how-to-generate-ethereum-addresses-technical-address-generation-explanation-and-online-course-9a56359f139e) about Ethereum addresses I remembered that account addresses are derived from private keys, and those private keys are 32 bytes long. This size matched the size of the strings previously found.

I decided to generate two addresses based on these strings, assuming they were private keys. To do this I used [Brownie](https://eth-brownie.readthedocs.io/en/stable/account-management.html)

```
$ brownie accounts new t1
Brownie v1.17.0 - Python development framework for Ethereum

Enter the private key you wish to add: 0xc678ef1aa456da65c6fc5861d44892cdfac0c6c8c2560bf0c9fbcdae2f4735a9
Enter the password to encrypt this account with: 

SUCCESS: A new account '0xe92401A4d3af5E446d93D11EEc806b1462b39D15' has been generated with the id 't1'

$ brownie accounts new t2
Brownie v1.17.0 - Python development framework for Ethereum

Enter the private key you wish to add: 0x208242c40acdfa9ed889e685c23547acbed9befc60371e9875fbcd736340bb48
Enter the password to encrypt this account with:

SUCCESS: A new account '0x81A5D6E50C214044bE44cA0CB057fe119097850c' has been generated with the id 't2'
```

As it is possible to see the addresses derived from these private keys are:

- Address #1: `0xe92401A4d3af5E446d93D11EEc806b1462b39D15`
- Address #2: `0x81A5D6E50C214044bE44cA0CB057fe119097850c`

If we look at addresses that are use by the Oracle to determine the NFT's prices, we'll see something very interesting:

```
...
This price is fetched from an on-chain oracle, and is based on three trusted reporters:
...
```

- 0xA73209FB1a42495120166736362A1DfA9F95A105
- 0xe92401A4d3af5E446d93D11EEc806b1462b39D15
- 0x81A5D6E50C214044bE44cA0CB057fe119097850c

As you can see, we have the private keys of two of the three accounts used as "trusted reporters". This made me think about the possibility of manipulate the NFT's price.

The next thing I did was check how the price of an NFT was calculated. I ended up in function `_computeMedianPrice`, for clarity I included the code below:

```
    function _computeMedianPrice(string memory symbol) private view returns (uint256) {
        uint256[] memory prices = _sort(getAllPricesForSymbol(symbol));

        // calculate median price
        if (prices.length % 2 == 0) {
            uint256 leftPrice = prices[(prices.length / 2) - 1];
            uint256 rightPrice = prices[prices.length / 2];
            return (leftPrice + rightPrice) / 2;
        } else {
            return prices[prices.length / 2];
        }
    }
```

As it is possible to see, it first orders the prices from lower to higher using the `_sort` function. It later checks if the amount of prices is an even number (checking if the reminder of the division by two equals 0). As we have three prices this won't happen. If this is not true, it returns the price stored in the index number equal as the reminder of the division of the price length by two. For our case this will be 1.

With all of this information we have a clear way to solve this challenge. As we can control two prices – remember that we have the private key of the accounts in charge of setting these prices – We'll be able to control which price goes to the index one in the `prices` array. The attack path will be:

1. The attacker changes the NFTs' prices to a really small value.
2. Then it proceeds to buy  NFTs.
3. It then changes the price of the NFTs to a really high value.
4. The attacker sells the NFTs.
5. The attacker changes the price to the original value.
6. PROFIT!.

I implemented this solution [here](https://github.com/nahueldsanchez/dvd_brownie/blob/master/compromised/scripts/exploit.py). I also ported this challenge to Brownie, you can find it [here](https://github.com/nahueldsanchez/dvd_brownie/) along with all the previous ones.

Thanks for reading!.

## Sources

- https://medium.com/@tunatore/how-to-generate-ethereum-addresses-technical-address-generation-explanation-and-online-course-9a56359f139e
- https://eth-brownie.readthedocs.io/en/stable/account-management.html
