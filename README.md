# 排班订阅源（私有用途）

两个只读日历订阅源，供 iPhone / macOS / Google 日历订阅。内容由 `publish.sh` 从 `specs/` 重新生成。

| 文件 | 内容 |
|---|---|
| `dist/shift.ics` | 白班（余术 / 钱门会 / 庆门会 / 余门会 / 余门） |
| `dist/ercall.ics` | 二唤夜班（当日 17:00–24:00） |

## 更新流程

```bash
# 1. 改 specs/*.txt（格式：日期|院区|班型[|备注]）
# 2. 重新生成 + 校验 + 提交推送
./publish.sh
```

`publish.sh` 会打印结构校验结果（无 BOM / CRLF / 无 VALARM / VEVENT 配对），
任何一项 ✗ 都不会推送成功——修好再推。

## 订阅地址（部署后）

```
https://<用户名>.github.io/<仓库名>/shift.ics
https://<用户名>.github.io/<仓库名>/ercall.ics
```

> 只读、无提醒：所有提醒由 QQ 定时任务另行推送，不在 ics 里重复设置。
