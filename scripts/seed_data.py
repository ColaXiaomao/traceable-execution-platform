"""
Seed data script - 批量创建测试数据
运行方式: python scripts/seed_data.py
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

# ════════════════════════════════════════════════════════
#  ✏️  在这里修改所有配置
# ════════════════════════════════════════════════════════

# 管理员账户
ADMIN = {"username": "admin1", "password": "admin12345"}

# 已有的 employee 账户
EXISTING_EMPLOYEES = [
    {"username": "employee1", "password": "employee12345"},
]

# 需要新建的 employee 账户（想加就往这里加）
NEW_EMPLOYEES = [
    {"username": "employee2", "password": "employee12345", "full_name": "Employee Two",   "email": "employee2@example.com"},
    {"username": "employee3", "password": "employee12345", "full_name": "Employee Three", "email": "employee3@example.com"},
    {"username": "employee4", "password": "employee12345", "full_name": "Employee Four",  "email": "employee4@example.com"},
]

# Admin 创建的资产（想加就往这里加）
ASSETS = [
    {"name": "Web服务器-01",    "asset_type": "服务器",  "location": "机房A"},
    {"name": "Web服务器-02",    "asset_type": "服务器",  "location": "机房A"},
    {"name": "数据库服务器-01", "asset_type": "服务器",  "location": "机房B"},
    {"name": "数据库服务器-02", "asset_type": "服务器",  "location": "机房B"},
    {"name": "应用服务器-01",   "asset_type": "服务器",  "location": "机房C"},
    {"name": "应用服务器-02",   "asset_type": "服务器",  "location": "机房C"},
    {"name": "核心交换机-01",   "asset_type": "交换机",  "location": "机房A"},
    {"name": "接入交换机-01",   "asset_type": "交换机",  "location": "机房B"},
    {"name": "接入交换机-02",   "asset_type": "交换机",  "location": "机房C"},
    {"name": "边界路由器-01",   "asset_type": "路由器",  "location": "机房A"},
]

# 每个用户创建多少工单（username 对应上面的账户）
TICKET_COUNTS = {
    "admin1":     20,
    "employee1":  30,
    "employee2":  10,
    "employee3":  15,
    "employee4":  20,
}

# Admin 审批多少工单（从每个用户的工单里各取几个）
APPROVE_COUNTS = {
    "admin1":     3,
    "employee1":  6,
    "employee2":  5,
    "employee3":  5,
    "employee4":  4,
}

# 工单标题模板
TICKET_TITLES = [
    "系统升级申请", "硬件维修申请", "网络故障处理", "安全补丁安装",
    "配置变更申请", "性能优化请求", "存储扩容申请", "备份恢复操作",
    "防火墙规则更新", "用户权限变更", "设备更换申请", "例行巡检",
    "故障排查", "紧急维护申请", "软件安装申请", "日志审查",
    "容量规划评估", "灾备演练申请", "监控配置更新", "安全审计"
]

# ════════════════════════════════════════════════════════
#  以下不需要修改
# ════════════════════════════════════════════════════════

def get_token(username, password):
    res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    res.raise_for_status()
    print(f"  ✅ 登录成功: {username}")
    return res.json()["access_token"]

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def register_user(token, user):
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "username": user["username"],
        "password": user["password"],
        "full_name": user.get("full_name", user["username"]),
        "email": user.get("email", f"{user['username']}@example.com"),
        "is_admin": False
    }, headers=auth(token))
    if res.status_code == 200:
        print(f"  ✅ 创建用户: {user['username']}")
    else:
        print(f"  ⚠️  用户已存在或失败: {user['username']} ({res.status_code})")

def create_asset(token, asset, i):
    res = requests.post(f"{BASE_URL}/assets", json={
        "name": asset["name"],
        "asset_type": asset["asset_type"],
        "serial_number": f"SN-{i:04d}",
        "location": asset.get("location", "未知"),
        "description": f"{asset['asset_type']}设备 #{i}"
    }, headers=auth(token))
    res.raise_for_status()
    result = res.json()
    print(f"  ✅ 创建资产: {asset['name']} (ID: {result['id']})")
    return result

def create_ticket(token, title, asset_id, username):
    res = requests.post(f"{BASE_URL}/tickets", json={
        "title": f"[{username}] {title}",
        "description": f"工单描述：{title}",
        "asset_id": asset_id
    }, headers=auth(token))
    res.raise_for_status()
    result = res.json()
    print(f"  ✅ 创建工单: {result['title']} (ID: {result['id']})")
    return result

def approve_ticket(token, ticket_id):
    res = requests.post(f"{BASE_URL}/tickets/{ticket_id}/approve", headers=auth(token))
    if res.status_code == 200:
        print(f"  ✅ 审批工单 ID: {ticket_id}")
    else:
        print(f"  ⚠️  审批失败 ID: {ticket_id} ({res.status_code})")

def main():
    print("\n🚀 开始创建种子数据...\n")

    # 登录 admin
    print("─── Step 1: 登录 Admin ───")
    admin_token = get_token(ADMIN["username"], ADMIN["password"])

    # 创建新用户
    print("\n─── Step 2: 创建新用户 ───")
    for emp in NEW_EMPLOYEES:
        register_user(admin_token, emp)

    # 登录所有用户
    print("\n─── Step 3: 登录所有用户 ───")
    tokens = {ADMIN["username"]: admin_token}
    for emp in EXISTING_EMPLOYEES:
        tokens[emp["username"]] = get_token(emp["username"], emp["password"])
    for emp in NEW_EMPLOYEES:
        tokens[emp["username"]] = get_token(emp["username"], emp["password"])

    # 创建资产
    print("\n─── Step 4: Admin 创建资产 ───")
    assets = []
    for i, asset in enumerate(ASSETS, 1):
        assets.append(create_asset(admin_token, asset, i))
    asset_ids = [a["id"] for a in assets]

    # 每个用户创建工单
    all_tickets = {}
    for username, count in TICKET_COUNTS.items():
        print(f"\n─── 创建工单: {username} ({count}个) ───")
        token = tokens[username]
        tickets = []
        for i in range(count):
            title = TICKET_TITLES[i % len(TICKET_TITLES)]
            asset_id = asset_ids[i % len(asset_ids)]
            tickets.append(create_ticket(token, title, asset_id, username))
        all_tickets[username] = tickets

    # Admin 审批工单
    print("\n─── Step 最终: Admin 审批工单 ───")
    total_approved = 0
    for username, count in APPROVE_COUNTS.items():
        tickets = all_tickets.get(username, [])
        for ticket in tickets[:count]:
            approve_ticket(admin_token, ticket["id"])
            total_approved += 1

    print(f"\n✅ 种子数据创建完成！")
    print(f"   资产: {len(assets)} 条")
    print(f"   工单: {sum(TICKET_COUNTS.values())} 条")
    print(f"   已审批: {total_approved} 条")

if __name__ == "__main__":
    main()