---
layout: post
title:  Un-bricking (and restoring the stock firmware!) a TP-Link AC1750 (Archer A7 v5)
excerpt_separator: <!--more-->
category: [Hardware-Hacking]
---

# Un-bricking (and restoring the stock firmware!) a TP-Link AC1750 (Archer A7 v5)

## Introduction

Hello!, As 2025 kicks off I'll try to write more often. This time I'll use this month's post as a guide for my future self in case I brick my router again, but it might be helpful for someone else too. Long story short, I flashed my old [TP-Link AC1750](https://www.tp-link.com/us/home-networking/wifi-router/archer-a7/) router with [OpenWRT](https://openwrt.org/toh/tp-link/archer_a7_v5) and at some point I decided to restore the stock firmware, thinking it was an easy task...

<!--more-->

When trying to go back to the stock firmware, I tried flashing it from the Web UI, overriding all "DANGER, FORMAT NOT COMPATIBLE, THIS IS A BAD IDEA" messages, and of course, I partially bricked it. As an excuse to start playing with hardware again, I took the challenge of fixing it (thinking that it would be harder than it was...)

## Assessing the damage

First of all, I reviewed how bad the damage was. This is a very well-known router and there is [plenty of documentation for it](https://openwrt.org/toh/tp-link/archer_c7). It was easy to open it and locate the serial interface. Unfortunately, for the `V5` version, you [need to soder the `RX` pin](https://openwrt.org/toh/tp-link/archer_a7_v5#serial) to be able to send commands to the device. In my case, I didn't do it so far, I just needed to see the console's output.

Using a USB-Serial Adapter and [following the documentation for the pinout](https://openwrt.org/toh/tp-link/archer_c7#version_50), I connected to the exposed interface and started the device. Lucky me, I could see the device starting and the Bootloader working. This meant that the damage was not that bad and I could try the [`tftp` method](https://openwrt.org/toh/tp-link/archer_a7_v5#installation_using_the_tftp_method) to re-write the firmware.

## TFTP Installation method TLDR

To be able to write the firmware using this method, I followed these steps:

1. Connected the router to my machine using the `LAN 1` Port.
2. Installed tftpd-hpa (`sudo apt install tftpd-hpa`).
3. Created directory `/srv/tftpd`.
4. Copied the firmware to be flashed in that directory and renamed it to `ArcherC7v5_tp_recovery.bin`. [Link to download it](https://github.com/nahueldsanchez/nahueldsanchez.github.io/blob/master/resources/ArcherC7v5_tp_recovery.bin).
5. Changed firmware permissions to `tftpd:tftpd`.
6. Set the ethernet interface's IP to `192.168.0.66/24`
7. Make an exception in the firewall
8. Configured the `tftpd` server as follows:

```
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/srv/tftp"
TFTP_ADDRESS="192.168.0.66:69"
TFTP_OPTIONS="--secure"
```

9. Restarted the `tftpd` server (`sudo systemctl restart tftpd-hpa.service`).
10. Holding the `reset` button pressed, turn the router on. If done correctly the WPS LED should start flashing.
11. If connected via serial, the process becomes easier as you can monitor progress and see the router's debug messages.
12. I downloaded the latest OpenWrt image for this model.

After working on these steps, I had my router working again!

## Restoring the stock Firmware

The hardest part of the journey was to successfully install TP-Link stock firmware. I spent way too much time downloading versions and rebooting my router until I found the correct steps. It turns out that the trick was to install a specific version but from `dd-wrt`, yes you are reading right... I don't want to make things any longer, so here you can find the steps that I performed:

1. First using the method described above I installed the `factory-to-ddwrt.bin` firmware (sha1sum: `F0A28AC1B8DB02E4A895FC8FE49B8F88C92D00F3`). As explained before, you have to rename the file to `ArcherC7v5_tp_recovery.bin`. [Link to download it](https://github.com/nahueldsanchez/nahueldsanchez.github.io/blob/master/resources/factory-to-ddwrt.bin).
2. Once the installation finished, I proceeded to flash the latest firmware version that I could download from TP-Link website.

## References

- https://forum.openwrt.org/t/tp-link-archer-a7-revert-to-stock-firmware-failed/42419/8
- https://openwrt.org/toh/tp-link/archer_a7_v5#back_to_stock_firmware
- https://wiki.dd-wrt.com/wiki/index.php/TP_Link_Archer_A7v5#TFTP_RECOVERY_TO_REVERT_BACK_TO_STOCK