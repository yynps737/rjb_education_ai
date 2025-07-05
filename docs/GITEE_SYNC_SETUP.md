# GitHub 到 Gitee 自动同步设置指南

本指南帮助你设置 GitHub 推送后自动同步到 Gitee。

## 步骤 1：生成 SSH 密钥对

在本地终端执行：

```bash
# 生成专门用于同步的 SSH 密钥（不要设置密码）
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gitee_sync_rsa -N ""

# 查看生成的公钥
cat ~/.ssh/gitee_sync_rsa.pub

# 查看生成的私钥（这个要保密）
cat ~/.ssh/gitee_sync_rsa
```

## 步骤 2：在 Gitee 上添加公钥

1. 登录 Gitee
2. 进入 设置 → SSH公钥
3. 添加公钥：
   - 标题：`GitHub Actions Sync`
   - 公钥：粘贴上面生成的公钥内容

## 步骤 3：在 Gitee 创建同名仓库

1. 在 Gitee 创建新仓库
2. 仓库名称：`rjb_education_ai`
3. 不要初始化仓库（不要添加 README、.gitignore 等）

## 步骤 4：在 GitHub 配置密钥

1. 进入 GitHub 仓库：https://github.com/yynps737/rjb_education_ai
2. Settings → Secrets and variables → Actions
3. 点击 "New repository secret"
4. 添加以下密钥：

### Secret 1: GITEE_PRIVATE_KEY
- Name: `GITEE_PRIVATE_KEY`
- Secret: 粘贴私钥内容（~/.ssh/gitee_sync_rsa 的内容）

### Secret 2: GITEE_USERNAME
- Name: `GITEE_USERNAME`
- Secret: 你的 Gitee 用户名

## 步骤 5：首次手动推送（可选）

如果 Gitee 仓库是空的，建议首次手动推送：

```bash
# 添加 Gitee 远程仓库
git remote add gitee git@gitee.com:your-gitee-username/rjb_education_ai.git

# 推送到 Gitee
git push gitee main

# 查看远程仓库
git remote -v
```

## 步骤 6：测试自动同步

1. 提交并推送更改到 GitHub
2. 查看 GitHub Actions：https://github.com/yynps737/rjb_education_ai/actions
3. 等待同步完成（通常只需几秒钟）
4. 检查 Gitee 仓库是否已更新

## 常见问题

### 1. 同步失败：Host key verification failed
需要在 workflow 中添加 Gitee 的 host key：

```yaml
- name: Add Gitee host key
  run: |
    mkdir -p ~/.ssh
    ssh-keyscan gitee.com >> ~/.ssh/known_hosts
```

### 2. 同步失败：Permission denied
检查：
- SSH 公钥是否正确添加到 Gitee
- 私钥是否正确配置到 GitHub Secrets
- Gitee 仓库是否存在且你有推送权限

### 3. 只想同步特定分支
修改 workflow 文件中的 branches：
```yaml
on:
  push:
    branches: [main]  # 只同步 main 分支
```

## 高级选项

### 使用 Gitee Token（备选方案）

如果 SSH 方式有问题，可以使用 Token：

1. Gitee：设置 → 私人令牌 → 生成新令牌
2. GitHub：添加 Secret `GITEE_TOKEN`
3. 修改 workflow 使用备选方案（已在文件中注释）

### 双向同步

如果需要 Gitee → GitHub 的同步，需要：
1. 在 Gitee 上配置 WebHook
2. 使用第三方服务（如 GitSync）
3. 或在 Gitee 上配置类似的 Actions

## 安全提示

- 私钥必须保密，不要提交到代码仓库
- 定期更换密钥对
- 使用专门的部署密钥，不要使用个人账户的主密钥

---

设置完成后，每次推送到 GitHub 的 main 分支，都会自动同步到 Gitee！