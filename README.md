## DSM7 Custom DDNS

This is a docker image for DSM 7.x to using custom DDNS provider
such as CloudFlare, etc.

## Description

Using this project to create a custom DDNS on DSM 7.x in minutes!

## Usage

```shell
DOMAIN="example.com"  # Replace the `example.com` to your own domain.

docker run -d -p 8000:80 --name ddns -e CF_ZONE="${DOMAIN}" chowrex/dsm7-ddns:latest
```

When you're done, you can use `http://IP:8000/update?record=__HOSTNAME__&value=__MYIP__&password=__PASSWORD__`
as your DSM DDNS provider's query URL.

For more details, read:

> ENG: [DDNS | DSM - Synology Knowledge Center](https://kb.synology.com/en-us/DSM/help/DSM/AdminCenter/connection_ddns?version=7)

> CHS: [DDNS | DSM - Synology 知识中心](https://kb.synology.cn/zh-cn/DSM/help/DSM/AdminCenter/connection_ddns?version=7)
