# 🐳 Cloud Docker Build Setup

## Option 1: GitHub Actions (Easiest)

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Add Lambda layer build configuration"
git push origin main
```

### Step 2: Set up AWS Credentials
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add these secrets:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### Step 3: Run the Build
1. Go to Actions tab in your GitHub repo
2. Click "Build Lambda Layer"
3. Click "Run workflow"
4. Wait for completion (usually 10-15 minutes)

### Step 4: Download the Layer
1. After build completes, go to Actions → Build Lambda Layer
2. Click on the completed run
3. Download the "lambda-layer-complete" artifact
4. Upload to AWS Lambda Console

## Option 2: AWS CodeBuild

### Step 1: Create CodeBuild Project
1. Go to AWS CodeBuild Console
2. Create new build project
3. Source: Connect to your GitHub repo
4. Environment: Use managed image with Docker
5. Buildspec: Use the `buildspec.yml` file

### Step 2: Run Build
1. Start the build project
2. Monitor progress in AWS Console
3. Layer will be automatically uploaded to S3

## Option 3: GitHub Codespaces

### Step 1: Open in Codespaces
1. Go to your GitHub repo
2. Click the green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on main"

### Step 2: Build in Cloud
```bash
# In the codespace terminal
chmod +x build_docker_complete.sh
./build_docker_complete.sh
```

## 🎯 Recommended: GitHub Actions

GitHub Actions is the best option because:
- ✅ Free for public repos
- ✅ No setup required
- ✅ Automatic S3 upload
- ✅ Reliable cloud environment
- ✅ Easy to monitor

## 📊 Expected Results

After successful build:
- Layer size: ~70-80MB
- Location: `s3://crawlchat-deployment/lambda-layer-complete.zip`
- Status: Ready for AWS Lambda deployment
- GLIBC compatibility: ✅ Fixed 