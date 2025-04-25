#!/bin/bash

# 默认值
DEFAULT_IMAGE_NAME="apscheduler-app"
DEFAULT_VERSION="latest"
DEFAULT_REGISTRY=""
DEFAULT_PLATFORMS="linux/amd64,linux/arm64"

# 帮助信息
show_help() {
    echo "Usage: ./build.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  -n, --name     Image name (default: $DEFAULT_IMAGE_NAME)"
    echo "  -v, --version  Image version (default: $DEFAULT_VERSION)"
    echo "  -r, --registry Docker registry (default: none)"
    echo "  -p, --platform Target platforms (default: $DEFAULT_PLATFORMS)"
    echo "  -h, --help     Show this help message"
    echo
    echo "Example:"
    echo "  ./build.sh -n myapp -v 1.0.0"
    echo "  ./build.sh -r registry.example.com -n myapp -v 1.0.0"
}

# 参数解析
IMAGE_NAME=$DEFAULT_IMAGE_NAME
VERSION=$DEFAULT_VERSION
REGISTRY=$DEFAULT_REGISTRY
PLATFORMS=$DEFAULT_PLATFORMS

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORMS="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# 构建完整镜像名称
FULL_IMAGE_NAME="$IMAGE_NAME:$VERSION"
if [ ! -z "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$FULL_IMAGE_NAME"
fi

echo "Building multi-platform Docker image: $FULL_IMAGE_NAME"
echo "Platforms: $PLATFORMS"

# 确保buildx已启用
docker buildx create --use --name multiarch-builder || true

# 构建多平台镜像
docker buildx build \
    --platform $PLATFORMS \
    -t $FULL_IMAGE_NAME \
    --push \
    .

# 检查构建是否成功
if [ $? -eq 0 ]; then
    echo "Successfully built and pushed multi-platform image: $FULL_IMAGE_NAME"
else
    echo "Failed to build multi-platform image: $FULL_IMAGE_NAME"
    exit 1
fi 