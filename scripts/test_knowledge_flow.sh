#!/bin/bash
# 测试知识库完整流程：入库 → 向量化 → 搜索
set -e

BASE_URL="http://localhost:8000"
EMAIL="admin@demo.com"
PASSWORD="123456"

echo "=========================================="
echo "  知识库完整流程测试"
echo "=========================================="

# 1. 登录获取 token
echo ""
echo "[1/4] 登录获取 JWT Token..."
LOGIN_RESP=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "  ✗ 登录失败: $LOGIN_RESP"
  exit 1
fi
echo "  ✓ 登录成功，Token: ${TOKEN:0:20}..."

# 2. 入库 - 创建知识条目
echo ""
echo "[2/4] 入库 - 创建知识条目..."

# 测试数据：3条不同类别的知识
ITEMS=(
  '{"title":"水飞蓟护肝片功效","content":"水飞蓟提取物含有水飞蓟宾，具有抗氧化和保护肝细胞的作用，常用于辅助改善肝功能。建议每日服用2次，每次1粒。","category":"health","tags":["护肝","水飞蓟","保健品"]}'
  '{"title":"小红书爆款笔记写作技巧","content":"写小红书笔记要注意：1. 标题要吸引眼球，多用数字和疑问句；2. 封面图要精美清晰；3. 正文分段落，善用emoji；4. 结尾引导互动，如点赞收藏。","category":"marketing","tags":["小红书","写作","运营"]}'
  '{"title":"维生素D补充指南","content":"维生素D有助于钙的吸收，建议成人每日摄入400-800IU。可以通过晒太阳、食用富含维D的食物或补充剂来获取。缺乏维D可能导致骨质疏松。","category":"health","tags":["维生素D","补钙","健康"]}'
)

ITEM_IDS=()
for i in "${!ITEMS[@]}"; do
  DATA="${ITEMS[$i]}"
  TITLE=$(echo "$DATA" | python -c "import sys,json; print(json.load(sys.stdin)['title'])")
  RESP=$(curl -s -X POST "$BASE_URL/api/v1/tenant/knowledge/items" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$DATA")
  ID=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
  SYNC=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin)['sync_status'])" 2>/dev/null)
  if [ -n "$ID" ]; then
    echo "  ✓ 条目[$((i+1))] 入库成功: id=$ID, sync_status=$SYNC, title=$TITLE"
    ITEM_IDS+=("$ID")
  else
    echo "  ✗ 条目[$((i+1))] 入库失败: $RESP"
  fi
done

# 3. 等待向量化完成
echo ""
echo "[3/4] 等待向量化完成..."
MAX_WAIT=60
WAITED=0
ALL_SYNCED=false

while [ $WAITED -lt $MAX_WAIT ]; do
  sleep 3
  WAITED=$((WAITED + 3))

  # 检查所有条目的 sync_status
  ALL_SYNCED=true
  for ID in "${ITEM_IDS[@]}"; do
    LIST_RESP=$(curl -s -X GET "$BASE_URL/api/v1/tenant/knowledge/items?page=1&page_size=100" \
      -H "Authorization: Bearer $TOKEN")
    STATUS=$(echo "$LIST_RESP" | python -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('items', []):
    if str(item.get('id')) == '$ID':
        print(item.get('sync_status', 'unknown'))
        break
" 2>/dev/null)

    if [ "$STATUS" != "synced" ]; then
      ALL_SYNCED=false
      break
    fi
  done

  if $ALL_SYNCED; then
    echo "  ✓ 所有条目向量化完成 (等待了 ${WAITED}s)"
    break
  fi

  echo "  ... 等待中 (${WAITED}s)，部分条目尚未完成向量化"
done

if ! $ALL_SYNCED; then
  echo "  ✗ 超时：${MAX_WAIT}s 后仍有条目未完成向量化"
  echo "  继续测试搜索（可能降级为 ILIKE）..."
fi

# 4. 语义搜索
echo ""
echo "[4/4] 语义搜索测试..."
echo ""

# 测试用例1：搜索"护肝"
echo "  --- 测试1: 查询「护肝」 ---"
SEARCH_RESP=$(curl -s -X POST "$BASE_URL/api/v1/tenant/knowledge/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "护肝", "limit": 5}')
echo "$SEARCH_RESP" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'  结果数: {data.get(\"total\", 0)}')
for e in data.get('entries', []):
    print(f'  → [{e.get(\"score\", 0):.3f}] {e.get(\"title\", \"\")} | category={e.get(\"category\", \"\")}')
" 2>/dev/null

echo ""

# 测试用例2：搜索"小红书写作"
echo "  --- 测试2: 查询「小红书写作」 ---"
SEARCH_RESP=$(curl -s -X POST "$BASE_URL/api/v1/tenant/knowledge/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "小红书写作", "limit": 5}')
echo "$SEARCH_RESP" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'  结果数: {data.get(\"total\", 0)}')
for e in data.get('entries', []):
    print(f'  → [{e.get(\"score\", 0):.3f}] {e.get(\"title\", \"\")} | category={e.get(\"category\", \"\")}')
" 2>/dev/null

echo ""

# 测试用例3：按分类搜索
echo "  --- 测试3: 查询「维生素」+ category=health ---"
SEARCH_RESP=$(curl -s -X POST "$BASE_URL/api/v1/tenant/knowledge/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "维生素", "category": "health", "limit": 5}')
echo "$SEARCH_RESP" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'  结果数: {data.get(\"total\", 0)}')
for e in data.get('entries', []):
    print(f'  → [{e.get(\"score\", 0):.3f}] {e.get(\"title\", \"\")} | category={e.get(\"category\", \"\")}')
" 2>/dev/null

echo ""

# 清理测试数据
echo "=========================================="
echo "  清理测试数据..."
for ID in "${ITEM_IDS[@]}"; do
  curl -s -X DELETE "$BASE_URL/api/v1/tenant/knowledge/items/$ID" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
done
echo "  ✓ 已删除 ${#ITEM_IDS[@]} 条测试数据"

echo ""
echo "=========================================="
echo "  测试完成！"
echo "=========================================="
