### Task 1 MininetTopo

```shell
sudo python mininetTopo.py # expect to see exact number of devices are launched.
```

![image-20211117213502945](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213502945.png)

### Task 2 PingAll

```shell
pingall # expect to see all hosts ping each other successfully
```

![image-20211117213532399](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213532399.png)

### Task 3 Fault Tolerance

```shell
pingall # same
h1 ping h4 # connected
link s1 s2 down # drop the link
h1 ping h4 # there could be a timeout before reconnection
link s1 s2 up
```

![image-20211117213732413](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213732413.png)

![image-20211117213618353](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213618353.png)

### Task 4 Firewall

h4 on port 4001

```shell
h4 iperf -s -p 4001 & # start a iperf server on port 4001
h5 iperf -c h4 -p 4001 # no response
h1 iperf -c h4 -p 4001 # no response
```

![image-20211117212511829](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117212511829.png)

```shell
h4 iperf -s -p 8080 & # start a iperf server on port 8080
h5 iperf -c h4 -p 8080 # local 10.0.0.5 port XXX connected with 10.0.0.4 port 8080
```

![image-20211117212613458](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117212613458.png)

h2 to h5 on port 1000

```shell
h5 iperf -s -p 1000 & # start a iperf server on port 1000
h2 iperf -c h5 -p 1000 # no response
h1 iperf -c h5 -p 1000 # local 10.0.0.1 port XXX connected with 10.0.0.5 port 1000
h7 iperf -c h5 -p 1000 # local 10.0.0.7 port XXX connected with 10.0.0.5 port 1000
```

![image-20211117212851585](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117212851585.png)

```shell
h5 iperf -s -p 8080 & # start a iperf server on port 8080
h2 iperf -c h5 -p 8080 # local 10.0.0.2 port XXX connected with 10.0.0.5 port 8080
```

![image-20211117213134930](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213134930.png)

### Task 5 Premium Traffic

premium to premium

```shell
iperf h1 h3 # Results: ~10Mbits
```

![image-20211117213322046](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213322046.png)

normal to premium

```shell
iperf h1 h2 # Results: ~5Mbits or ~10Mbits
iperf h2 h1 # Results: ~5Mbits or ~10Mbits
```

![image-20211117213345926](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213345926.png)

normal to normal 

```shell
iperf h2 h5 # Results: ~5Mbits
```

![image-20211117213402588](https://cdn.jsdelivr.net/gh/irissky/00-pic/2021summer-images/image-20211117213402588.png)




