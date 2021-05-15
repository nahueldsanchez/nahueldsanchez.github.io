---
layout: post
title:  Bypassing upgrade limitations on a TP-Link TL-WR841N
excerpt_separator: <!--more-->
---

## Introduction

Hello! In this blogpost we'll continue with our TP-Link TL-WR841N Saga. Today's post will explain the steps that I followed to bypass a silly limitation in the Router's Stock firmware for Latin America (ES) models that did not allow me to install the latest US firmware.

<!--more-->

## Router and firmware versions per region

As I wanted to hunt for new vulnerabilities in the Router's firmware, I decided to install the latest firmware available.

<html>
<img src="/images/2021-05-14-Playing-with-a-TP-LINK-TR841_II_img_1.png" alt="latest Firmware version when US region is selected">
</html>

This is the latest firmware available for download for the *United States* region. Released on April 09 2021, is still hot. This update has been released even after the product as reached is end of life (EOL).

I proceeded to download it and tried to install it, but I ended up the following error message:

<html>
<img src="/images/2021-05-14-Playing-with-a-TP-LINK-TR841_II_img_2.png" alt="Error updating the firmware">
</html>

It says that the device did not accept the firmware. As I was connected over the serial interface I took a look at the screen while the update process was running and I saw the following error:

<html>
<img src="/images/2021-05-14-Playing-with-a-TP-LINK-TR841_II_img_3.png" alt="Error updating the firmware printed in the serial interface">
</html>

At this point I decided to take a look at what was happening under the hood.

## Analysis of the Firmware's update process and rediscovering CVE-2019-19143 on it

