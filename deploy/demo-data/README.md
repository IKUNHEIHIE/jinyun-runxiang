# 批量演示数据（2026-10-21）

`sys_config.demo_bulk_seed_20261021` 记录了一次性生成的一批演示数据，用于让小课堂与社区在演示时具备分页后的真实体量。

## 内容

| 表 | 行数 | 说明 |
| --- | --- | --- |
| `course` | 200 | 8 个非遗门类轮换，学段 PRIMARY_LOW / PRIMARY_HIGH，封面取自 `backend/static/design/*.webp` |
| `course_chapter` | 800 | 每门 4 章，视频沿用 MDN flower 与 W3C Sintel 两条 CC0 示例 |
| `community_post` | 200 | 全部 `APPROVED`，作者从现有学生账号中随机取，点赞/浏览为演示值 |
| `community_post_detail` | 200 | `gallery_json` 为封面（部分含第二张），其余字段为空数组 |
| `community_comment` | 299 | 每帖 1–2 条，`comment_count` 与之一致 |

生成后线上总量：课程 206、章节 806、作品 222（过审 217）、评论 326。

## 两种导入方式

### 1. 直接导入 SQL（推荐，行内容与线上一致）

```bash
gunzip -c deploy/demo-data/demo_courses.sql.gz > /tmp/demo.sql
gunzip -c deploy/demo-data/demo_chapters.sql.gz >> /tmp/demo.sql
gunzip -c deploy/demo-data/demo_posts.sql.gz >> /tmp/demo.sql
gunzip -c deploy/demo-data/demo_post_details.sql.gz >> /tmp/demo.sql
gunzip -c deploy/demo-data/demo_comments.sql.gz >> /tmp/demo.sql
mysql -u <user> -p <database> < /tmp/demo.sql
```

SQL 使用显式主键，导入前请确认目标库没有同 id 的行；导入后建议补写 `sys_config.demo_bulk_seed_20261021`（见脚本 `--rollback` 依赖它记录 id）。

### 2. 用脚本重新生成（内容等价，随机种子固定）

```bash
cd backend            # DATABASE_URL 指向目标库
python ../scripts/seed_demo_bulk.py            # dry-run，只打印计划
python ../scripts/seed_demo_bulk.py --apply    # 写入并登记 marker
python ../scripts/seed_demo_bulk.py --rollback # 按 marker 里的 id 精确删除
```

脚本使用 `random.Random(20261021)`，同一份封面目录下生成结果稳定；封面目录可用 `DEMO_DESIGN_DIR` 覆盖。

## 封面

`backend/static/design/` 同时保留原始 PNG 与转换后的 WebP。WebP 由 ffmpeg 生成（最长边 800、quality 80），数据库引用指向 `.webp`；如重新生成封面，可按同样参数转换后更新 `cover_url`。

## 说明

- 这批数据仅用于演示与联调，点赞/浏览等互动数值为随机值，不代表真实用户行为。
- 课程标题按「门类·主题+入门/精讲/工坊」组合生成，可能与正式内容规划不一致。
- 社区作品的评论数与评论行严格一致；点赞数与评论点赞为演示值。
