# 上传安全 v3：ClamAV 扫描接入说明

本版本在上传链路加入可选 ClamAV 扫描：
- 图片上传：MIME + 扩展名 + 魔数 + ClamAV
- 文件上传：扩展名白名单 + 危险魔数 + ClamAV

## 配置项

```env
UPLOAD_CLAMAV_ENABLED=False
UPLOAD_CLAMAV_HOST=127.0.0.1
UPLOAD_CLAMAV_PORT=3310
UPLOAD_CLAMAV_TIMEOUT=5
UPLOAD_CLAMAV_FAIL_CLOSED=False
```

### 策略说明

- `UPLOAD_CLAMAV_ENABLED=False`：关闭扫描（默认）
- `UPLOAD_CLAMAV_FAIL_CLOSED=False`：扫描服务异常时放行（fail-open）
- `UPLOAD_CLAMAV_FAIL_CLOSED=True`：扫描服务异常时拒绝上传（fail-closed）

生产建议：
- 安全优先：`ENABLED=True` + `FAIL_CLOSED=True`
- 可用性优先：`ENABLED=True` + `FAIL_CLOSED=False`

## clamd 快速部署（Docker）

```bash
docker run -d --name clamav -p 3310:3310 clamav/clamav:latest
```

> 首次启动会更新病毒库，耗时较长。建议观察容器日志直到服务就绪。

## 验证方法

1. 正常图片上传：应成功
2. 上传 EICAR 测试样本：应被拦截（返回“文件安全扫描未通过”）
3. 停止 clamd：
   - fail-open 模式下：允许上传，日志记录异常
   - fail-closed 模式下：拒绝上传

## 风险提示

- 扫描会增加上传延迟（通常几十到几百毫秒）
- 大文件扫描开销更高，建议结合异步扫描策略（后续可做）
