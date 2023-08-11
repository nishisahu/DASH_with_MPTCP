# DASH_with_MPTCP
MPTCP is an extension of TCP that allows the applications to  use multiple interfaces over the same TCP connection, enabling them to utilize the aggregated bandwidth and provide resilience to network failure. These characteristics of MPTCP make it well-suited for streaming traffic. Dynamic Adaptive Streaming over HTTP (DASH), a streaming protocol dominating the Internet, ensures Quality of Experience (QoE) to content consumers by adapting the playback bitrate to match the available throughput.


 When DASH is used with MPTCP as transport protocol, the aggregated throughput and increased reliability due to the use of multiple interfaces for a streaming session improves QoE.There have been several studies to analyze the performance of DASH on MPTCP under the presence of shared bottleneck link, and varying network resources like MPTCP buffer sizes and path latencies. However, the real Internet scenario consists of several types of traffic with varying loads competing for resources.

Problem Statement:-

To perform experimental evaluation of Multipath TCP for MPEG-DASH traffic under varying traffic loads and BBR as congestion control for background traffic.

Objectives:-

To gain an in-depth understanding of the working of Multipath TCP and its components.

To gain an in-depth understanding of the working of MPEG-DASH (Dynamic Adaptive Streaming over HTTP).

To emulate Multipath TCP using Linux network namespaces and utilities.

To check the compliance of Linux Upstream implementation of MPTCP with RFC 8684.

To implement different scenarios with varying loads and test the performance of DASH on MPTCP.

To gain an in-depth understanding of the behavior of BBR congestion control in background traffic.