I decided to use a combination of static and dynamic analysis to understand what was happening, taking advantage of the debugging capabilities that I obtained before. If you want to read more about it you can refer to the [previous post of this saga](https://nahueldsanchez.com.ar/Playing-with-a-TP-LINK-TR841_I/).

I started decompressing the installed firmware.  I had a copy of it, that you can find [here](TBD). I used [binwalk](https://github.com/ReFirmLabs/binwalk) for this task:

```
binwalk -eM TL-WR841Nv14_ES_0.9.1_4.16_up_boot[180515-rel41770].bin
```

To figure out where start looking I executed the upgrade process again, this time using [Burp Proxy](https://portswigger.net/burp) to analyze every HTTP request performed by the web application.

Below you can find a shortened version with the important information.

```
POST /cgi/softup HTTP/1.1
Host: 192.168.0.1
Content-Length: 4063991
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary2Q0BPMrYW8nfAK4B
Cookie: Authorization=Basic XXXXXXXX
...
```
As we can see there is a `POST` request to `/cgi/softup` that needs authentication. We have some interesting information already:

* The firmware is uploaded and something is validated on the router's side that kicks us out
* The endpoint in charge of the update is `/cgi/softup`

### Side note: rediscovering CVE-2019-19143

One of the first things that I tried was replaying the update request without the `Cookie` header. To my surprise IT WORKED!. It was possible to upload a new firmware to the router without authentication. After some googling I found that this issue was already known and tagged as [CVE-2019-19143](https://nvd.nist.gov/vuln/detail/CVE-2019-19143). The router checks that the `Referer` header matches the Router IP address. A "funny" thing is that this check is wrongly performed, as it only checks that the IP in the header contains the Router IP. I tried with the following value: `Referer: http://192.168.0.122111` and it also worked.

Coming back to our main objective, I decided to take a look at the file system to see if there was any `/cgi/` folder or any `softup` file. I found nothing. I concluded that the filepath was being processed by the webserver, in this case the `httpd` binary.

I loaded it in Ghidra and searched for that string:

<html>
<img src="/images/2021-05-14-Playing-with-a-TP-LINK-TR841_II_img_4.png" alt="function using the softup URL">
</html>

As the image above shows, I found it being used as an argument for the function `http_alias_addEntryByArg`. I assumed that this function was some kind of "Handler installer", and the function called when the URI of interest was requested was `http_rpm_update`. I proceeded to analyze it.

### Function http_rpm_update

Decompiled function code provided by Ghidra:

```C
int http_rpm_update(int *param_1)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  undefined *puVar4;
  uint uVar5;
  undefined4 local_a38;
  undefined auStack2612 [256];
  char acStack2356 [256];
  char acStack2100 [2052];
  int local_30;
  
  local_a38 = 0;
  DAT_00438730 = 0;
  if (*(int *)(*param_1 + 0x1030) == 2) {
    DAT_00438730 = 0x1162b;
    iVar2 = 0x193;
  }
  else {
    uVar5 = param_1[6];
    iVar2 = cmem_getUpdateBufSize();
    if (iVar2 + 0x40bb8U < uVar5) {
      DAT_00438730 = 0x1162b;
      iVar2 = 0x19d;
    }
    else {
      if ((DAT_00438734 == (undefined *)0x0) &&
         (DAT_00438734 = (undefined *)cmem_updateFirmwareBufAlloc(),
         DAT_00438734 == (undefined *)0x0)) {
        DAT_00438730 = 0x232a;
        return 500;
      }
      puVar4 = DAT_00438734;
      uVar3 = cmem_getUpdateBufSize();
      bVar1 = false;
      while ((param_1[6] != 0 &&
             (iVar2 = http_parser_illMultiObj(param_1,acStack2356,0,puVar4,uVar3,&local_a38),
             -1 < iVar2))) {
        local_30 = iVar2;
        iVar2 = strcmp(acStack2356,"filename");
        if (iVar2 == 0) {
          DAT_00438738 = local_30;
          bVar1 = true;
          puVar4 = auStack2612;
          uVar3 = 0x100;
        }
      }
      if (bVar1) {
        param_1[0xe] = (int)FUN_00408400;
        puVar4 = &DAT_0040c7a4;
      }
      else {
        DAT_00438730 = 0x1162b;
        iVar2 = cmem_updateFirmwareBufFree(DAT_00438734);
        if (iVar2 < 0) {
          cdbg_printf(8,"http_rpm_update",0xa4,"Detach big buffer error\n");
        }
        DAT_00438734 = (undefined *)0x0;
        puVar4 = &DAT_0040cd58;
      }
      sprintf(acStack2100,"<html><head></head><body>%s</body></html>",puVar4);
      param_1[7] = 0;
      param_1[0xf] = (int)g_http_file_pTypeHTML;
      iVar2 = http_io_output(param_1,acStack2100);
      iVar2 = (iVar2 != -1) - 1;
    }
  }
  return iVar2;
}
```

Taking a quick look at this function I found some clues that led me to believe it could be the one being executed when the update process was called. Before starting to analyze it, I tried to identify key points like the following ones:

* The returned value was the one I was receiving: `<html><head></head><body>%s</body></html>`
* The function processed input looking for a file
* There were some names suggesting "update buffers"

Based on the ideas above, I decided to avoid doing a full analysis of this function and only focusing on understand what I needed to modify or change to accomplish my goal. I tried to understand how the process continued, and discarding options I learned that it called function `FUN_00408400`. This function after some checks called `rdp_updateFirmware`, I knew I was closer!.


This function was being imported by the `httpd` binary from the `libcmm.so` shared object. It's primary function was calling (finally) the function doing the actual job, `rsl_sys_updateFirmware`.

## rsl_sys_updateFirmware

The decompiled code for this function is:

<html>
<script src="https://gist.github.com/nahueldsanchez/7101197b7018760d7a478c70ab62e007.js"></script>
</html>

The first thing that I did was trying to be sure that this one was the function I was looking for. Luckily at the end of it we can see the same error message that we saw in our Serial terminal when we tried to update the firmware: `Firmware version check failed` and the hex number `0xbd7` which in decimal is `3031`, the same that in the error message.

My main goal was to be able to land after line 46. That's after some checks that the code was doing to determine if it was possible to install the firmware in the device.

At this point I thought that what I was trying to do could end up bricking my router, after all, I was bypassing checks made with the purpose of validating hardware parameters. To reduce this possibility I performed a diff with Meld between the decompressed stock firmware and the US firmware that I wanted to install. I noticed changes but the main structure was the same and I decided to take the risk.

## Bypassing the update checks

To bypass the annoying checks I decided to debug the httpd binary and change its execution flow to land in the code I needed to execute. I already had gdb-server in the router so I attached it to the httpd process as follows:

```
./var/tmp # ./gdbserver-buildroot 0.0.0.0:8888 --attach <httpd_pid>
Attached; pid = 319
Listening on port 8888
```

In my local machine I used gdb-multiarch to connect to the remote gdb-server:

```
cd /path_to_local_copy_of_the_firmware/usr/bin/
gdb-multiarch httpd

(gdb) target remote 192.168.0.1:8888
Remote debugging using 192.168.0.1:8888
...
0x2bad75cc in ?? () from target:/lib/libc.so.0
```
I put a breakpoint in one of the earliest calls done by the verification checks `rsl_dev_getProductVer`, continued the execution and started the upgrade process:

```
(gdb) br rsl_dev_getProductVer

Breakpoint 1 at 0x2b9a76ac
(gdb) c
Continuing.
```

After a few second I hit the breakpoint:

```
Breakpoint 1, 0x2b9a76ac in rsl_dev_getProductVer () from target:/lib/libcmm.so
=> 0x2b9a76ac <rsl_dev_getProductVer+12>:	30 80 85 8f	lw	a1,-32720(gp)
(gdb) 
```
The following image will illustrate the purpose of this idea better than words:

<html>
<img src="/images/2021-05-14-Playing-with-a-TP-LINK-TR841_II_img_5.png" alt="assembly code for update function">
</html>

As we can see in the assembly listing, once the execution returns from `rsl_dev_getProductVer` there is a branch instruction that must be taken. Otherwise, execution continues at label `LAB_0002b0f8` and we are presented with an error message. To be able to update our firmware the program execution should continue at `LAB_0002b120`.

Back on track with our BP, I put a breakpoint in the return address (`RA` Register) once the function `rsl_dev_getProductVer` was called and landed exactly were I wanted:

```
Breakpoint 1, 0x2b9a76ac in rsl_dev_getProductVer () from target:/lib/libcmm.so
=> 0x2b9a76ac <rsl_dev_getProductVer+12>:	30 80 85 8f	lw	a1,-32720(gp)
(gdb) info r
          zero       at       v0       v1       a0       a1       a2       a3
 R0   00000000 00000001 00000000 00000300 7fbde0f0 7fbddd98 00000004 2ba3fe50 
            t0       t1       t2       t3       t4       t5       t6       t7
 R8   0000a32a 31000000 00302e34 00000000 00000000 00000000 08410014 000001e4 
            s0       s1       s2       s3       s4       s5       s6       s7
 R16  2bb3e008 003e0200 2bb3e008 00000348 00ff0000 00040100 7fbde298 7fbde33b 
            t8       t9       k0       k1       gp       sp       s8       ra
 R24  00000318 2b9a76a0 00000000 00000000 2ba70300 7fbde150 004230d4 2b9a70ec 
        status       lo       hi badvaddr    cause       pc
      0100ff13 00000284 00000000 2ba11694 50800024 2b9a76ac 
          fcsr      fir      hi1      lo1      hi2      lo2      hi3      lo3
      00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 
        dspctl  restart
      00000000 00000000 
(gdb) br *0x2b9a70ec
Breakpoint 2 at 0x2b9a70ec
(gdb) c
Continuing.

Breakpoint 2, 0x2b9a70ec in rsl_sys_updateFirmware () from target:/lib/libcmm.so
=> 0x2b9a70ec <rsl_sys_updateFirmware+264>:	20 00 bc 8f	lw	gp,32(sp)
(gdb) x/10i $pc
=> 0x2b9a70ec <rsl_sys_updateFirmware+264>:	lw	gp,32(sp)
   0x2b9a70f0 <rsl_sys_updateFirmware+268>:	beq	s3,v0,0x2b9a7120 <rsl_sys_updateFirmware+316>
   0x2b9a70f4 <rsl_sys_updateFirmware+272>:	nop
   0x2b9a70f8 <rsl_sys_updateFirmware+276>:	lw	a1,-32720(gp)
   0x2b9a70fc <rsl_sys_updateFirmware+280>:	lw	a3,-32720(gp)
   0x2b9a7100 <rsl_sys_updateFirmware+284>:	lw	t9,-32508(gp)
   0x2b9a7104 <rsl_sys_updateFirmware+288>:	li	a0,8
   0x2b9a7108 <rsl_sys_updateFirmware+292>:	addiu	a1,a1,-28560
   0x2b9a710c <rsl_sys_updateFirmware+296>:	li	a2,3031
   0x2b9a7110 <rsl_sys_updateFirmware+300>:	jalr	t9
   0x2b9a7114 <rsl_sys_updateFirmware+304>:	addiu	a3,a3,-14844
(gdb) 

```
I single stepped one instruction (`si` command), changed the $PC to address `0x2b9a7120` to continue execution (set $pc = 0x2b9a7120) and prayed to the hardware gods for a flawless update:

```
(gdb) si
0x2b9a70f0 in rsl_sys_updateFirmware () from target:/lib/libcmm.so
=> 0x2b9a70f0 <rsl_sys_updateFirmware+268>:	0b 00 62 12	beq	s3,v0,0x2b9a7120 <rsl_sys_updateFirmware+316>

(gdb) set $pc=0x2b9a7120
(gdb) c
Continuing.
[Detaching after fork from child process 2995]
```

I checked the serial output and saw several messages like this one:

```
...
piflash_ioctl_write, Write to 0x00210000 length 0x10000, ret 0, retlen 0x10000
#spiflash_ioctl_read, Read from 0x00220000 length 0x10000, ret 0, retlen 0x10000
.
...
```

I held my breath until the process finished:

<html>
<img src="/images/2021-05-14-Playing-with-a-TP-LINK-TR841_II_img_6.png" alt="latest firmware version installed">
</html>

As we can see the latest version was correctly installed!. With the method we can freely update and downgrade the firmware as needed. In future posts I'll continue playing with this router, see you!