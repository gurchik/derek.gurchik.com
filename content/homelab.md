---
template: "page.html.j2"
title: "My homelab"
---

| Host          | Model                          | CPU                           | Memory | Disk                                             |
|---------------|--------------------------------|-------------------------------|--------|--------------------------------------------------|
| snickers.lan  | Lenovo Thinkcentre Tiny M75q-1 | AMD Ryzen 3 Pro 3200GE 3.3GHz | 64 GB  | 250 GB NVME SSD (root fs), 250 GB SSD (Longhorn) |
| twix.lan      | Lenovo Thinkcentre Tiny M720q  | Intel Core i5-8400T 1.7 GHz   | 64 GB  | 250 GB NVME SSD (root fs), 250 GB SSD (Longhorn) |
| almondjoy.lan | Lenovo Thinkcentre Tiny M720q  | Intel Core i5-8400T 1.7 GHz   | 64 GB  | 250 GB NVME SSD (root fs), 250 GB SSD (Longhorn) |

The machines are running [k3s](https://k3s.io/) version 1.25 in [High Availability (Embedded etcd) mode](https://docs.k3s.io/datastore/ha-embedded). They are provisioned using Ansible and Helm. They are currently running:

* [Longhorn](https://longhorn.io/) for replicated block storage. Volumes are snapshotted regularly and uploaded to S3.
* [k8s_gateway](https://github.com/ori-edge/k8s_gateway) for resolving DNS for Kubernetes Services and Ingresses within my home network
* [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/) for dashboards and alerts
* Some Discord bots for some private servers
